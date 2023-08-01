from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Field, Layout, Submit, Div
from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms import (
    BaseFormSet,
    ModelForm,
    inlineformset_factory,
    modelformset_factory,
)
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from taggit.forms import TagField
from taggit.models import Tag
import git
import pathlib
from giturlparse import parse
from tinymce.widgets import TinyMCE

from experiments import models as models

class ConsentForm(forms.Form):
    agree = forms.BooleanField(required=False)
    disagree = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Submit'))

    def clean(self):
        cleaned_data = super().clean()

        if (bool(cleaned_data['accept']) and bool(cleaned_data['disagree'])):
            raise forms.ValidationError('Only One of two fields may be checked')
        if (not bool(cleaned_data['accept']) and not bool(cleaned_data['disagree'])):
            raise forms.ValidationError('One of the two fields must be checked')

        return cleaned_data

class RepoOriginForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cancel_url = reverse('experiments:repo-origin-list')
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Submit'))
        self.helper.add_input(
            Button(
                'cancel',
                'Cancel',
                css_class='btn-primary',
                onclick=f'window.location.href = "{cancel_url}"'
            )
        )

    class Meta:
        model  = models.RepoOrigin
        fields = ["url"]
        widgets = {
            "url": forms.TextInput(),
        }

    # Todo: extract user/org name and use them in path and name
    # could also imagine adding index for collisions.
    def clean(self):
        cleaned_data = super().clean()
        url = cleaned_data["url"]
        gitparse_url = parse(url)
        if not gitparse_url.valid:
            self.add_error("url", "gitparseurl library could not validate repo url.")
        else:
            name = gitparse_url.name
            path = pathlib.Path(settings.REPO_DIR, name)
            path.mkdir(parents=True, exist_ok=True)
            self.instance.path = path
            self.instance.name = name
            try:
                models.RepoOrigin.objects.get(name=name, path=path)
            except ObjectDoesNotExist:
                pass
            else:
                self.add_error('Repository with this name currently exists')
        return cleaned_data

'''
    Here we make a widget and field to make partial use of form validation
    for the checkboxes that are manually rendered in subject-list.
    Exposing instance and relation data in a nice table takes more work
    with custom widget templates. In lieu of that we manually render the
    inputs in the template, and keep our feel bad hacks small.
'''
class NoRenderWidget(forms.SelectMultiple):
    def render(*args, **kwargs):
        return ""

'''
    TypedMultipleChoiceField understands the arrays that html post
    data sends in, but it expects 'valid_values' to be pre specified
    a la choices tupoles. We bypass this check with the valid_value override.
    Validate is still called, which attempts to coerce the values.
'''
class IdList(forms.TypedMultipleChoiceField):
    def __init__(self, *args, **kwargs):
        self.coerce = int
        super().__init__(*args, **kwargs)

    def valid_value(self, value):
        return True

class BatteryMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        url = reverse_lazy('experiments:battery-detail', args=[obj.pk])
        return format_html('<a href="{}"> {} (id:{}) </a> - {}', url, obj.title, obj.pk, obj.status)

class SubjectActionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.add_input(Submit('deactivate', 'Deactivate Selected Subjects', formaction='/subjects/toggle'))
        self.helper.add_input(Submit('assign', 'Assign Batteries', formaction='/subjects/assign'))
        self.helper.form_tag = False

    batteries = BatteryMultipleChoiceField(
        queryset=models.Battery.objects.exclude(status='inactive').exclude(status='template'),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    subjects = IdList(
        widget=NoRenderWidget,
        required=False,
        label=False
    )


class SubjectCount(forms.Form):
    count = forms.IntegerField(required=True, label="Number of subjects to create")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.add_input(Submit('submit', 'Submit'))


class ExperimentRepoForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = True
        self.helper.add_input(Submit('submit', 'Update'))

    class Meta:
        model = models.ExperimentRepo
        fields = ["name", "tags"]
        widgets = {
            "name": forms.TextInput()
        }

class ExperimentRepoBulkTagForm(forms.Form):
    # tags = TagField()
    choices = [ (x.name, x.name) for x in Tag.objects.all() ]
    choices = [('', ''), *choices]

    tags = forms.MultipleChoiceField(choices=choices)
    experiments = IdList(
        widget=NoRenderWidget,
        required=False,
        label=False
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.add_input(
            Submit(
                'add_tags',
                'Add to Selected Experiments',
                formaction=reverse_lazy("experiments:experiment-repo-bulk-tag-add")
            )
        )
        self.helper.add_input(
            Submit(
                'remove_tags',
                'Remove From Selected Experiments',
                formaction=reverse_lazy("experiments:experiment-repo-bulk-tag-remove")
            )
        )
        self.helper.add_input(
            Button(
                'search-by-tag',
                'Search By Tags',
                css_class="btn btn-primary",
            )
        )
        self.helper.form_id = 'experiment-repo-bulk-tag'
        self.helper.form_method = 'POST'


class BatteryForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False

    class Meta:
        model = models.Battery
        fields = ["title", "consent", "instructions", "advertisement", "status", "random_order"]
        widgets = {
            "title": forms.TextInput(),
            "consent": TinyMCE(attrs={'cols': 80, 'rows': 12}),
            "instructions": TinyMCE(attrs={'cols': 80, 'rows': 12}),
            "advertisement": TinyMCE(attrs={'cols': 80, 'rows': 12}),
            "status": forms.HiddenInput(),
        }


class ExperimentInstanceForm(ModelForm):
    class Meta:
        model = models.ExperimentInstance
        fields = ["note", "commit", "experiment_repo_id"]
        widgets = {
            "commit": forms.TextInput(),
            "note": forms.Textarea(attrs={"cols": 40, "rows": 1}),
        }

    def save(self, commit=True):
        exp_instance, _ = models.ExperimentInstance.objects.update_or_create(
            commit=self.instance.commit,
            experiment_repo_id=self.instance.experiment_repo_id,
            defaults={'note': self.instance.note}
        )
        return exp_instance

class ExperimentInstanceOrderForm(ExperimentInstanceForm):
    template_name = "experiments/experiment_instance_order_form.html"
    exp_order = forms.IntegerField()
    use_latest = forms.BooleanField(initial=True)
    exp_instance_select = forms.ModelChoiceField(queryset=models.ExperimentRepo.objects.none(), required=False)
    battery_id = None

    def __init__(self, repo_id=-1, *args, **kwargs):
        ordering = kwargs.pop("ordering", None)
        self.battery_id = kwargs.pop("battery_id", None)
        super().__init__(*args, **kwargs)
        if ordering and self.instance.id:
            order_inst = ordering.get(id=self.instance.id)
            self.fields["exp_order"].initial = order_inst.exp_order
            self.fields["exp_instance_select"].initial = self.instance
            repo_id = self.instance.experiment_repo_id.id
        if not self.instance.id:
            self.fields["commit"].initial = "latest"
            self.fields["use_latest"].initial = True
        self.fields["exp_order"].widget = forms.HiddenInput()
        self.fields["experiment_repo_id"].widget = forms.HiddenInput()
        self.fields["experiment_repo_id"].initial = repo_id
        if repo_id > -1:
            try:
                repo = models.ExperimentRepo.objects.get(id=repo_id)
                self.fields["exp_instance_select"].queryset = repo.experimentinstance_set
                if repo.experimentinstance_set.count == 0:
                    self.fields["commit"].initial = "latest"
                    self.fields["use_latest"].initial = True
                self.name = repo.name
                hx_url = reverse('experiments:instance-order-form', args=[repo_id ])
                self.fields["exp_instance_select"].widget.attrs['hx-get'] = hx_url
                self.fields["exp_instance_select"].widget.attrs['hx-target'] = 'closest .list-group-item'
                self.fields["exp_instance_select"].widget.attrs['hx-swap'] = 'outerHTML'

            except ObjectDoesNotExist:
                pass
        self.set_classes()


    def clean(self):
        cleaned_data = super().clean()
        commit = cleaned_data["commit"]
        exp_instance = cleaned_data["experiment_repo_id"]
        if commit == "latest":
            commit = exp_instance.get_latest_commit()

        # should we return gitpython error message here?
        if not exp_instance.origin.is_valid_commit(commit):
            raise forms.ValidationError(
                f"Commit '{commit}' is invalid for {exp_instance.url}"
            )

        cleaned_data["commit"] = commit
        return cleaned_data

    def save(self, *args, **kwargs):
        exp_instance = super().save(*args, **kwargs)
        exp_repo_id = exp_instance.experiment_repo_id_id
        battery = models.Battery.objects.get(id=self.battery_id)
        try:
            batt_exp = battery.batteryexperiments_set.get(experiment_instance__experiment_repo_id=exp_repo_id)
            batt_exp.order = self.cleaned_data.get("exp_order", -1)
            batt_exp.save()
        except ObjectDoesNotExist:
            batt_exp = models.BatteryExperiments(
                battery=battery,
                experiment_instance=exp_instance,
                order=self.cleaned_data.get("exp_order", -1),
            )
            batt_exp.save()
        return exp_instance

    def set_classes(self):
        class_pattern = "instance_{}"
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': class_pattern.format(field)})



ExpInstanceFormset = modelformset_factory(
    models.ExperimentInstance,
    form=ExperimentInstanceOrderForm,
    can_delete=True,
    extra=0,
)

class BatteryExperimentsForm(ModelForm):
    class Meta:
        model = models.BatteryExperiments
        fields = ["order", "use_latest", "experiment_instance"]

BatteryExperimentsFormset = modelformset_factory(
    models.BatteryExperiments,
    form=BatteryExperimentsForm,
    can_delete=True,
    extra=0,
)
