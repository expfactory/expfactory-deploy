from django.db import models

from experiments import models as em

from model_utils.models import TimeStampedModel

class ResultQA(TimeStampedModel):
    exp_result = models.OneToOneField(em.Result, on_delete=models.CASCADE)
    qa_result = models.JSONField(blank=True)
    pass = models.Boolean(null=True, default=None)
    error = models.TextField(null=True)

'''
class ThresholdGroup(models.Model):
    name = models.TextField(blank=True, help_text="Name of group of thresholds.")

class Threshold(models.Model):
    experiment = models.ForeignKey(em.ExperimentRepo, on_delete=models.CASCADE)
    group = models.ForeignKey(Threshold, on_delete.CASCADE)
    threshold_values = models.JSONField()
'''
