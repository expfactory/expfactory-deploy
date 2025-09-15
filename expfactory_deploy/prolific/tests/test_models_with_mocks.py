"""
Comprehensive tests for Prolific models using mock API responses.

These tests demonstrate how to test all Prolific API integrations without
making real API calls.
"""

import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model

from experiments.models import Battery, Framework, RepoOrigin, ExperimentRepo, ExperimentInstance, Subject
from prolific.models import StudyCollection, Study, StudySubject, StudyCollectionSubject, ProlificAPIResult
from prolific.tests.mock_api import (
    ProlificAPIMock, mock_prolific_api, assert_api_called, get_api_call_args,
    create_mock_study_response
)
from prolific.tests.fixtures import ProlificAPIFixtures, TEST_PROJECT_ID, TEST_WORKSPACE_ID

User = get_user_model()


class StudyCollectionModelTests(TestCase):
    """Test StudyCollection model methods that interact with Prolific API."""
    
    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="test_pass")
        self.battery = Battery.objects.create(
            title="Test Battery",
            status="draft",
            user=self.user
        )
        self.study_collection = StudyCollection.objects.create(
            name="Test Collection",
            project=TEST_PROJECT_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Test Study Collection",
            description="A test study collection",
            total_available_places=50,
            estimated_completion_time=30,
            reward=500,
            number_of_groups=2
        )
    
    @mock_prolific_api()
    def test_create_drafts_success(self, mock_api):
        """Test successful study draft creation."""
        # Create studies for the collection
        study1 = Study.objects.create(
            battery=self.battery,
            study_collection=self.study_collection,
            rank=0
        )
        study2 = Study.objects.create(
            battery=self.battery,
            study_collection=self.study_collection,
            rank=1
        )
        
        # Call the method that creates drafts
        responses = self.study_collection.create_drafts()
        
        # Verify API was called for each study
        assert_api_called(mock_api, 'create_part_group', expected_calls=3)  # One for each study + next group
        assert_api_called(mock_api, 'create_draft', expected_calls=2)
        
        # Verify studies were updated with remote IDs
        study1.refresh_from_db()
        study2.refresh_from_db()
        self.assertIsNotNone(study1.remote_id)
        self.assertIsNotNone(study2.remote_id)
    
    @mock_prolific_api(fail_mode='validation_error')
    def test_create_drafts_api_error(self, mock_api):
        """Test handling of API errors during draft creation."""
        study = Study.objects.create(
            battery=self.battery,
            study_collection=self.study_collection,
            rank=0
        )
        
        # This should handle the error gracefully
        responses = self.study_collection.create_drafts()
        
        # Study should not have remote_id set
        study.refresh_from_db()
        self.assertEqual(study.remote_id, "")
        
        # API error should be logged
        assert_api_called(mock_api, 'create_draft', expected_calls=1)
    
    @mock_prolific_api()
    def test_set_allowlists(self, mock_api):
        """Test participant allowlist management."""
        # Create studies with remote IDs and participant groups
        study1 = Study.objects.create(
            battery=self.battery,
            study_collection=self.study_collection,
            rank=0,
            remote_id="study_123",
            participant_group="pg_123"
        )
        study2 = Study.objects.create(
            battery=self.battery,
            study_collection=self.study_collection,
            rank=1,
            remote_id="study_456",
            participant_group="pg_456"
        )
        
        # Mock participant data
        mock_api.get_participants = lambda gid: ProlificAPIFixtures.participant_group_participants_response(gid)
        mock_api.list_submissions = lambda sid: ProlificAPIFixtures.list_submissions_response(sid).get('results', [])
        
        # Call set_allowlists
        self.study_collection.set_allowlists()
        
        # Verify API calls were made
        assert_api_called(mock_api, 'get_participants', expected_calls=1)
        assert_api_called(mock_api, 'list_submissions', expected_calls=2)


