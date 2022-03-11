from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms import (
    BaseFormSet,
    ModelForm,
    inlineformset_factory,
    modelformset_factory,
)
import git
import pathlib
from giturlparse import parse
from experiments import models as models

class ExperimentUploadForm(forms.Form):
    url = forms.URLField()

    def clean(self):
        cleaned_data = super().clean()
        url = cleaned_data["url"]
        gitparse_url = parse(url)
        if not gitparse_url.valid:
            self.add_error("url", "gitparseurl library could not validate repo url.")
        url = gitparse_url.urls.get('https', url)
        self.cleaned_data.update({'url', url})

        path = pathlib.Path(settings.REPO_DIR, gitparse_url)
        path.mkdir(parents=True, exists_ok=True)
        try:
            models.RepoOrigin.get(origin=url)
            self.add_error("url", f"repository with this origin already exists")
        except models.RepoOrigin.DoexNotExist:
            db_repo_origin = models.RepoOrigin(origin=url, path=path)
            try:
                repo = git.Repo.clone_from(url, path)
                db_repo_origin.save()
            except git.exc.GitError as e:
                self.add_error("url", e)

        return cleaned_data

class BatteryForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False

    class Meta:
        model = models.Battery
        fields = ["title", "consent", "instructions", "advertisement"]
        widgets = {
            "title": forms.TextInput(),
            "consent": forms.Textarea(attrs={"cols": 80, "rows": 2}),
            "instructions": forms.Textarea(attrs={"cols": 80, "rows": 2}),
            "advertisement": forms.Textarea(attrs={"cols": 80, "rows": 2}),
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
    exp_order = forms.IntegerField()
    battery_id = None

    def __init__(self, *args, **kwargs):
        ordering = kwargs.pop("ordering", None)
        self.battery_id = kwargs.pop("battery_id", None)
        super().__init__(*args, **kwargs)
        if ordering and self.instance.id:
            self.fields["exp_order"].initial = ordering.get(
                id=self.instance.id
            ).exp_order
        self.fields["commit"].initial = "latest"
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("exp_order", css_class="exp-order-input"),
            Field("note", css_class="exp-note-input"),
            Field("commit", css_class="exp-commit-input"),
            Field("experiment_repo_id", css_class="exp-repo-input"),
        )

    def clean(self):
        cleaned_data = super().clean()
        commit = cleaned_data["commit"]
        exp_instance = cleaned_data["experiment_repo_id"]
        if commit == "latest":
            commit = exp_instance.get_latest_commit()

        # should we return gitpython error message here?
        if not exp_instance.origin.is_valid_commit(commit):
            raise forms.ValidationError(
                f"Commit '{commit}' is invalid for {exp_instance.origin}"
            )

        cleaned_data["commit"] = commit
        return cleaned_data

    def save(self, *args, **kwargs):
        exp_instance = super().save(*args, **kwargs)
        exp_repo_id = exp_instance.experiment_repo_id_id
        battery = models.Battery.objects.get(id=self.battery_id)
        try:
            batt_exp = models.BatteryExperiments.objects.get(
                battery=battery, experiment_instance__experiment_repo_id=exp_repo_id
            )
            batt_exp.order = self.cleaned_data.get("exp_order", -1)
        except ObjectDoesNotExist:
            batt_exp = models.BatteryExperiments(
                battery=battery,
                experiment_instance=exp_instance,
                order=self.cleaned_data.get("exp_order", -1),
            )
        batt_exp.save()
        return exp_instance


ExpInstanceFormset = modelformset_factory(
    models.ExperimentInstance,
    form=ExperimentInstanceOrderForm,
    can_delete=True,
    extra=0,
)


