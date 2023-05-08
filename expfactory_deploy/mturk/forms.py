from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Field, Layout, Submit, Div

from mturk.models import MturkCredentials, HitGroup, HitGroupDetails, HitGroupHits


class HitGroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = None
        self.helper.layout = Layout(
            Field("credentials"),
            Field("sandbox"),
            Field("note"),
            Field("number_of_assignments"),
        )
        self.helper.render_hidden_fields = True

    class Meta:
        model = HitGroup
        fields = ["battery", "credentials", "sandbox", "note", "number_of_assignments"]
        widgets = {
            "battery": forms.HiddenInput(),
            "title": forms.TextInput(),
            "note": forms.Textarea(attrs={"cols": 80, "rows": 2}),
        }


class HitGroupDetailsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = None
        self.helper.layout = Layout(
            Field("title"),
            Field("description"),
            Field("keywords"),
            Field("reward"),
            Field("auto_approval_delay"),
            Field("lifetime_in_hours"),
            Field("assignment_duration_in_hours"),
            Field("qualification_requirements"),
        )

    class Meta:
        model = HitGroupDetails
        fields = [
            "title",
            "description",
            "keywords",
            "reward",
            "auto_approval_delay",
            "lifetime_in_hours",
            "assignment_duration_in_hours",
            "qualification_requirements",
        ]

        widgets = {
            "title": forms.TextInput(),
            "description": forms.Textarea(attrs={"cols": 80, "rows": 2}),
            "keywords": forms.TextInput(),
        }
