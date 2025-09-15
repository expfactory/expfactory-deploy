"""
Mock Prolific API client for testing.

This module provides drop-in replacements for Prolific API functions
that work with the existing outgoing_api.py without requiring changes.
"""

import json
from unittest.mock import Mock, patch
from typing import Dict, Any, Optional, List, Union
from .fixtures import ProlificAPIFixtures, MockProlificResponse


class MockProlificAPI:
    """
    Mock Prolific API that simulates all the functions in outgoing_api.py.
    
    Can be configured to simulate various scenarios:
    - Success responses
    - API errors (400, 401, 429, 500)
    - Network timeouts
    - Validation errors
    """
    
    def __init__(self, fail_mode: Optional[str] = None):
        """
        Initialize mock API.
        
        Args:
            fail_mode: 'auth_error', 'rate_limit', 'validation_error', 
                      'server_error', 'timeout', or None for success
        """
        self.fail_mode = fail_mode
        self.call_history: List[Dict[str, Any]] = []
        self.call_count = 0
    
    def _record_call(self, function_name: str, **kwargs):
        """Record API calls for verification in tests."""
        self.call_count += 1
        self.call_history.append({
            'function': function_name,
            'args': kwargs,
            'call_number': self.call_count
        })
    
    def _create_error_response(self):
        """Create appropriate error response based on fail_mode."""
        if self.fail_mode == 'auth_error':
            error_obj = type('ErrorResponse', (), {})()
            error_obj.status_code = 401
            error_obj.data = ProlificAPIFixtures.authentication_error_response()
            return error_obj
        elif self.fail_mode == 'rate_limit':
            error_obj = type('ErrorResponse', (), {})()
            error_obj.status_code = 429
            error_obj.data = ProlificAPIFixtures.rate_limit_error_response()
            return error_obj
        elif self.fail_mode == 'validation_error':
            error_obj = type('ErrorResponse', (), {})()
            error_obj.status_code = 400
            error_obj.data = ProlificAPIFixtures.validation_error_response()
            return error_obj
        elif self.fail_mode == 'server_error':
            error_obj = type('ErrorResponse', (), {})()
            error_obj.status_code = 500
            error_obj.data = ProlificAPIFixtures.error_response(500, "Internal Server Error")
            return error_obj
        elif self.fail_mode == 'timeout':
            raise TimeoutError("Request timed out")
        
        # Default success response
        return None
    
    # Mock implementations matching outgoing_api.py functions
    
    def list_studies(self, pid: Optional[str] = None):
        """Mock list_studies function."""
        self._record_call('list_studies', project_id=pid)
        
        error_response = self._create_error_response()
        if error_response:
            return error_response
        
        response_data = ProlificAPIFixtures.list_studies_response()
        return response_data.get('results', [])
    
    def list_active_studies(self, state: str = "ACTIVE") -> List[Dict]:
        """Mock list_active_studies function."""
        self._record_call('list_active_studies', state=state)
        
        if self.fail_mode:
            return []  # Function returns empty list on error
        
        response_data = ProlificAPIFixtures.list_studies_response()
        return response_data.get('results', [])
    
    def study_detail(self, id: str) -> Union[Dict, MockProlificResponse]:
        """Mock study_detail function."""
        self._record_call('study_detail', id=id)
        
        error_response = self._create_error_response()
        if error_response:
            return error_response
        
        return ProlificAPIFixtures.study_response(study_id=id)
    
    def create_draft(self, study_details: Dict) -> Union[Dict, MockProlificResponse]:
        """Mock create_draft function."""
        self._record_call('create_draft', study_details=study_details)
        
        error_response = self._create_error_response()
        if error_response:
            return error_response
        
        # Validate required fields like the real API
        required_fields = ['name', 'description', 'external_study_url']
        for field in required_fields:
            if field not in study_details:
                return MockProlificResponse(
                    ProlificAPIFixtures.validation_error_response(),
                    status_code=400
                )
        
        return ProlificAPIFixtures.study_response(**study_details)
    
    def update_draft(self, id: str, study_details: Dict) -> Union[Dict, MockProlificResponse]:
        """Mock update_draft function."""
        self._record_call('update_draft', id=id, study_details=study_details)
        
        error_response = self._create_error_response()
        if error_response:
            return error_response
        
        return ProlificAPIFixtures.study_response(study_id=id, **study_details)
    
    def create_part_group(self, pid: str, name: str):
        """Mock create_part_group function."""
        self._record_call('create_part_group', project_id=pid, name=name)
        
        error_response = self._create_error_response()
        if error_response:
            return error_response
        
        return ProlificAPIFixtures.participant_group_response(name=name)
    
    def update_part_group(self, pid: str, name: str) -> Union[Dict, MockProlificResponse]:
        """Mock update_part_group function."""
        self._record_call('update_part_group', group_id=pid, name=name)
        
        error_response = self._create_error_response()
        if error_response:
            return error_response
        
        return ProlificAPIFixtures.participant_group_response(group_id=pid, name=name)
    
    def add_to_part_group(self, group_id: str, part_ids: List[str]) -> Union[bool, MockProlificResponse]:
        """Mock add_to_part_group function."""
        self._record_call('add_to_part_group', group_id=group_id, participant_ids=part_ids)
        
        error_response = self._create_error_response()
        if error_response:
            return error_response
        
        return True  # Function returns True on 204 success
    
    def remove_from_part_group(self, group_id: str, part_ids: List[str]) -> Union[bool, MockProlificResponse]:
        """Mock remove_from_part_group function."""
        self._record_call('remove_from_part_group', group_id=group_id, participant_ids=part_ids)
        
        error_response = self._create_error_response()
        if error_response:
            return error_response
        
        return True  # Function returns True on 204 success
    
    def get_participants(self, gid: str) -> Union[Dict, MockProlificResponse]:
        """Mock get_participants function."""
        self._record_call('get_participants', group_id=gid)
        
        error_response = self._create_error_response()
        if error_response:
            return error_response
        
        return ProlificAPIFixtures.participant_group_participants_response(group_id=gid)
    
    def publish(self, sid: str) -> Union[Dict, MockProlificResponse]:
        """Mock publish function."""
        self._record_call('publish', study_id=sid)
        
        error_response = self._create_error_response()
        if error_response:
            return error_response
        
        return {"status": "PUBLISHING", "message": "Study is being published"}
    
    def list_submissions(self, sid: str) -> Union[List[Dict], MockProlificResponse]:
        """Mock list_submissions function."""
        self._record_call('list_submissions', study_id=sid)
        
        error_response = self._create_error_response()
        if error_response:
            return error_response
        
        response_data = ProlificAPIFixtures.list_submissions_response(study_id=sid)
        return response_data.get('results', [])
    
    def get_submission(self, session_id: str):
        """Mock get_submission function."""
        self._record_call('get_submission', session_id=session_id)
        
        error_response = self._create_error_response()
        if error_response:
            return error_response
        
        # Create an object with status attribute for compatibility
        response_data = ProlificAPIFixtures.submission_response(submission_id=session_id)
        response_obj = type('SubmissionResponse', (), response_data)()
        return response_obj
    
    def send_message(self, participant_id: str, study_id: str, message: str) -> Union[Dict, MockProlificResponse]:
        """Mock send_message function."""
        self._record_call('send_message', participant_id=participant_id, study_id=study_id, message=message)
        
        error_response = self._create_error_response()
        if error_response:
            return error_response
        
        return ProlificAPIFixtures.send_message_response()


