
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Field, Layout, Submit, Div
from django.forms import ModelForm
from django.forms import modelformset_factory

from prolific import models

class SimpleCCForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Submit'))

    class Meta:
        model  = models.SimpleCC
        fields = ["completion_url"]

class StudyCollectionForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Submit'))

    class Meta:
        model  = models.StudyCollection
        fields = ["name", "default_project"]

class StudyForm(ModelForm):
    class Meta:
        model  = models.Study
        fields = ["battery"]

class StudyRankForm(ModelForm):
    class Meta:
        model  = models.StudyRank
        fields = ["study", "rank"]

StudyRankFormset = modelformset_factory(
    models.StudyRank,
    form=StudyRankForm,
    can_delete=True,
    extra=0,
)
