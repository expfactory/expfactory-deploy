"""
Test settings and utilities for Prolific API mocking.

This module provides settings and utilities for testing Prolific integrations
without hitting the real API.
"""

import os
from unittest.mock import patch
from django.test import override_settings
from django.conf import settings

from prolific.tests.mock_api import ProlificAPIMock


# Test-specific settings
TEST_PROLIFIC_SETTINGS = {
    'PROLIFIC_KEY': 'test_token_12345',
    'PROLIFIC_DEFAULT_WORKSPACE': 'test_workspace_67890',
    'PROLIFIC_PARTICIPANT_PARAM': 'PROLIFIC_PID',
    'PROLIFIC_STUDY_PARAM': 'STUDY_ID', 
    'PROLIFIC_SESSION_PARAM': 'SESSION_ID'
}


class ProlificTestMixin:
    """
    Mixin class for test cases that need Prolific API mocking.
    
    Provides common setup and utilities for Prolific-related tests.
    """
    
    def setUp(self):
        """Set up test environment with mocked Prolific settings."""
        super().setUp()
        
        # Apply test settings
        for key, value in TEST_PROLIFIC_SETTINGS.items():
            setattr(settings, key, value)
    
    def mock_prolific_api(self, fail_mode=None):
        """Create a Prolific API mock for use in tests."""
        return ProlificAPIMock(fail_mode=fail_mode)
    
    def assert_prolific_api_called(self, mock_api, function_name, expected_calls=1):
        """Assert that a Prolific API function was called."""
        actual_calls = len([
            call for call in mock_api.call_history 
            if call['function'] == function_name
        ])
        self.assertEqual(
            actual_calls, 
            expected_calls, 
            f"Expected {expected_calls} calls to {function_name}, got {actual_calls}"
        )
    
    def get_prolific_api_calls(self, mock_api, function_name):
        """Get all calls to a specific Prolific API function."""
        return [
            call for call in mock_api.call_history 
            if call['function'] == function_name
        ]


def with_mocked_prolific_api(fail_mode=None):
    """
    Class decorator to automatically mock Prolific API for all test methods.
    
    Usage:
        @with_mocked_prolific_api()
        class MyTestCase(TestCase):
            def test_something(self):
                # Prolific API is automatically mocked
    """
    def decorator(test_class):
        # Store original setUp and tearDown
        original_setUp = getattr(test_class, 'setUp', None)
        original_tearDown = getattr(test_class, 'tearDown', None)
        
        def new_setUp(self):
            # Call original setUp if it exists
            if original_setUp:
                original_setUp(self)
            
            # Start mocking
            self._prolific_api_mock = ProlificAPIMock(fail_mode=fail_mode)
            self.mock_api = self._prolific_api_mock.__enter__()
            
            # Apply test settings
            self._settings_patches = []
            for key, value in TEST_PROLIFIC_SETTINGS.items():
                patcher = patch.object(settings, key, value)
                patcher.start()
                self._settings_patches.append(patcher)
        
        def new_tearDown(self):
            # Stop mocking
            if hasattr(self, '_prolific_api_mock'):
                self._prolific_api_mock.__exit__(None, None, None)
            
            # Stop settings patches
            if hasattr(self, '_settings_patches'):
                for patcher in self._settings_patches:
                    patcher.stop()
            
            # Call original tearDown if it exists
            if original_tearDown:
                original_tearDown(self)
        
        # Replace setUp and tearDown
        test_class.setUp = new_setUp
        test_class.tearDown = new_tearDown
        
        return test_class
    
    return decorator


def mock_prolific_settings(**overrides):
    """
    Context manager for temporarily overriding Prolific settings.
    
    Usage:
        with mock_prolific_settings(PROLIFIC_KEY='test_key'):
            # Code runs with mocked settings
    """
    test_settings = {**TEST_PROLIFIC_SETTINGS, **overrides}
    
    class MockSettings:
        def __enter__(self):
            self.patches = []
            for key, value in test_settings.items():
                patcher = patch.object(settings, key, value)
                patcher.start()
                self.patches.append(patcher)
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            for patcher in self.patches:
                patcher.stop()
    
    return MockSettings()


# Environment variable setup for testing
def setup_test_environment():
    """
    Set up environment variables for testing.
    Call this in your test configuration.
    """
    for key, value in TEST_PROLIFIC_SETTINGS.items():
        os.environ.setdefault(key, str(value))


# Pytest fixtures (if using pytest)
try:
    import pytest
    
    @pytest.fixture
    def mock_prolific_api():
        """Pytest fixture for mocking Prolific API."""
        with ProlificAPIMock() as mock_api:
            yield mock_api
    
    @pytest.fixture
    def mock_prolific_settings_fixture():
        """Pytest fixture for mocking Prolific settings."""
        with mock_prolific_settings():
            yield
    
    @pytest.fixture
    def prolific_error_api():
        """Pytest fixture for mocking Prolific API with errors."""
        with ProlificAPIMock(fail_mode='server_error') as mock_api:
            yield mock_api

except ImportError:
    # pytest not available, skip fixtures
    pass


# Common test data generators
def create_test_study_data(**overrides):
    """Create test data for study creation."""
    from .fixtures import ProlificAPIFixtures
    return ProlificAPIFixtures.create_study_request(**overrides)


def create_test_models(user=None):
    """
    Create a complete set of test models for Prolific testing.
    
    Returns a dictionary with all the created objects.
    """
    from django.contrib.auth import get_user_model
    from experiments.models import Battery
    from prolific.models import StudyCollection, Study
    
    User = get_user_model()
    
    if not user:
        user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )
    
    battery = Battery.objects.create(
        title='Test Battery',
        status='published',
        user=user
    )
    
    study_collection = StudyCollection.objects.create(
        name='Test Collection',
        project=TEST_PROLIFIC_SETTINGS['PROLIFIC_DEFAULT_WORKSPACE'],
        title='Test Study Collection',
        description='A test study collection for API testing',
        total_available_places=50,
        estimated_completion_time=30,
        reward=500
    )
    
    study = Study.objects.create(
        battery=battery,
        study_collection=study_collection,
        rank=0
    )
    
    return {
        'user': user,
        'battery': battery,
        'study_collection': study_collection,
        'study': study
    }


# Assertion helpers
def assert_study_created_correctly(study, expected_data):
    """Assert that a study was created with the expected data."""
    assert study.remote_id is not None, "Study should have remote_id set"
    assert study.completion_code is not None, "Study should have completion_code set"
    
    if 'name' in expected_data:
        # Note: The study name might be modified by the system
        assert expected_data['name'] in study.battery.title


def assert_api_error_handled(mock_api, function_name):
    """Assert that API errors are properly handled."""
    # Check that the function was called
    calls = [call for call in mock_api.call_history if call['function'] == function_name]
    assert len(calls) > 0, f"Expected {function_name} to be called"
    
    # In a real implementation, you might check for error logging
    # or specific error handling behavior


# Test data constants
SAMPLE_STUDY_DATA = {
    'name': 'Test Cognitive Study',
    'description': 'A comprehensive test of cognitive abilities',
    'external_study_url': 'https://deploy.expfactory.org/test/study',
    'estimated_completion_time': 45,
    'reward': 750,
    'total_available_places': 100
}

SAMPLE_PARTICIPANT_IDS = [
    'participant_001',
    'participant_002', 
    'participant_003',
    'participant_004',
    'participant_005'
]