class ProlificAPIMock:
    """
    Context manager for mocking Prolific API calls.
    
    Usage:
        with ProlificAPIMock() as mock_api:
            # Your code that calls Prolific API
            result = api.create_draft(study_data)
            
            # Verify calls
            assert mock_api.call_count == 1
            assert 'create_draft' in [call['function'] for call in mock_api.call_history]
    """
    
    def __init__(self, fail_mode: Optional[str] = None):
        self.fail_mode = fail_mode
        self.mock_api = None
        self.patches = []
    
    def __enter__(self) -> MockProlificAPI:
        """Start mocking Prolific API functions."""
        self.mock_api = MockProlificAPI(self.fail_mode)
        
        # Patch all the functions in outgoing_api.py
        from prolific import outgoing_api
        
        functions_to_mock = [
            'list_studies', 'list_active_studies', 'study_detail',
            'create_draft', 'update_draft', 'create_part_group',
            'update_part_group', 'add_to_part_group', 'remove_from_part_group',
            'get_participants', 'publish', 'list_submissions',
            'get_submission', 'send_message'
        ]
        
        for func_name in functions_to_mock:
            if hasattr(outgoing_api, func_name):
                mock_func = getattr(self.mock_api, func_name)
                patcher = patch.object(outgoing_api, func_name, side_effect=mock_func)
                self.patches.append(patcher)
                patcher.start()
        
        return self.mock_api
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop mocking and clean up."""
        for patcher in self.patches:
            patcher.stop()
        self.patches.clear()


def mock_prolific_api(fail_mode: Optional[str] = None):
    """
    Decorator for mocking Prolific API in test methods.
    
    Usage:
        @mock_prolific_api()
        def test_study_creation(self):
            # API calls will be mocked
            
        @mock_prolific_api(fail_mode='auth_error')
        def test_auth_failure(self):
            # API calls will return 401 errors
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with ProlificAPIMock(fail_mode) as mock_api:
                # Inject mock_api as a parameter if the test function expects it
                if 'mock_api' in func.__code__.co_varnames:
                    kwargs['mock_api'] = mock_api
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Convenience functions for common test scenarios

def create_mock_study_response(study_id: str = "test_study_123", **overrides):
    """Create a mock study response for testing."""
    return ProlificAPIFixtures.study_response(study_id=study_id, **overrides)

def create_mock_submission_response(submission_id: str = "test_sub_123", **overrides):
    """Create a mock submission response for testing."""
    return ProlificAPIFixtures.submission_response(submission_id=submission_id, **overrides)

def assert_api_called(mock_api: MockProlificAPI, function_name: str, expected_calls: int = 1):
    """Assert that a specific API function was called the expected number of times."""
    actual_calls = len([
        call for call in mock_api.call_history 
        if call['function'] == function_name
    ])
    assert actual_calls == expected_calls, f"Expected {expected_calls} calls to {function_name}, got {actual_calls}"

def get_api_call_args(mock_api: MockProlificAPI, function_name: str, call_index: int = 0) -> Dict[str, Any]:
    """Get the arguments from a specific API call."""
    matching_calls = [
        call for call in mock_api.call_history 
        if call['function'] == function_name
    ]
    if call_index >= len(matching_calls):
        raise IndexError(f"Call index {call_index} out of range for {function_name}")
    return matching_calls[call_index]['args']