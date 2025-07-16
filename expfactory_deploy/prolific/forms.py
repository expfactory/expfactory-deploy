from datetime import datetime
import ast
import csv
import json
import os

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Field, Layout, Submit, Div
from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.mail import EmailMessage
from django.forms import ModelForm
from django.forms import modelformset_factory, formset_factory

from experiments import models as exp_models
from prolific import models


class SimpleCCForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))

    class Meta:
        model = models.SimpleCC
        fields = ["completion_url"]


class StudyCollectionForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        time_based_fields = [
            "inter_study_delay",
            "study_time_to_warning",
            "time_to_start_first_study",
            "study_grace_interval",
            "collection_time_to_warning",
            "collection_grace_interval",
        ]
        for time_field in time_based_fields:
            self.fields[time_field].initial = "00:00:00"
        self.fields[
            "inter_study_delay"
        ].help_text = "hh:mm:ss - Time to wait before assigning prolific participants to the next study after completing the previous one."
        self.fields["screener_for"].queryset = models.StudyCollection.objects.order_by('-id')

    class Meta:
        model = models.StudyCollection
        fields = [
            "name",
            "project",
            "reward",
            "total_available_places",
            "estimated_completion_time",
            "title",
            "inter_study_delay",
            "description",
            "number_of_groups",
            "time_to_start_first_study",
            "failure_to_start_warning_message",
            "failure_to_start_message",
            "failure_to_start_grace_interval",
            "study_time_to_warning",
            "study_warning_message",
            "study_grace_interval",
            "study_kick_on_timeout",
            "collection_time_to_warning",
            "collection_warning_message",
            "collection_grace_interval",
            "collection_kick_on_timeout",
            "screener_for",
            "screener_rejection_message",
        ]
        widgets = {
            "name": forms.TextInput(),
            "project": forms.TextInput(),
            "title": forms.TextInput(),
        }


class StudyForm(ModelForm):
    class Meta:
        model = models.Study
        fields = ["battery"]


"""
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

"""


class BatteryRankForm(forms.Form):
    rank = forms.IntegerField()
    battery = forms.ModelChoiceField(queryset=exp_models.Battery.objects.all())

    class Meta:
        widgets = {
            "rank": forms.HiddenInput(),
            "battery": forms.HiddenInput(),
        }


BatteryRankFormset = formset_factory(
    form=BatteryRankForm,
    can_delete=True,
    extra=0,
)


class ParticipantIdForm(forms.Form):
    ids = forms.CharField(widget=forms.Textarea(attrs={"cols": 60, "rows": 25}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))

    def clean_ids(self):
        ids = self.cleaned_data["ids"]
        ids_split = ids.replace("\n", ",").split(",")
        ids_cleaned = [x.strip() for x in ids_split if len(x) > 4]
        return ids_cleaned

class ManualUploadForm(forms.Form):
    prolific_id = forms.CharField()
    study_id = forms.CharField()
    dataFile = forms.FileField()
    error = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit"))

    def clean_prolific_id(self):
        prolific_id = self.cleaned_data["prolific_id"]
        try:
            self.subject = exp_models.Subject.objects.get(prolific_id=prolific_id)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            raise forms.ValidationError('Prolific ID not found or has duplicate.')
        return self.cleaned_data["prolific_id"]

    def clean_study_id(self):
        study_id = self.cleaned_data["study_id"]
        try:
            self.study = models.Study.objects.get(remote_id=study_id)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            raise forms.ValidationError('Study ID not found.')
        return self.cleaned_data["study_id"]

    def write_to_file(self):
        study_id = self.study.remote_id
        subject_id = self.subject.prolific_id

        self.sub_dir = os.path.join(settings.MEDIA_ROOT, "uploads", f'sub-{subject_id}')
        os.makedirs(self.sub_dir, exist_ok=True)

        self.datetime = datetime.now()
        self.date = self.datetime.strftime("%y_%m_%d_%H_%M_%S")
        self.fname_stub = f"study-{study_id}_date-{self.date}"
        data_fname = os.path.join(self.sub_dir, f"{self.fname_stub}_upload.txt")
        self.data_fname = data_fname

        with open(data_fname, "wb") as fp:
            for chunk in self.cleaned_data["dataFile"].chunks():
                fp.write(chunk)
            fp.flush()

        error_fname = os.path.join(self.sub_dir, f"{self.fname_stub}_error.txt")
        with open(error_fname, 'w') as fp:
            fp.write(f'{self.cleaned_data["error"]}\n')

    def write_to_result(self):

        target = []
        lines = []
        with open(self.data_fname, 'r') as fp:
            cr = csv.reader(fp)
            lines = [x for x in cr]

        header = lines[0]

        for line in lines[1:]:
            obj = {}
            for i in range(len(header)):
                obj[header[i]] = line[i]
            target.append(obj)

        exp_id = None
        exp_ids = set([x["exp_id"] for x in target if x.get("exp_id", '') != ''])
        if len(exp_ids) == 1:
            exp_id = exp_ids.pop()

        if exp_id is None:
            message = EmailMessage(
                f"Unable to find exp_id for manual upload by subject.",
                f"""
                    Subject: {self.subject.prolific_id}
                    Study: {self.study.remote_id}
                    Date: {self.date}
                """,
                settings.SERVER_EMAIL,
                [a[1] for a in settings.MANAGERS],
            )
            message.send()
            return

        export = {
          "current_trial": 0,
          "dateTime": self.datetime.timestamp(),
          "ip": "0.0.0.0",
          "prolific_id": self.subject.prolific_id,
          "status": "finished",
          "trialdata": target,
          "uniqueid": "0",
          "browser": {"userAgent": "manual_import"},
          "user_agent": "manual_import",
          "interactionData": []
        }

        ss = models.StudySubject.objects.get(subject=self.subject, study=self.study)
        assgn = ss.assignment

        results = assgn.results.filter(battery_experiment__experiment_instance__experiment_repo_id__name=exp_id)
        started_count = results.filter(status='started').count()
        other_count = results.exclude(status='started').count()

        if started_count == 1 and other_count == 0:
            result = results.get(status='started')
            if result.data != '':
                old_data_fname = os.join(self.sub_dir, f"{self.fname_stub}_old_data.json")
                old_data = ast.literal(result.data)
                with open(old_data_fname, 'w') as fp:
                    json.dump(fp)
            result.data = export
            result.status = 'completed'
            result.save()
            message = EmailMessage(
                f"Manual Upload Success",
                f"""
                    Subject: {self.subject.prolific_id}
                    Study: {self.study.remote_id}
                    Date: {self.date}
                    exp_id: {exp_id}
                    result id: {result.id}
                """,
                settings.SERVER_EMAIL,
                [a[1] for a in settings.MANAGERS],
            )
            message.send()
        else:
            message = EmailMessage(
                f"Unable to find unique result for manual upload by subject.",
                f"""
                    Subject: {self.subject.prolific_id}
                    Study: {self.study.remote_id}
                    Date: {self.date}
                    exp_id: {exp_id}
                    started_count: {started_count}
                    other_count: {other_count}
                """,
                settings.SERVER_EMAIL,
                [a[1] for a in settings.MANAGERS],
            )
            message.send()
        return