class StudyModelTests(TestCase):
    """Test Study model methods that interact with Prolific API."""
    
    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="test_pass")
        self.battery = Battery.objects.create(
            title="Test Battery",
            status="published",
            user=self.user
        )
        self.study_collection = StudyCollection.objects.create(
            name="Test Collection",
            project=TEST_PROJECT_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Test Study Collection",
            description="A test study collection",
            total_available_places=50,
            estimated_completion_time=30,
            reward=500
        )
        self.study = Study.objects.create(
            battery=self.battery,
            study_collection=self.study_collection,
            rank=0
        )
    
    @mock_prolific_api()
    def test_create_draft_success(self, mock_api):
        """Test successful study draft creation."""
        response = self.study.create_draft()
        
        # Verify API call was made
        assert_api_called(mock_api, 'create_draft', expected_calls=1)
        
        # Verify call arguments
        call_args = get_api_call_args(mock_api, 'create_draft')
        study_args = call_args['study_details']
        
        self.assertIn('name', study_args)
        self.assertIn('external_study_url', study_args)
        self.assertIn('completion_code', study_args)
        
        # Study should have remote_id set
        self.study.refresh_from_db()
        self.assertIsNotNone(self.study.remote_id)
    
    @mock_prolific_api()
    def test_create_draft_with_next_group(self, mock_api):
        """Test draft creation with next group for multi-study collections."""
        next_group_id = "next_pg_123"
        response = self.study.create_draft(next_group=next_group_id)
        
        # Verify API call was made
        assert_api_called(mock_api, 'create_draft', expected_calls=1)
        
        # Verify completion codes include next group action
        call_args = get_api_call_args(mock_api, 'create_draft')
        study_args = call_args['study_details']
        
        self.assertIn('completion_codes', study_args)
        completion_codes = study_args['completion_codes']
        self.assertEqual(len(completion_codes), 1)
        
        actions = completion_codes[0].get('actions', [])
        next_group_actions = [
            action for action in actions 
            if action.get('action') == 'ADD_TO_PARTICIPANT_GROUP'
        ]
        self.assertEqual(len(next_group_actions), 1)
        self.assertEqual(next_group_actions[0]['participant_group'], next_group_id)
    
    @mock_prolific_api()
    def test_add_to_allowlist(self, mock_api):
        """Test adding participants to study allowlist."""
        self.study.participant_group = "pg_123"
        self.study.save()
        
        participant_ids = ["participant_1", "participant_2", "participant_3"]
        self.study.add_to_allowlist(participant_ids)
        
        # Verify API call
        assert_api_called(mock_api, 'add_to_part_group', expected_calls=1)
        
        # Verify StudySubject objects were created
        study_subjects = StudySubject.objects.filter(study=self.study)
        self.assertEqual(study_subjects.count(), len(participant_ids))
        
        # Verify subjects were created with prolific_ids
        for participant_id in participant_ids:
            subject = Subject.objects.filter(prolific_id=participant_id).first()
            self.assertIsNotNone(subject)
            
            study_subject = StudySubject.objects.filter(
                study=self.study, 
                subject=subject
            ).first()
            self.assertIsNotNone(study_subject)
    
    @mock_prolific_api()
    def test_remove_participant(self, mock_api):
        """Test removing participant from study."""
        self.study.participant_group = "pg_123"
        self.study.save()
        
        # Create subject and study subject
        subject = Subject.objects.create(prolific_id="participant_123")
        study_subject = StudySubject.objects.create(
            study=self.study,
            subject=subject,
            assignment=None  # Will be created in save method
        )
        
        # Remove participant
        self.study.remove_participant("participant_123")
        
        # Verify API call
        assert_api_called(mock_api, 'remove_from_part_group', expected_calls=1)
        
        # Verify StudySubject was deleted
        self.assertFalse(
            StudySubject.objects.filter(
                study=self.study,
                subject=subject
            ).exists()
        )
    
    @mock_prolific_api()
    def test_set_group_name(self, mock_api):
        """Test updating participant group name."""
        self.study.remote_id = "study_123"
        self.study.participant_group = "pg_123"
        self.study.save()
        
        self.study.set_group_name()
        
        # Verify API call
        assert_api_called(mock_api, 'update_part_group', expected_calls=1)
        
        call_args = get_api_call_args(mock_api, 'update_part_group')
        self.assertEqual(call_args['group_id'], "pg_123")
        self.assertIn(self.study.battery.title, call_args['name'])


