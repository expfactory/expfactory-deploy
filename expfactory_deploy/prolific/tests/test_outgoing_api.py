import datetime

from django.conf import settings
from django.test import TestCase

from experiments import models as em
from prolific import models as pm
from prolific import outgoing_api as api
from users.models import User


TEST_PROJECT_ID="65d65f5231592c82a95db12c"
WORKSPACE_ID="6410d74c29d97f193806ca67"
class ProlificAPITest(TestCase):
    def setUp(self):
        self.scs = pm.StudyCollection.objects.create(
            name = "Automated API Test",
            project = TEST_PROJECT_ID,
            title = "Automated API Test",
            description = "Automated API Test",
            total_available_places = 1,
            estimated_completion_time = 1,
            reward = 14,
            published = 1,
            inter_study_delay = datetime.timedelta(hours=1),
            number_of_groups = 1
        )
        self.user = User.objects.create(username='test_user')
        self.batt1 = em.Battery.objects.create(
            status="draft",
            title="test_battery 1",
            user=self.user
        )
        self.batt2 = em.Battery.objects.create(
            status="draft",
            title="test_battery 2",
            user=self.user
        )
        self.study1 = pm.Study.objects.create(
            battery=self.batt1,
            study_collection=self.scs,
            rank=0
        )
        self.study2 = pm.Study.objects.create(
            battery=self.batt2,
            study_collection=self.scs,
            rank=0
        )


    def test_generate_hit(self):
        scs = list(pm.StudyCollection.objects.all())
        self.assertEqual(len(scs), 1)
