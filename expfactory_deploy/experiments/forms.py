from crispy_forms.helper import FormHelper
from django import forms
from django.forms import BaseFormSet, ModelForm, modelformset_factory
from experiments import models as models


class BatteryForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False

    class Meta:
        model = models.Battery
        fields = ["name", "consent", "instructions", "advertisement"]
        widgets = {
            "name": forms.TextInput(),
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
            "note": forms.Textarea(attrs={"cols": 80, "rows": 2}),
        }


class ExperimentInstanceOrderForm(ExperimentInstanceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commit"].initial = "latest"
        self.helper = FormHelper(self)
        self.helper.form_tag = False

    def clean(self):
        commit = self.cleaned_data["commit"]
        exp_instance = self.cleaned_data["experiment_repo_id"]
        if commit == "latest":
            commit = exp_instance.get_latest_commit()

        # should we return gitpython error message here?
        if not exp_instance.origin.is_valid_commit(commit):
            raise forms.ValidationError(
                f"Commit '{commit}' is invalid for {exp_instance.origin}"
            )

        self.cleaned_data["commit"] = commit
        return self.cleaned_data


ExpInstanceFormset = modelformset_factory(
    models.ExperimentInstance,
    form=ExperimentInstanceOrderForm,
    can_order=True,
    can_delete=True,
    extra=0,
)

# class BaseBatteryExperimentFormSet(BaseFormSet):