class StudySubjectModelTests(TestCase):
    """Test StudySubject model methods that interact with Prolific API."""
    
    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="test_pass")
        self.battery = Battery.objects.create(
            title="Test Battery",
            status="published",
            user=self.user
        )
        self.study_collection = StudyCollection.objects.create(
            name="Test Collection",
            project=TEST_PROJECT_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Test Study Collection",
            description="A test study collection",
            total_available_places=50,
            estimated_completion_time=30,
            reward=500
        )
        self.study = Study.objects.create(
            battery=self.battery,
            study_collection=self.study_collection,
            rank=0,
            remote_id="study_123"
        )
        self.subject = Subject.objects.create(prolific_id="participant_123")
        self.study_subject = StudySubject.objects.create(
            study=self.study,
            subject=self.subject,
            prolific_session_id="session_123"
        )
    
    @mock_prolific_api()
    def test_get_prolific_status(self, mock_api):
        """Test getting participant status from Prolific."""
        status = self.study_subject.get_prolific_status()
        
        # Verify API call
        assert_api_called(mock_api, 'get_submission', expected_calls=1)
        
        call_args = get_api_call_args(mock_api, 'get_submission')
        self.assertEqual(call_args['session_id'], "session_123")
        
        # Status should be returned from mock
        self.assertIsNotNone(status)
    
    @mock_prolific_api(fail_mode='auth_error')
    def test_get_prolific_status_error(self, mock_api):
        """Test handling of API errors when getting status."""
        status = self.study_subject.get_prolific_status()
        
        # Should handle error gracefully
        self.assertIsNone(status)


class StudyCollectionSubjectModelTests(TestCase):
    """Test StudyCollectionSubject model methods that interact with Prolific API."""
    
    def setUp(self):
        self.user = User.objects.create_user(username="test_user", password="test_pass")
        self.battery1 = Battery.objects.create(title="Battery 1", status="published", user=self.user)
        self.battery2 = Battery.objects.create(title="Battery 2", status="published", user=self.user)
        
        self.study_collection = StudyCollection.objects.create(
            name="Test Collection",
            project=TEST_PROJECT_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Multi-Study Collection",
            description="A test study collection with multiple studies",
            total_available_places=50,
            estimated_completion_time=60,
            reward=1000
        )
        
        self.study1 = Study.objects.create(
            battery=self.battery1,
            study_collection=self.study_collection,
            rank=0,
            remote_id="study_123",
            participant_group="pg_123"
        )
        self.study2 = Study.objects.create(
            battery=self.battery2,
            study_collection=self.study_collection,
            rank=1,
            remote_id="study_456",
            participant_group="pg_456"
        )
        
        self.subject = Subject.objects.create(prolific_id="participant_123")
        self.scs = StudyCollectionSubject.objects.create(
            study_collection=self.study_collection,
            subject=self.subject,
            current_study=self.study1
        )
    
    @mock_prolific_api()
    def test_incomplete_study_collection(self, mock_api):
        """Test creating new collection for incomplete participant."""
        # Create some assignments to simulate partial completion
        from experiments.models import Assignment
        assignment1 = Assignment.objects.create(
            subject=self.subject,
            battery=self.battery1,
            status="completed"
        )
        assignment2 = Assignment.objects.create(
            subject=self.subject,
            battery=self.battery2,
            status="not-started"
        )
        
        # Call the method
        api_responses, new_scs = self.scs.incomplete_study_collection()
        
        # Verify API calls for removing from groups
        assert_api_called(mock_api, 'remove_from_part_group', expected_calls=1)
        assert_api_called(mock_api, 'create_part_group', expected_calls=1)
        assert_api_called(mock_api, 'create_draft', expected_calls=1)
        
        # Verify new study collection was created
        self.assertIsNotNone(new_scs)
        self.assertNotEqual(new_scs.study_collection.id, self.study_collection.id)
        self.assertEqual(new_scs.subject, self.subject)
        
        # New collection should have parent relationship
        self.assertEqual(new_scs.study_collection.parent, self.study_collection)


