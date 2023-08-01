from django.db import models
from experiments.models import Battery, Subject, Assignment
from model_utils.models import TimeStampedModel

'''
A deployment represents a battery that we want run on prolific.
We will need to create a prolific project for it.
If we need to pay subjects seperately for each experiment we will
need to create a study for each user and each experiment.

class Deployment(TimeStampedModel):
    project = models.TextField()
    battery = models.ForeignKey(Battery, null=True, on_delete=models.SET_NULL)
    per_subject_study = models.BooleanField(default=False)

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
'''

class SimpleCC(TimeStampedModel):
    battery = models.OneToOneField(Battery, on_delete=models.CASCADE)
    completion_url = models.URLField(max_length=65536, blank=True)
