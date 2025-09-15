"""
Simple examples showing how to test Prolific API integrations.

This file demonstrates the key testing patterns for different scenarios.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

from experiments.models import Battery
from prolific.models import StudyCollection, Study
from prolific.tests.mock_api import mock_prolific_api, assert_api_called
from prolific.tests.fixtures import TEST_PROJECT_ID, TEST_WORKSPACE_ID

User = get_user_model()


class ProlificTestingExamples(TestCase):
    """Examples of how to test different Prolific API scenarios."""
    
    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="test_pass")
        self.battery = Battery.objects.create(
            title="Example Battery",
            status="published",
            user=self.user
        )
    
    @mock_prolific_api()
    def test_successful_study_creation(self, mock_api):
        """Example: Test successful study creation with API mocking."""
        study_collection = StudyCollection.objects.create(
            name="Example Collection",
            project=TEST_PROJECT_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Example Study",
            description="An example study for testing",
            total_available_places=10,
            estimated_completion_time=20,
            reward=300
        )
        
        study = Study.objects.create(
            battery=self.battery,
            study_collection=study_collection,
            rank=0
        )
        
        # Call the method that interacts with Prolific API
        response = study.create_draft()
        
        # Verify the API was called correctly
        assert_api_called(mock_api, 'create_draft', expected_calls=1)
        
        # Verify the study was updated with response data
        study.refresh_from_db()
        self.assertIsNotNone(study.remote_id)
        self.assertIsNotNone(study.completion_code)
    
    @mock_prolific_api(fail_mode='auth_error')
    def test_api_authentication_error(self, mock_api):
        """Example: Test handling of authentication errors."""
        study_collection = StudyCollection.objects.create(
            name="Example Collection",
            project=TEST_PROJECT_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Example Study",
            description="An example study for testing",
            total_available_places=10,
            estimated_completion_time=20,
            reward=300
        )
        
        study = Study.objects.create(
            battery=self.battery,
            study_collection=study_collection,
            rank=0
        )
        
        # This will return a 401 authentication error
        response = study.create_draft()
        
        # Verify API was called but study wasn't updated due to error
        assert_api_called(mock_api, 'create_draft', expected_calls=1)
        
        study.refresh_from_db()
        self.assertEqual(study.remote_id, "")  # Should remain empty on error
    
    @mock_prolific_api()
    def test_participant_management(self, mock_api):
        """Example: Test participant management operations."""
        study_collection = StudyCollection.objects.create(
            name="Participant Test Collection",
            project=TEST_PROJECT_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Participant Management Study",
            description="Testing participant operations",
            total_available_places=50,
            estimated_completion_time=30,
            reward=500
        )
        
        study = Study.objects.create(
            battery=self.battery,
            study_collection=study_collection,
            rank=0,
            participant_group="test_pg_123"  # Simulate existing group
        )
        
        # Add participants to the study
        participant_ids = ["participant_1", "participant_2", "participant_3"]
        study.add_to_allowlist(participant_ids)
        
        # Verify API calls
        assert_api_called(mock_api, 'add_to_part_group', expected_calls=1)
        
        # Verify database objects were created
        from prolific.models import StudySubject
        study_subjects = StudySubject.objects.filter(study=study)
        self.assertEqual(study_subjects.count(), len(participant_ids))
    
    @mock_prolific_api()
    def test_complex_workflow(self, mock_api):
        """Example: Test a complex multi-step workflow."""
        study_collection = StudyCollection.objects.create(
            name="Complex Workflow Collection",
            project=TEST_PROJECT_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Multi-Step Study Collection",
            description="Testing complex workflows",
            total_available_places=100,
            estimated_completion_time=60,
            reward=1000,
            number_of_groups=2
        )
        
        # Create multiple studies in the collection
        study1 = Study.objects.create(
            battery=self.battery,
            study_collection=study_collection,
            rank=0
        )
        study2 = Study.objects.create(
            battery=self.battery,
            study_collection=study_collection,
            rank=1
        )
        
        # Execute the complex workflow
        responses = study_collection.create_drafts()
        
        # Verify multiple API calls were made in the correct order
        api_calls = mock_api.call_history
        
        # Should have calls to create participant groups and study drafts
        group_calls = [call for call in api_calls if call['function'] == 'create_part_group']
        draft_calls = [call for call in api_calls if call['function'] == 'create_draft']
        
        self.assertGreater(len(group_calls), 0)
        self.assertEqual(len(draft_calls), 2)  # One for each study
        
        # Verify both studies were updated
        study1.refresh_from_db()
        study2.refresh_from_db()
        
        self.assertIsNotNone(study1.remote_id)
        self.assertIsNotNone(study2.remote_id)
        self.assertNotEqual(study1.remote_id, study2.remote_id)  # Should be different
    
    def test_without_api_mocking(self):
        """Example: Test logic that doesn't require API calls."""
        study_collection = StudyCollection.objects.create(
            name="No API Collection",
            project=TEST_PROJECT_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Local Logic Study",
            description="Testing local logic only",
            total_available_places=25,
            estimated_completion_time=15,
            reward=250
        )
        
        # Test properties and methods that don't make API calls
        self.assertEqual(study_collection.study_count, 0)
        self.assertFalse(study_collection.deployed)
        
        # Add a study and test again
        Study.objects.create(
            battery=self.battery,
            study_collection=study_collection,
            rank=0,
            remote_id="test_remote_123"  # Simulate deployed study
        )
        
        self.assertEqual(study_collection.study_count, 1)
        self.assertTrue(study_collection.deployed)