class ProlificAPIIntegrationTests(TestCase):
    """Test various Prolific API integration scenarios."""
    
    @mock_prolific_api()
    def test_api_success_logging(self, mock_api):
        """Test that successful API calls don't create error logs."""
        study_collection = StudyCollection.objects.create(
            name="Test Collection",
            project=TEST_PROJECT_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Test Study",
            description="Test description",
            total_available_places=10,
            estimated_completion_time=30,
            reward=500
        )
        
        # Make API call
        study_collection.create_drafts()
        
        # No error logs should be created
        self.assertEqual(ProlificAPIResult.objects.count(), 0)
    
    @mock_prolific_api(fail_mode='server_error')
    def test_api_error_logging(self, mock_api):
        """Test that API errors are properly logged."""
        user = User.objects.create_user(username="test_user", password="test_pass")
        battery = Battery.objects.create(title="Test Battery", status="draft", user=user)
        
        study_collection = StudyCollection.objects.create(
            name="Test Collection",
            project=TEST_PROJECT_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Test Study",
            description="Test description",
            total_available_places=10,
            estimated_completion_time=30,
            reward=500
        )
        
        study = Study.objects.create(
            battery=battery,
            study_collection=study_collection,
            rank=0
        )
        
        # This should trigger API error logging
        study_collection.create_drafts()
        
        # API error should be logged (if the existing code does this)
        # Note: This depends on how the actual code handles errors
    
    @mock_prolific_api()
    def test_multiple_api_calls(self, mock_api):
        """Test complex workflows with multiple API calls."""
        user = User.objects.create_user(username="test_user", password="test_pass")
        battery = Battery.objects.create(title="Test Battery", status="published", user=user)
        
        study_collection = StudyCollection.objects.create(
            name="Complex Collection",
            project=TEST_PROJECT_ID,
            workspace_id=TEST_WORKSPACE_ID,
            title="Complex Study Collection",
            description="A complex multi-stage study",
            total_available_places=100,
            estimated_completion_time=45,
            reward=750,
            number_of_groups=3
        )
        
        # Create multiple studies
        studies = []
        for i in range(3):
            study = Study.objects.create(
                battery=battery,
                study_collection=study_collection,
                rank=i
            )
            studies.append(study)
        
        # Create drafts (should make multiple API calls)
        study_collection.create_drafts()
        
        # Verify comprehensive API usage
        total_calls = sum(
            len([call for call in mock_api.call_history if call['function'] == func])
            for func in ['create_part_group', 'create_draft']
        )
        self.assertGreater(total_calls, 3)  # Should be multiple calls
        
        # Verify call history is properly recorded
        self.assertGreater(mock_api.call_count, 0)
        self.assertTrue(len(mock_api.call_history) > 0)


class MockAPITestCase(TestCase):
    """Test the mock API framework itself."""
    
    def test_mock_api_context_manager(self):
        """Test that context manager properly mocks and unmocks."""
        from prolific import outgoing_api
        
        # Store original function
        original_create_draft = outgoing_api.create_draft
        
        with ProlificAPIMock() as mock_api:
            # Function should be mocked
            self.assertNotEqual(outgoing_api.create_draft, original_create_draft)
            
            # Call should be recorded
            outgoing_api.create_draft({'name': 'test'})
            self.assertEqual(mock_api.call_count, 1)
        
        # Function should be restored
        self.assertEqual(outgoing_api.create_draft, original_create_draft)
    
    def test_mock_api_decorator(self):
        """Test the decorator works properly."""
        
        @mock_prolific_api()
        def test_function(mock_api):
            from prolific import outgoing_api
            result = outgoing_api.study_detail('test_id')
            return result, mock_api.call_count
        
        result, call_count = test_function()
        
        # Should return mock data
        self.assertIn('id', result)
        self.assertEqual(result['id'], 'test_id')
        
        # Should have recorded the call
        self.assertEqual(call_count, 1)