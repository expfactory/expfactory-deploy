import pytest
from django.test import Client
from django.urls import reverse

from pytest_django.asserts import assertTemplateUsed

import experiments.views as views
import experiments.models as models
from experiments.tests.test_models import all_models



@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_preview_consent(client, all_models):
    battery = models.Battery.objects.first()
    response = client.get(
        reverse("experiments:preview-consent", kwargs={"battery_id": battery.pk})
    )
    assert response.status_code == 200
    assert battery.consent in response.content.decode("utf-8")


@pytest.mark.django_db
def test_serve_consent(client, all_models):
    assignment = models.Assignment.objects.first()
    response = client.get(
        reverse("experiments:consent", kwargs={"assignment_id": assignment.pk})
    )
    assert response.status_code == 200
    assert assignment.battery.consent in response.content.decode("utf-8")
    assert assignment.battery.instructions not in response.content.decode("utf-8")
    assignment.consent_accepted = True
    assignment.save()

    response = client.get(
        reverse("experiments:consent", kwargs={"assignment_id": assignment.pk}),
        follow=True
    )
    assert response.status_code == 200
    assert assignment.battery.consent not in response.content.decode("utf-8")
    assert assignment.battery.instructions in response.content.decode("utf-8")

@pytest.mark.django_db
def test_serve_battery(client, all_models):
    assignment = models.Assignment.objects.first()
    assignment.consent_accepted = False
    assignment.save()

    response = client.get(
        reverse("experiments:serve-battery", kwargs={"battery_id": assignment.battery.pk, "subject_id": assignment.subject.pk}),
        follow=True
    )
    assert response.status_code == 200
    assert assignment.battery.consent in response.content.decode("utf-8")

    assignment.consent_accepted = True
    assignment.save()

    response = client.get(
        reverse("experiments:serve-battery", kwargs={"battery_id": assignment.battery.pk, "subject_id": assignment.subject.pk}),
        follow=True
    )
    assert response.status_code == 200
    assert not(assignment.battery.consent in response.content.decode("utf-8"))
