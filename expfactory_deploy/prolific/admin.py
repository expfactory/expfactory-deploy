from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea, NumberInput
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from django.contrib import messages
from django.http import HttpResponseRedirect
from prolific.models import (
    StudyCollection, Study, StudyRank, StudySubject, 
    StudyCollectionSubject, SimpleCC, ProlificAPIResult, BlockedParticipant
)


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


class DeploymentFilter(SimpleListFilter):
    """Filter for study collection deployment status"""
    title = 'deployment status'
    parameter_name = 'deployed'
    
    def lookups(self, request, model_admin):
        return (
            ('1', 'Deployed'),
            ('0', 'Not deployed'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(study__remote_id__gt='')
        if self.value() == '0':
            return queryset.exclude(study__remote_id__gt='')


class StudyInline(admin.TabularInline):
    model = Study
    extra = 0
    ordering = ('rank',)
    readonly_fields = ('remote_id', 'participant_group', 'completion_code')
    fields = ('battery', 'rank', 'remote_id', 'participant_group', 'completion_code')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('battery')


class StudyCollectionSubjectInline(admin.TabularInline):
    model = StudyCollectionSubject
    extra = 0
    readonly_fields = ('subject', 'status', 'group_index', 'current_study', 'active')
    fields = ('subject', 'status', 'group_index', 'current_study', 'active')


@admin.register(StudyCollection)
class StudyCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'study_count_display', 'total_available_places', 
                   'reward_display', 'published', 'deployed_status', 'active')
    list_filter = ('published', 'active', DeploymentFilter, 'project')
    search_fields = ('name', 'title', 'project', 'description')
    readonly_fields = ('study_count_display', 'deployed_status', 'parent_link', 'children_count')
    actions = ['create_drafts_action', 'set_allowlists_action', 'clear_remote_ids_action',
              'activate_collections', 'deactivate_collections']
    inlines = [StudyInline, StudyCollectionSubjectInline]
    
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 60})},
        models.IntegerField: {'widget': NumberInput(attrs={'style': 'width: 100px'})},
    }
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'title', 'description', 'project', 'workspace_id')
        }),
        ('Study Configuration', {
            'fields': ('total_available_places', 'estimated_completion_time', 'reward',
                      'number_of_groups', 'inter_study_delay')
        }),
        ('Status', {
            'fields': ('published', 'active', 'study_count_display', 'deployed_status')
        }),
        ('Screening', {
            'fields': ('screener_for', 'screener_rejection_message'),
            'classes': ('collapse',)
        }),
        ('Timing Controls', {
            'fields': (
                'time_to_start_first_study', 'failure_to_start_grace_interval',
                'study_time_to_warning', 'study_grace_interval', 'study_kick_on_timeout',
                'collection_time_to_warning', 'collection_grace_interval', 'collection_kick_on_timeout'
            ),
            'classes': ('collapse',)
        }),
        ('Messages', {
            'fields': (
                'failure_to_start_message', 'failure_to_start_warning_message',
                'study_warning_message', 'collection_warning_message'
            ),
            'classes': ('collapse',)
        }),
        ('Relationships', {
            'fields': ('parent_link', 'children_count'),
            'classes': ('collapse',)
        })
    )
    
    def study_count_display(self, obj):
        return obj.study_count
    study_count_display.short_description = 'Studies'
    
    def reward_display(self, obj):
        return f"${obj.reward / 100:.2f}" if obj.reward else "$0.00"
    reward_display.short_description = 'Reward'
    
    def deployed_status(self, obj):
        return '✓ Deployed' if obj.deployed else '✗ Not deployed'
    deployed_status.short_description = 'Deployment Status'
    
    def parent_link(self, obj):
        if obj.parent:
            url = reverse('admin:prolific_studycollection_change', args=[obj.parent.pk])
            return format_html('<a href="{}">{}</a>', url, obj.parent.name)
        return 'Root collection'
    parent_link.short_description = 'Parent'
    
    def children_count(self, obj):
        return obj.children.count()
    children_count.short_description = 'Child Collections'
    
    def create_drafts_action(self, request, queryset):
        """Create Prolific study drafts for selected collections"""
        results = []
        for collection in queryset:
            try:
                responses = collection.create_drafts()
                results.append(f"{collection.name}: {len(responses)} studies created/updated")
            except Exception as e:
                self.message_user(request, f"Error creating drafts for {collection.name}: {str(e)}", level=messages.ERROR)
        
        if results:
            self.message_user(request, "; ".join(results))
    create_drafts_action.short_description = "Create Prolific study drafts"
    
    def set_allowlists_action(self, request, queryset):
        """Set participant allowlists for selected collections"""
        updated = 0
        for collection in queryset:
            try:
                collection.set_allowlists()
                updated += 1
            except Exception as e:
                self.message_user(request, f"Error setting allowlists for {collection.name}: {str(e)}", level=messages.ERROR)
        
        if updated:
            self.message_user(request, f"Updated allowlists for {updated} collections")
    set_allowlists_action.short_description = "Set participant allowlists"
    
    def clear_remote_ids_action(self, request, queryset):
        """Clear remote study IDs for selected collections"""
        for collection in queryset:
            collection.clear_remote_ids()
        self.message_user(request, f"Cleared remote IDs for {queryset.count()} collections")
    clear_remote_ids_action.short_description = "Clear remote study IDs"
    
    def activate_collections(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f"Activated {updated} collections")
    activate_collections.short_description = "Activate selected collections"
    
    def deactivate_collections(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f"Deactivated {updated} collections")
    deactivate_collections.short_description = "Deactivate selected collections"


