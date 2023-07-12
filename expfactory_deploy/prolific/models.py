from django.db import models
from experiments.models import Battery, Subject, Assignment
from model_utils.models import TimeStampedModel

class Deployment(TimeStampedModel):
    project = models.TextField()
    battery = models.ForeignKey(Battery, null=True, on_delete=models.SET_NULL)
    per_subject_study = models.BooleanField(default=True)

    def deploy(self):
        # prolific api calls to make initial study for consent.
        return

class Study(TimeStampedModel):
    study_id = models.TextField()
    completion_url = models.TextField()
    estimated_completion_time = models.TextField()
    project = models.TextField()
    deployment = models.ForeignKey(Deployment, null=True, on_delete=models.SET_NULL)
    battery = models.ForeignKey(Battery, null=True, on_delete=models.SET_NULL)

class Session(TimeStampedModel):
    participant_id = models.TextField()
    study = models.ForeignKey(Study, null=True, on_delete=models.SET_NULL)
    assignment = models.ForeignKey(Assignment, null=True, on_delete=models.SET_NULL)
