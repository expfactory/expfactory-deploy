from django.test import TestCase
from experiments import models
from mturk import boto_utils as bu
import time
import uuid

test_url = f"https://example.com/{uuid.uuid4()}"


class BotoUtils(TestCase):
    def setup(self):
        er = models.ExperimentRepo.create(name="text_experiment_repo", location="/tmp/")
        ei = models.ExperimentInstance.create(experiment_repo_id=er)
        batt = models.Battery.create(status="draft", title="test_battery")
        models.BatteryExperiments.create(experiment_instance=ei, battery=batt)

    def test_generate_hit(self):
        title = "test_title"
        hit = bu.generate_hit(Title=title)
        self.assertEqual(hit["Title"], title)

    def test_submit_then_expire(self):
        print(test_url)
        bw = bu.BotoWrapper()
        title = "test_title"
        question = bu.generate_question_xml(test_url)
        hit = bu.generate_hit(Title=title, Question=question)
        hit = bu.generate_hit(Title=title, Question=question)
        response = bw.create_hit_batches(hit)
        time.sleep(10)
        all_hits = bw.get_hits()
        self.assertIn(test_url, all_hits)
        time.sleep(10)
        hits = bw.get_active_hits()
        self.assertIn(test_url, hits)
        bw.expire_hits_by_url(test_url)
        time.sleep(10)
        bw.delete_hits(test_url)
        time.sleep(10)
        hits = bw.get_active_hits()
        self.assertNotIn(test_url, hits)