class StudySubjectInline(admin.TabularInline):
    model = StudySubject
    extra = 0
    readonly_fields = ('subject', 'assignment', 'status', 'assigned_to_study', 'prolific_session_id')
    fields = ('subject', 'assignment', 'status', 'status_reason', 'assigned_to_study', 'prolific_session_id')


@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ('battery_title', 'study_collection', 'rank', 'remote_id_short', 
                   'participant_group_short', 'completion_code', 'subject_count')
    list_filter = ('study_collection', 'battery__status')
    search_fields = ('battery__title', 'study_collection__name', 'remote_id', 'completion_code')
    readonly_fields = ('remote_id', 'participant_group', 'completion_code', 'prolific_url', 'part_group_name')
    actions = ['create_drafts_action', 'set_group_names', 'sync_with_prolific']
    inlines = [StudySubjectInline]
    
    fieldsets = (
        ('Study Configuration', {
            'fields': ('battery', 'study_collection', 'rank')
        }),
        ('Prolific Integration', {
            'fields': ('remote_id', 'participant_group', 'completion_code', 'prolific_url')
        }),
        ('System Information', {
            'fields': ('part_group_name',),
            'classes': ('collapse',)
        })
    )
    
    def battery_title(self, obj):
        return obj.battery.title if obj.battery else 'No battery'
    battery_title.short_description = 'Battery'
    
    def remote_id_short(self, obj):
        return obj.remote_id[:8] + '...' if len(obj.remote_id) > 8 else obj.remote_id
    remote_id_short.short_description = 'Prolific ID'
    
    def participant_group_short(self, obj):
        return obj.participant_group[:8] + '...' if len(obj.participant_group) > 8 else obj.participant_group
    participant_group_short.short_description = 'Part. Group'
    
    def subject_count(self, obj):
        return obj.studysubject_set.count()
    subject_count.short_description = 'Subjects'
    
    def prolific_url(self, obj):
        if obj.remote_id:
            url = f"https://app.prolific.co/researcher/workspaces/studies/{obj.remote_id}"
            return format_html('<a href="{}" target="_blank">View on Prolific</a>', url)
        return 'Not deployed'
    prolific_url.short_description = 'Prolific Link'
    
    def create_drafts_action(self, request, queryset):
        """Create study drafts on Prolific"""
        updated = 0
        for study in queryset:
            try:
                next_study = study.study_collection.next_study(study.id)
                next_group = next_study.participant_group if next_study else None
                response = study.create_draft(next_group)
                if not hasattr(response, 'status_code'):
                    updated += 1
                else:
                    self.message_user(request, f"Error creating draft for {study}: {response}", level=messages.ERROR)
            except Exception as e:
                self.message_user(request, f"Error creating draft for {study}: {str(e)}", level=messages.ERROR)
        
        if updated:
            self.message_user(request, f"Created/updated {updated} study drafts")
    create_drafts_action.short_description = "Create study drafts on Prolific"
    
    def set_group_names(self, request, queryset):
        """Update participant group names on Prolific"""
        updated = 0
        for study in queryset:
            try:
                study.set_group_name()
                updated += 1
            except Exception as e:
                self.message_user(request, f"Error setting group name for {study}: {str(e)}", level=messages.ERROR)
        
        self.message_user(request, f"Updated group names for {updated} studies")
    set_group_names.short_description = "Update participant group names"


@admin.register(StudyRank)
class StudyRankAdmin(admin.ModelAdmin):
    list_display = ('study', 'rank')
    list_filter = ('study__study_collection',)
    search_fields = ('study__battery__title',)


