# from model_utils.fields import StatusField
import reversion
from django.db import models
from django.urls import reverse
from model_utils import Choices
from model_utils.fields import MonitorField
from model_utils.models import StatusModel, TimeStampedModel


class RepoOrigin(models.Model):
    origin = models.URLField(unique=True)
    path = models.TextField()


@reversion.register()
class ExperimentRepo(models.Model):
    """ Location of a repository that contains an experiment """

    name = models.TextField()
    origin = models.ForeignKey(RepoOrigin, null=True, on_delete=models.SET_NULL)
    location = models.TextField()

    def get_absolute_url(self):
        return reverse("experiment-repo-detail", kwargs={"pk": self.pk})


@reversion.register()
class ExperimentInstance(models.Model):
    """ A specific point in time of an experiment. """

    note = models.TextField(blank=True)
    commit = models.TextField(blank=True)
    commit_date = models.DateField(blank=True)
    experiment_repo_id = models.ForeignKey(ExperimentRepo, on_delete=models.CASCADE)


@reversion.register()
class Battery(TimeStampedModel, StatusModel):
    """when a battery is "created" its a template.
    When cloned for it becomes a draft for deployment
    When published no further changes are allowed.
    Finally inactive prevents subjects from using it.
    """

    STATUS = Choices("template", "draft", "published", "inactive")
    name = models.TextField()
    template_id = models.ForeignKey(
        "Battery", on_delete=models.CASCADE, blank=True, null=True
    )
    experiment_instances = models.ManyToManyField(
        ExperimentInstance, through="BatteryExperiments"
    )
    consent = models.TextField(blank=True)
    insturctions = models.TextField(blank=True)
    advertisement = models.TextField(blank=True)


class BatteryExperiments(models.Model):
    """ Associate specific experiments with a deployment of a battery """

    experiment_instance = models.ForeignKey(
        ExperimentInstance, on_delete=models.CASCADE
    )
    battery = models.ForeignKey(Battery, on_delete=models.CASCADE)
    order = models.IntegerField(
        help_text="""
            Order for experiment presentation. Smaller numbers will be selected first, and equivalent numbers
            will be chosen from randomly.
        """,
        default=1,
        verbose_name="Experiment order",
    )


@reversion.register()
class ExperimentFramework(models.Model):
    """ Framework used by experiments. """

    pass


class Subject(models.Model):
    email = models.TextField(blank=True)
    mturk_id = models.TextField(blank=True)
    notes = models.TextField(blank=True)


class Assignment(models.Model):
    """ Associate a subject with a battery deployment that they should complete """

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    battery = models.ForeignKey(Battery, on_delete=models.CASCADE)


class Result(TimeStampedModel):
    """ Results from a particular experiment returned by subjects """

    battery = models.ForeignKey(Battery, on_delete=models.CASCADE)
    experiment_instance = models.ForeignKey(
        ExperimentInstance, on_delete=models.CASCADE
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    data = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
