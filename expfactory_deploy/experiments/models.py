import uuid
from pathlib import Path

import git
import reversion
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from model_utils import Choices
from model_utils.fields import MonitorField, StatusField
from model_utils.models import StatusModel, TimeStampedModel

from .utils import repo as repo


class SubjectTaskStatusModel(StatusModel):
    """Abstract class that tracks the various states a subject might
    be in relation to either an experiment or a battery"""

    STATUS = Choices("not-started", "started", "completed", "failed")
    status = StatusField()
    started_at = MonitorField(monitor="status", when=["started"])
    completed_at = MonitorField(monitor="status", when=["completed"])
    failed_at = MonitorField(monitor="status", when=["failed"])

    @property
    def completed(self):
        return self.status == self.STATUS.completed

    class Meta:
        abstract = True


class RepoOrigin(models.Model):
    """ Location of a repository that contains an experiment """

    origin = models.URLField(unique=True)
    path = models.TextField()
    name = models.TextField(blank=True, unique=True)

    def __str__(self):
        return self.origin

    def get_latest_commit(self):
        return repo.get_latest_commit(self.path)

    def is_valid_commit(self, commit):
        return repo.is_valid_commit(self.path, commit)

    def checkout_commit(self, commit):
        base_repo = git.Repo(self.path)
        stem = Path(self.path).stem
        deploy_to = str(Path(settings.DEPLOYMENT_DIR, stem, commit))
        if deploy_to in base_repo.git.worktree("list"):
            return deploy_to
        elif not repo.is_valid_commit(self.path, commit):
            return False
        else:
            base_repo.git.worktree("add", deploy_to, commit)
            return deploy_to


@reversion.register()
class ExperimentRepo(models.Model):
    """ Location of an experiment and the repository it belongs to """

    name = models.TextField()
    origin = models.ForeignKey(RepoOrigin, null=True, on_delete=models.SET_NULL)
    location = models.TextField()

    def get_absolute_url(self):
        return reverse("experiment-repo-detail", kwargs={"pk": self.pk})

    """ We may want to just look at latest commit for files in its directory(location)
        instead of getting entire repos latest commit """

    def get_latest_commit(self):
        return self.origin.get_latest_commit()

    def __str__(self):
        return self.name


@reversion.register()
class ExperimentInstance(models.Model):
    """ A specific point in time of an experiment. """

    note = models.TextField(blank=True)
    commit = models.TextField(blank=True)
    commit_date = models.DateField(blank=True, null=True)
    experiment_repo_id = models.ForeignKey(ExperimentRepo, on_delete=models.CASCADE)

    def is_valid_commit(self):
        return self.experiment_repo_id.origin.is_valid_commit(self.commit)

    def deploy_static(self):
        return self.experiment_repo_id.origin.checkout_commit(self.commit)

    def __str__(self):
        return f"{self.commit}"


@reversion.register()
class Battery(TimeStampedModel, StatusField):
    """when a battery is "created" its a template.
    When cloned for it becomes a draft for deployment
    When published no further changes are allowed.
    Finally inactive prevents subjects from using it.
    """

    STATUS = Choices("template", "draft", "published", "inactive")
    status = StatusField()
    title = models.TextField()
    template_id = models.ForeignKey(
        "Battery", on_delete=models.CASCADE, blank=True, null=True
    )
    experiment_instances = models.ManyToManyField(
        ExperimentInstance, through="BatteryExperiments"
    )
    consent = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    advertisement = models.TextField(blank=True)
    random_order = models.BooleanField(default="True")


class BatteryExperiments(models.Model):
    """ Associate specific experiments with a deployment of a battery """

    experiment_instance = models.ForeignKey(
        ExperimentInstance, on_delete=models.CASCADE
    )
    battery = models.ForeignKey(Battery, on_delete=models.CASCADE)
    order = models.IntegerField(
        default=0,
        verbose_name="Experiment order",
    )


@reversion.register()
class Framework(models.Model):
    """ Framework used by experiments. """

    name = models.TextField(unique=True)
    template = models.TextField()


class FrameworkResource(models.Model):
    name = models.TextField(unique=True)
    path = models.TextField()


class Subject(models.Model):
    email = models.TextField(blank=True)
    mturk_id = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)


class Assignment(SubjectTaskStatusModel):
    """ Associate a subject with a battery deployment that they should complete """

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    battery = models.ForeignKey(Battery, on_delete=models.CASCADE)
    consent_accepted = models.BooleanField(null=True)

    def get_next_experiment(self):
        order = "?" if self.battery.random_order else "order"
        experiments = (
            BatteryExperiments.objects.filter(battery=self.battery)
            .values("experiment_instance")
            .order_by(order)
        )
        exempt = list(
            Results.objects.filter(
                Q(status=Results.STATUS.completed) | Q(status=Results.STATUS.failed),
                subject=self.subject,
            )
        )
        unfinished = [exp for exp in experiments if exp not in exempt]
        if len(unfinished):
            return unfinished[0]
        else:
            return None

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_assignment", fields=["subject", "battery"]
            )
        ]


class Result(TimeStampedModel, SubjectTaskStatusModel):
    """ Results from a particular experiment returned by subjects """

    battery_experiment = models.ForeignKey(
        BatteryExperiments, on_delete=models.SET_NULL, null=True
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True)
    data = models.TextField(blank=True)
