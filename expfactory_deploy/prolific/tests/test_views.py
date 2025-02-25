from urllib.parse import urlencode
import pytest

from django.conf import settings
from django.test import Client
from django.urls import reverse

from pytest_django.asserts import assertTemplateUsed

import experiments.views as views
import experiments.models as em
import prolific.models as pm
from experiments import forms
from experiments.tests.test_models import all_models

from prolific.tests.test_models import prolific_models


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_serve_consent(client, all_models, prolific_models):
    study_subject = pm.StudySubject.objects.first()
    assignment = study_subject.assignment
    response = client.get(
        reverse("prolific:consent", kwargs={"battery_id": assignment.battery.pk}),
        data={
            settings.PROLIFIC_PARTICIPANT_PARAM: 'part_id',
            settings.PROLIFIC_STUDY_PARAM: 'study_id',
            settings.PROLIFIC_SESSION_PARAM: 'session_id',
        }
    )
    assert response.status_code == 200
    assert assignment.battery.consent in response.content.decode("utf-8")
    assert assignment.battery.instructions not in response.content.decode("utf-8")

    base = reverse("prolific:consent", kwargs={"battery_id": assignment.battery.pk})
    params = urlencode({
        settings.PROLIFIC_PARTICIPANT_PARAM: 'part_id',
        settings.PROLIFIC_STUDY_PARAM: 'study_id',
        settings.PROLIFIC_SESSION_PARAM: 'session_id',
    })
    url = f'{base}?{params}'

    form = forms.ConsentForm({'accept': True})
    response = client.post(
        url,
        data=form.data,
        follow=True,

    )
    assert response.status_code == 200
    print(assignment.consent_accepted)
    assert assignment.battery.consent not in response.content.decode("utf-8")
    assert assignment.battery.instructions in response.content.decode("utf-8")
    assert response.wsgi_request.GET[settings.PROLIFIC_PARTICIPANT_PARAM] == 'part_id'
    assert response.wsgi_request.GET[settings.PROLIFIC_STUDY_PARAM] == 'study_id'


@pytest.mark.django_db
def test_serve_battery(client, all_models, prolific_models):
    study_subject = pm.StudySubject.objects.first()
    assignment = study_subject.assignment
    assignment.consent_accepted = False
    assignment.save()

    response = client.get(
        reverse("prolific:serve-battery", kwargs={"battery_id": assignment.battery.pk}),
        data={
            settings.PROLIFIC_PARTICIPANT_PARAM: 'part_id',
            settings.PROLIFIC_STUDY_PARAM: 'study_id',
            settings.PROLIFIC_SESSION_PARAM: 'session_id',
        },
        follow=True
    )
    assert response.status_code == 200
    assert assignment.battery.consent in response.content.decode("utf-8")

    assignment.consent_accepted = True
    assignment.save()

    response = client.get(
        reverse("prolific:serve-battery", kwargs={"battery_id": assignment.battery.pk}),
        data={
            settings.PROLIFIC_PARTICIPANT_PARAM: 'part_id',
            settings.PROLIFIC_STUDY_PARAM: 'study_id',
            settings.PROLIFIC_SESSION_PARAM: 'session_id',
        },
        follow=True
    )
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert assignment.battery.consent not in content
    assert "group_index': 5" in content
