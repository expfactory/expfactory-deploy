from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Field, Layout, Submit, Div

class MturkHit(forms.Form):
    title = forms.CharField()
    description = forms.CharField()
    reward = forms.CharField()
    assignmentDurationInSeconds = forms.CharField()
    lifetimeinseconds = forms.CharField()
    keywords = forms.CharField()
    sandbox = forms.BooleanField()
    number_of_assignments = forms.IntegerField(min_value=1)
    # MaxAssignments

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.add_input(Submit('submit', 'Submit'))