@admin.register(StudySubject)
class StudySubjectAdmin(admin.ModelAdmin):
    list_display = ('subject', 'study_battery', 'status', 'status_reason', 'assigned_to_study', 
                   'prolific_session_id', 'assignment_status')
    list_filter = ('status', 'status_reason', StatusFilter, 'assigned_to_study')
    search_fields = ('subject__prolific_id', 'subject__handle', 'study__battery__title', 
                    'prolific_session_id')
    readonly_fields = ('assigned_to_study', 'failed_at', 'warned_at', 'added_to_study', 
                      'prolific_status', 'study_collection_subject_link')
    actions = ['sync_prolific_status', 'remove_from_studies', 'reset_status']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('study', 'subject', 'assignment')
        }),
        ('Status Tracking', {
            'fields': ('status', 'status_reason', 'assigned_to_study', 'failed_at', 'warned_at')
        }),
        ('Prolific Integration', {
            'fields': ('prolific_session_id', 'added_to_study', 'prolific_status')
        }),
        ('Relationships', {
            'fields': ('study_collection_subject_link',),
            'classes': ('collapse',)
        })
    )
    
    def study_battery(self, obj):
        return obj.study.battery.title if obj.study and obj.study.battery else 'N/A'
    study_battery.short_description = 'Battery'
    
    def assignment_status(self, obj):
        return obj.assignment.status if obj.assignment else 'No assignment'
    assignment_status.short_description = 'Assignment Status'
    
    def prolific_status(self, obj):
        try:
            return obj.get_prolific_status()
        except:
            return 'Error retrieving status'
    prolific_status.short_description = 'Prolific Status'
    
    def study_collection_subject_link(self, obj):
        try:
            scs = obj.study_collection_subject
            if scs:
                url = reverse('admin:prolific_studycollectionsubject_change', args=[scs.pk])
                return format_html('<a href="{}">View Collection Subject</a>', url)
        except:
            pass
        return 'N/A'
    study_collection_subject_link.short_description = 'Collection Subject'
    
    def sync_prolific_status(self, request, queryset):
        """Sync status with Prolific for selected subjects"""
        updated = 0
        for study_subject in queryset:
            try:
                status = study_subject.get_prolific_status()
                if status:
                    updated += 1
            except Exception as e:
                self.message_user(request, f"Error syncing status for {study_subject}: {str(e)}", level=messages.ERROR)
        
        self.message_user(request, f"Synced status for {updated} study subjects")
    sync_prolific_status.short_description = "Sync status with Prolific"
    
    def remove_from_studies(self, request, queryset):
        """Remove participants from Prolific studies"""
        removed = 0
        for study_subject in queryset:
            try:
                if study_subject.subject and study_subject.subject.prolific_id:
                    study_subject.study.remove_participant(study_subject.subject.prolific_id)
                    removed += 1
            except Exception as e:
                self.message_user(request, f"Error removing {study_subject}: {str(e)}", level=messages.ERROR)
        
        self.message_user(request, f"Removed {removed} participants from studies")
    remove_from_studies.short_description = "Remove from Prolific studies"


@admin.register(StudyCollectionSubject)
class StudyCollectionSubjectAdmin(admin.ModelAdmin):
    list_display = ('subject', 'study_collection', 'status', 'group_index', 'current_study', 
                   'active', 'progress_summary')
    list_filter = ('status', 'active', 'study_collection', StatusFilter, 'group_index')
    search_fields = ('subject__prolific_id', 'subject__handle', 'study_collection__name')
    readonly_fields = ('failed_at', 'warned_at', 'ttfs_warned_at', 'ttcc_warned_at', 
                      'ttcc_flagged_at', 'ended_status', 'study_progress')
    actions = ['create_incomplete_collections', 'activate_subjects', 'deactivate_subjects',
              'reset_to_not_started']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('study_collection', 'subject', 'group_index', 'current_study', 'active')
        }),
        ('Status Tracking', {
            'fields': ('status', 'status_reason', 'failed_at', 'warned_at', 'ended_status')
        }),
        ('Timer Warnings', {
            'fields': ('ttfs_warned_at', 'ttcc_warned_at', 'ttcc_flagged_at'),
            'classes': ('collapse',)
        }),
        ('Progress Summary', {
            'fields': ('study_progress',),
            'classes': ('collapse',)
        })
    )
    
    def progress_summary(self, obj):
        try:
            statuses = obj.study_statuses()
            completed = len(statuses.get('completed', []))
            total = sum(len(studies) for studies in statuses.values())
            return f"{completed}/{total} completed"
        except:
            return 'Error calculating progress'
    progress_summary.short_description = 'Progress'
    
    def ended_status(self, obj):
        return '✓ Ended' if obj.ended else '✗ Active'
    ended_status.short_description = 'Ended'
    
    def study_progress(self, obj):
        try:
            statuses = obj.study_statuses()
            progress_html = "<ul>"
            for status, studies in statuses.items():
                progress_html += f"<li><strong>{status}:</strong> {len(studies)} studies</li>"
            progress_html += "</ul>"
            return mark_safe(progress_html)
        except:
            return 'Error retrieving progress'
    study_progress.short_description = 'Detailed Progress'
    
    def create_incomplete_collections(self, request, queryset):
        """Create new study collections for incomplete subjects"""
        created = 0
        for scs in queryset:
            try:
                if not scs.ended:
                    api_responses, new_scs = scs.incomplete_study_collection()
                    created += 1
            except Exception as e:
                self.message_user(request, f"Error creating incomplete collection for {scs}: {str(e)}", level=messages.ERROR)
        
        self.message_user(request, f"Created {created} incomplete study collections")
    create_incomplete_collections.short_description = "Create incomplete study collections"
    
    def activate_subjects(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f"Activated {updated} collection subjects")
    activate_subjects.short_description = "Activate selected subjects"
    
    def deactivate_subjects(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f"Deactivated {updated} collection subjects")
    deactivate_subjects.short_description = "Deactivate selected subjects"


