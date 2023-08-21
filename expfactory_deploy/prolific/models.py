from django.db import models
from experiments.models import Battery, Subject, Assignment
from model_utils.models import TimeStampedModel

'''
Due to how prolific tracks time for payment we much chunk large batteries into
multiple batteries that can be done in single sittings.
'''
class StudyCollection(models.Model):
    name = models.TextField(blank=True)
    default_project = models.TextField(blank=True)
    # default_*

class Study(models.Model):
    battery = models.ForeignKey(Battery, null=True, on_delete=models.SET_NULL)
    study_collection = models.ForeignKey(StudyCollection, null=True, on_delete=models.SET_NULL)

    completion_url = models.URLField(max_length=65536, blank=True)
    study_name = models.TextField(blank=True)
    # rest of prolific study api fields go here

    def check_for_study(self):
        return

    def create_study(self, participant_id):
        # I believe we will need one participant id to create a study with custom_allowlist in place.
        return

    def list_study_submissions(self):
        return

    def add_to_allowlist(self, participant_id):
        return

class StudyRank(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    rank = models.IntegerField(
        default=0,
        verbose_name="Experiment order",
    )

class StudySubject(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    # or subject? can get at all the information through the relations one way or another

    def result_qa(self):
        return

class SimpleCC(TimeStampedModel):
    battery = models.OneToOneField(Battery, on_delete=models.CASCADE)
    completion_url = models.URLField(max_length=65536, blank=True)
