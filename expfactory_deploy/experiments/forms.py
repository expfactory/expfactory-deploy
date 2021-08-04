from django import forms
from django.forms import formset_factory
from django.forms import BaseFormSet
from django.forms import ModelForm

from crispy_forms.helper import FormHelper

from experiments import models as models

class BatteryForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False

    class Meta:
        model = models.Battery
        fields = ["name", "consent", "insturctions", "advertisement"]


class ExperimentInstanceForm(ModelForm):
    class Meta:
        model = models.ExperimentInstance
        fields = ["note", "commit", "experiment_repo_id"]

class ExperimentInstanceOrderForm(ExperimentInstanceForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
    order = forms.IntegerField()

ExpInstanceFormset = formset_factory(
    form=ExperimentInstanceOrderForm, can_order=True, can_delete=True,
)

# class BaseBatteryExperimentFormSet(BaseFormSet):
