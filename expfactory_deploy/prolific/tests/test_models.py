import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from prolific import models as pm
from experiments import models as em
from users.models import Group


@pytest.fixture
def prolific_models():
    assignment = em.Assignment.objects.first()
    study_collection = pm.StudyCollection.objects.create(
        name='test sc',
    )
    study = pm.Study.objects.create(
        battery=assignment.battery,
        remote_id='study_id',
        study_collection=study_collection
    )
    study_subject = pm.StudySubject.objects.create(
        study=study,
        subject=assignment.subject,
        assignment=assignment,
        prolific_session_id='session_id'
    )
    scs = pm.StudyCollectionSubject.objects.create(
        study_collection=study_collection,
        subject=assignment.subject,
        group_index=5
    )
