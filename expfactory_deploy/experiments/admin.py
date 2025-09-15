from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from experiments.models import (
    Framework, FrameworkResource, RepoOrigin, ExperimentRepo,
    ExperimentInstance, Battery, BatteryExperiments, Subject,
    Result, Assignment, ExperimentOrder, ExperimentOrderItem
)


class ActiveFilter(SimpleListFilter):
    """Filter for active/inactive items"""
    title = 'active status'
    parameter_name = 'active'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Active'),
            ('0', 'Inactive'),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(active=True)
        if self.value() == '0':
            return queryset.filter(active=False)


class StatusFilter(SimpleListFilter):
    """Filter for status fields"""
    title = 'status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        if hasattr(model_admin.model, 'STATUS'):
            return model_admin.model.STATUS
        return ()

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())


@admin.register(Framework)
class FrameworkAdmin(admin.ModelAdmin):
    list_display = ('name', 'experiment_count')
    search_fields = ('name',)

    def experiment_count(self, obj):
        return obj.experimentrepo_set.count()
    experiment_count.short_description = 'Experiments'


@admin.register(FrameworkResource)
class FrameworkResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'path')
    search_fields = ('name', 'path')


class ExperimentRepoInline(admin.TabularInline):
    model = ExperimentRepo
    extra = 0
    readonly_fields = ('name', 'framework', 'active', 'experiment_count')
    fields = ('name', 'framework', 'active', 'experiment_count')

    def experiment_count(self, obj):
        return obj.experimentinstance_set.count()
    experiment_count.short_description = 'Instances'


@admin.register(RepoOrigin)
class RepoOriginAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_url_link', 'active', 'experiment_count', 'latest_commit_short')
    list_filter = (ActiveFilter,)
    search_fields = ('name', 'url', 'path')
    readonly_fields = ('latest_commit', 'latest_commit_date')
    actions = ['sync_repositories', 'activate_repos', 'deactivate_repos']
    inlines = [ExperimentRepoInline]

    formfield_overrides = {
        models.TextField: {'widget': TextInput(attrs={'size': '80'})},
    }

    def display_url_link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.display_url, obj.display_url)
    display_url_link.short_description = 'Repository URL'

    def experiment_count(self, obj):
        return obj.experimentrepo_set.count()
    experiment_count.short_description = 'Experiments'

    def latest_commit_short(self, obj):
        try:
            commit = obj.get_latest_commit()
            return commit[:8] if commit else 'N/A'
        except:
            return 'Error'
    latest_commit_short.short_description = 'Latest Commit'

    def latest_commit(self, obj):
        try:
            return obj.get_latest_commit()
        except:
            return 'Error retrieving commit'

    def latest_commit_date(self, obj):
        try:
            return obj.commit_date()
        except:
            return 'Error retrieving date'

    def sync_repositories(self, request, queryset):
        updated = 0
        for repo in queryset:
            try:
                repo.pull_origin()
                updated += 1
            except Exception as e:
                self.message_user(request, f"Error syncing {repo.name}: {str(e)}", level='ERROR')
        self.message_user(request, f"Successfully synced {updated} repositories.")
    sync_repositories.short_description = "Sync selected repositories"

    def activate_repos(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f"Activated {updated} repositories.")
    activate_repos.short_description = "Activate selected repositories"

    def deactivate_repos(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f"Deactivated {updated} repositories.")
    deactivate_repos.short_description = "Deactivate selected repositories"


class ExperimentInstanceInline(admin.TabularInline):
    model = ExperimentInstance
    extra = 0
    readonly_fields = ('commit', 'commit_date', 'remote_url_link')
    fields = ('note', 'commit', 'commit_date', 'remote_url_link')

    def remote_url_link(self, obj):
        if obj.remote_url:
            return format_html('<a href="{}" target="_blank">View</a>', obj.remote_url)
        return 'N/A'
    remote_url_link.short_description = 'Remote'


@admin.register(ExperimentRepo)
class ExperimentRepoAdmin(admin.ModelAdmin):
    list_display = ('name', 'framework', 'origin', 'active', 'instance_count', 'tags_display')
    list_filter = ('framework', 'active', ActiveFilter)
    search_fields = ('name', 'cogat_id', 'tags__name')
    readonly_fields = ('url_link', 'latest_commit')
    inlines = [ExperimentInstanceInline]

    formfield_overrides = {
        models.TextField: {'widget': TextInput(attrs={'size': '60'})},
    }

    def url_link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.url, obj.url)
    url_link.short_description = 'Repository URL'

    def instance_count(self, obj):
        return obj.experimentinstance_set.count()
    instance_count.short_description = 'Instances'

    def tags_display(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()[:3]])
    tags_display.short_description = 'Tags'

    def latest_commit(self, obj):
        try:
            return obj.get_latest_commit()
        except:
            return 'Error retrieving commit'


