from django import forms
from django.forms import ModelForm
from experiments import models as models

class BatteryForm(ModelForm):
    def __init__(self, *args, **kwargs):
        # we could pass user/request to limit experiments retrieved
        super(BatteryForm, self).__init__(*args, **kwargs)
        '''
        experiment_choices = [(x.id, x.name) for x in models.ExperimentRepo.objects.all()]
        self.fields['experiments'] = forms.MultipleChoiceField(
            initial=[],
            widget=forms.CheckboxSelectMultiple,
            choices=experiment_choices
        )
        '''

    class Meta:
        model = models.Battery
        fields = [
            "name", "consent", "insturctions", "advertisement"
        ]


class ExperimentInstanceForm(ModelForm):
    class Meta:
        model = models.ExperimentInstance
        fields = ["note", "commit", "experiment_repo_id"]
