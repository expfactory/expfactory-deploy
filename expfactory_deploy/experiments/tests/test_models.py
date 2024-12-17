import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from experiments.models import (
    Battery,
    BatteryExperiments,
    ExperimentInstance,
    ExperimentRepo,
    Framework,
    RepoOrigin,
    Subject,
    Assignment,
    ExperimentOrder,
)
from users.models import Group


@pytest.mark.django_db
@pytest.fixture
def all_models():
    # Create a user and group
    user = get_user_model().objects.create(username="testuser")
    group = Group.objects.create(name="testgroup")

    # Create a framework
    framework = Framework.objects.create(name="test_framework", template="template")

    # Create a RepoOrigin
    repo_origin = RepoOrigin.objects.create(
        url="https://github.com/test/repo.git", path="/path/to/repo", name="test_repo"
    )

    # Create an ExperimentRepo
    experiment_repo = ExperimentRepo.objects.create(
        name="test_experiment_repo",
        origin=repo_origin,
        branch="main",
        location="/path/to/experiment",
        framework=framework,
    )

    # Create an ExperimentInstance
    experiment_instance = ExperimentInstance.objects.create(
        note="test note", commit="abc123", experiment_repo_id=experiment_repo
    )

    # Create a Battery
    battery = Battery.objects.create(
        title="test_battery",
        user=user,
        group=group,
        instructions="test instructions somewhat unique",
        consent="test consent",
    )

    # Create a BatteryExperiments
    battery_experiment = BatteryExperiments.objects.create(
        experiment_instance=experiment_instance, battery=battery, order=1
    )

    # Create a Subject
    subject = Subject.objects.create(handle="test_subject")

    # Create an Assignment
    assignment = Assignment.objects.create(subject=subject, battery=battery)

    # Create an ExperimentOrder
    experiment_order = ExperimentOrder.objects.create(
        name="test_order", battery=battery
    )


@pytest.mark.django_db
def test_model_relationships(all_models):
    # Get models from fixture
    repo_origin = RepoOrigin.objects.first()
    experiment_repo = ExperimentRepo.objects.first()
    experiment_instance = ExperimentInstance.objects.first()
    battery = Battery.objects.first()
    battery_experiment = BatteryExperiments.objects.first()
    subject = Subject.objects.first()
    assignment = Assignment.objects.first()
    experiment_order = ExperimentOrder.objects.first()

    # Assertions to verify relationships
    assert experiment_repo.origin == repo_origin
    assert experiment_instance.experiment_repo_id == experiment_repo
    assert battery_experiment.experiment_instance == experiment_instance
    assert battery_experiment.battery == battery
    assert assignment.subject == subject
    assert assignment.battery == battery
    assert experiment_order.battery == battery

    # Check reverse relationships
    assert battery.experiment_instances.count() == 1
    assert battery.experiment_instances.first() == experiment_instance
    assert subject.assignment_set.count() == 1
    assert subject.assignment_set.first() == assignment