@admin.register(SimpleCC)
class SimpleCCAdmin(admin.ModelAdmin):
    list_display = ('battery', 'completion_url_short', 'created', 'modified')
    list_filter = ('created', 'modified')
    search_fields = ('battery__title', 'completion_url')
    readonly_fields = ('created', 'modified')
    
    def completion_url_short(self, obj):
        if obj.completion_url:
            url = obj.completion_url[:50] + '...' if len(obj.completion_url) > 50 else obj.completion_url
            return format_html('<a href="{}" target="_blank">{}</a>', obj.completion_url, url)
        return 'No URL'
    completion_url_short.short_description = 'Completion URL'


@admin.register(ProlificAPIResult)
class ProlificAPIResultAdmin(admin.ModelAdmin):
    list_display = ('created', 'collection', 'request_short', 'response_status', 'response_preview')
    list_filter = ('created', 'collection')
    search_fields = ('request', 'collection__name')
    readonly_fields = ('created', 'request_formatted', 'response_formatted')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('created', 'collection')
        }),
        ('API Call Details', {
            'fields': ('request_formatted', 'response_formatted')
        })
    )
    
    def request_short(self, obj):
        return obj.request[:100] + '...' if len(obj.request) > 100 else obj.request
    request_short.short_description = 'Request'
    
    def response_status(self, obj):
        if isinstance(obj.response, dict):
            return obj.response.get('status', 'Unknown')
        return 'N/A'
    response_status.short_description = 'Status'
    
    def response_preview(self, obj):
        if isinstance(obj.response, dict):
            preview = str(obj.response)[:100] + '...' if len(str(obj.response)) > 100 else str(obj.response)
            return preview
        return str(obj.response)[:100] + '...' if len(str(obj.response)) > 100 else str(obj.response)
    response_preview.short_description = 'Response Preview'
    
    def request_formatted(self, obj):
        return format_html('<pre>{}</pre>', obj.request)
    request_formatted.short_description = 'Request Details'
    
    def response_formatted(self, obj):
        import json
        try:
            if isinstance(obj.response, dict):
                formatted = json.dumps(obj.response, indent=2)
            else:
                formatted = str(obj.response)
            return format_html('<pre>{}</pre>', formatted)
        except:
            return format_html('<pre>{}</pre>', str(obj.response))
    response_formatted.short_description = 'Response Details'


@admin.register(BlockedParticipant)
class BlockedParticipantAdmin(admin.ModelAdmin):
    list_display = ('prolific_id', 'active', 'note_short', 'created', 'modified')
    list_filter = ('active', 'created', 'modified')
    search_fields = ('prolific_id', 'note')
    readonly_fields = ('created', 'modified')
    actions = ['activate_participants', 'deactivate_participants']
    
    def note_short(self, obj):
        return obj.note[:50] + '...' if len(obj.note) > 50 else obj.note
    note_short.short_description = 'Note'
    
    def activate_participants(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f"Activated {updated} blocked participants")
    activate_participants.short_description = "Activate selected participants"
    
    def deactivate_participants(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f"Deactivated {updated} blocked participants")
    deactivate_participants.short_description = "Deactivate selected participants"


# Keep existing django-q customizations
from django_q import models as q_models
from django_q import admin as q_admin

admin.site.unregister([q_models.Schedule])
@admin.register(q_models.Schedule)
class ModedScheduleAdmin(q_admin.ScheduleAdmin):
    list_display = (
        "id",
        "name",
        "func",
        "args",
        "schedule_type",
        "repeats",
        "cluster",
        "next_run",
        "get_last_run",
        "get_success",
    )

admin.site.unregister([q_models.Success])
@admin.register(q_models.Success)
class ModedSuccessAdmin(q_admin.TaskAdmin):
    list_display = (
        "name",
        "group",
        "func",
        "args",
        "cluster",
        "started",
        "stopped",
        "time_taken",
    )