@admin.register(ExperimentInstance)
class ExperimentInstanceAdmin(admin.ModelAdmin):
    list_display = ('experiment_repo_id', 'commit_short', 'commit_date', 'note_short', 'is_valid')
    list_filter = ('commit_date', 'experiment_repo_id__framework')
    search_fields = ('experiment_repo_id__name', 'commit', 'note')
    readonly_fields = ('remote_url_link', 'deploy_path')

    formfield_overrides = {
        models.TextField: {'widget': TextInput(attrs={'size': '60'})},
    }

    def commit_short(self, obj):
        return obj.commit[:8] if obj.commit else 'N/A'
    commit_short.short_description = 'Commit'

    def note_short(self, obj):
        return obj.note[:50] + '...' if len(obj.note) > 50 else obj.note
    note_short.short_description = 'Note'

    def is_valid(self, obj):
        try:
            return '✓' if obj.is_valid_commit() else '✗'
        except:
            return '?'
    is_valid.short_description = 'Valid'

    def remote_url_link(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>', obj.remote_url, obj.remote_url)
    remote_url_link.short_description = 'Remote URL'

    def deploy_path(self, obj):
        try:
            return obj.deploy_static()
        except:
            return 'Error getting deploy path'


class BatteryExperimentsInline(admin.TabularInline):
    model = BatteryExperiments
    extra = 0
    ordering = ('order',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('experiment_instance__experiment_repo_id')


class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 0
    readonly_fields = ('subject', 'status', 'consent_accepted', 'result_summary')
    fields = ('subject', 'status', 'consent_accepted', 'note', 'result_summary')

    def result_summary(self, obj):
        if obj.pk:
            status = obj.result_status
            return f"Results: {status['completed']}/{status['total']} completed"
        return 'No results'
    result_summary.short_description = 'Results'


@admin.register(Battery)
class BatteryAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'user', 'experiment_count', 'assignment_count', 'created', 'public')
    list_filter = ('status', 'public', 'random_order', 'created', 'user')
    search_fields = ('title', 'user__username', 'user__email')
    readonly_fields = ('created', 'modified', 'template_link', 'children_count')
    # actions = ['clone_batteries', 'publish_batteries', 'make_inactive']
    inlines = [BatteryExperimentsInline, AssignmentInline]

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 60})},
    }

    fieldsets = (
        (None, {
            'fields': ('title', 'status', 'user', 'group')
        }),
        ('Content', {
            'fields': ('consent', 'instructions', 'advertisement'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('random_order', 'public', 'inter_task_break')
        }),
        ('Relationships', {
            'fields': ('template_link', 'children_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created', 'modified'),
            'classes': ('collapse',)
        })
    )

    def experiment_count(self, obj):
        return obj.experiment_instances.count()
    experiment_count.short_description = 'Experiments'

    def assignment_count(self, obj):
        return obj.assignment_set.count()
    assignment_count.short_description = 'Assignments'

    def template_link(self, obj):
        if obj.template_id:
            url = reverse('admin:experiments_battery_change', args=[obj.template_id.pk])
            return format_html('<a href="{}">{}</a>', url, obj.template_id.title)
        return 'Original template'
    template_link.short_description = 'Template'

    def children_count(self, obj):
        return obj.children.count()
    children_count.short_description = 'Clones'

    def clone_batteries(self, request, queryset):
        cloned = 0
        for battery in queryset:
            try:
                battery.duplicate()
                cloned += 1
            except Exception as e:
                self.message_user(request, f"Error cloning {battery.title}: {str(e)}", level='ERROR')
        self.message_user(request, f"Successfully cloned {cloned} batteries.")
    clone_batteries.short_description = "Clone selected batteries"

    def publish_batteries(self, request, queryset):
        updated = queryset.filter(status='draft').update(status='published')
        self.message_user(request, f"Published {updated} batteries.")
    publish_batteries.short_description = "Publish selected draft batteries"

    def make_inactive(self, request, queryset):
        updated = queryset.update(status='inactive')
        self.message_user(request, f"Made {updated} batteries inactive.")
    make_inactive.short_description = "Make selected batteries inactive"


@admin.register(BatteryExperiments)
class BatteryExperimentsAdmin(admin.ModelAdmin):
    list_display = ('battery', 'experiment_name', 'order', 'use_latest')
    list_filter = ('use_latest', 'battery__status')
    search_fields = ('battery__title', 'experiment_instance__experiment_repo_id__name')
    ordering = ('battery', 'order')

    def experiment_name(self, obj):
        return obj.experiment_instance.experiment_repo_id.name
    experiment_name.short_description = 'Experiment'


class ResultInline(admin.TabularInline):
    model = Result
    extra = 0
    readonly_fields = ('status', 'include', 'created', 'data_preview')
    fields = ('battery_experiment', 'status', 'include', 'created', 'data_preview')

    def data_preview(self, obj):
        if obj.data:
            preview = obj.data[:100] + '...' if len(obj.data) > 100 else obj.data
            return preview
        return 'No data'
    data_preview.short_description = 'Data Preview'


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'email', 'active', 'assignment_count', 'result_count', 'prolific_id')
    list_filter = ('active', 'prolific_id')
    search_fields = ('handle', 'email', 'prolific_id', 'uuid', 'tags__name')
    readonly_fields = ('uuid', 'last_url_at')
    actions = ['activate_subjects', 'deactivate_subjects']
    inlines = [ResultInline]

    def assignment_count(self, obj):
        return obj.assignment_set.count()
    assignment_count.short_description = 'Assignments'

    def result_count(self, obj):
        return obj.result_set.count()
    result_count.short_description = 'Results'

    def activate_subjects(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f"Activated {updated} subjects.")
    activate_subjects.short_description = "Activate selected subjects"

    def deactivate_subjects(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f"Deactivated {updated} subjects.")
    deactivate_subjects.short_description = "Deactivate selected subjects"


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('subject', 'experiment_name', 'status', 'include', 'created', 'data_length')
    list_filter = ('status', 'include', 'created', StatusFilter)
    search_fields = ('subject__handle', 'subject__prolific_id', 'assignment__battery__title')
    readonly_fields = ('created', 'modified', 'started_at', 'completed_at', 'failed_at', 'data_formatted')
    actions = ['set_include_status', 'export_results']

    fieldsets = (
        (None, {
            'fields': ('assignment', 'battery_experiment', 'subject', 'status', 'include')
        }),
        ('Data', {
            'fields': ('data_formatted',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created', 'modified', 'started_at', 'completed_at', 'failed_at'),
            'classes': ('collapse',)
        })
    )

    def experiment_name(self, obj):
        if obj.battery_experiment:
            return obj.battery_experiment.experiment_instance.experiment_repo_id.name
        return 'N/A'
    experiment_name.short_description = 'Experiment'

    def data_length(self, obj):
        return len(obj.data) if obj.data else 0
    data_length.short_description = 'Data Size'

    def data_formatted(self, obj):
        if obj.data:
            return format_html('<pre>{}</pre>', obj.data[:1000] + '...' if len(obj.data) > 1000 else obj.data)
        return 'No data'
    data_formatted.short_description = 'Data'

    def set_include_status(self, request, queryset):
        updated = 0
        for result in queryset:
            try:
                result.set_include()
                updated += 1
            except Exception as e:
                self.message_user(request, f"Error setting include for result {result.id}: {str(e)}", level='ERROR')
        self.message_user(request, f"Updated include status for {updated} results.")
    set_include_status.short_description = "Update include status for selected results"


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('subject', 'battery', 'status', 'consent_accepted', 'result_summary', 'created_date')
    list_filter = ('status', 'consent_accepted', 'battery__status', StatusFilter)
    search_fields = ('subject__handle', 'subject__prolific_id', 'battery__title', 'alt_id')
    readonly_fields = ('started_at', 'completed_at', 'failed_at', 'result_summary', 'pass_check_result')
    actions = ['check_completion', 'reset_assignments']

    def result_summary(self, obj):
        if obj.pk:
            status = obj.result_status
            return f"{status['completed']}/{status['total']} completed, {status['failed']} failed"
        return 'No results'
    result_summary.short_description = 'Results Summary'

    def created_date(self, obj):
        return obj.started_at.date() if obj.started_at else 'Not started'
    created_date.short_description = 'Started Date'

    def pass_check_result(self, obj):
        try:
            return '✓ Pass' if obj.pass_check() else '✗ Fail'
        except:
            return '? Error'
    pass_check_result.short_description = 'QA Check'

    def check_completion(self, request, queryset):
        for assignment in queryset:
            assignment.get_next_experiment()
        self.message_user(request, f"Checked completion status for {queryset.count()} assignments.")
    check_completion.short_description = "Check completion status"

    def reset_assignments(self, request, queryset):
        updated = queryset.update(status='not-started')
        self.message_user(request, f"Reset {updated} assignments to not-started.")
    reset_assignments.short_description = "Reset selected assignments"


class ExperimentOrderItemInline(admin.TabularInline):
    model = ExperimentOrderItem
    extra = 0
    ordering = ('order',)


@admin.register(ExperimentOrder)
class ExperimentOrderAdmin(admin.ModelAdmin):
    list_display = ('name_or_auto', 'battery', 'auto_generated', 'item_count')
    list_filter = ('auto_generated',)
    search_fields = ('name', 'battery__title')
    inlines = [ExperimentOrderItemInline]

    def name_or_auto(self, obj):
        return obj.name if obj.name else f"Auto-generated for {obj.battery.title}"
    name_or_auto.short_description = 'Name'

    def item_count(self, obj):
        return obj.experimentorderitem_set.count()
    item_count.short_description = 'Items'


@admin.register(ExperimentOrderItem)
class ExperimentOrderItemAdmin(admin.ModelAdmin):
    list_display = ('experiment_order', 'experiment_name', 'order')
    search_fields = ('experiment_order__name', 'battery_experiment__experiment_instance__experiment_repo_id__name')
    ordering = ('experiment_order', 'order')

    def experiment_name(self, obj):
        return obj.battery_experiment.experiment_instance.experiment_repo_id.name
    experiment_name.short_description = 'Experiment'
