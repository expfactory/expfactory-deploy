"""
Mock API response fixtures for Prolific API testing.

Based on the official Prolific OpenAPI specification to ensure accuracy
with the actual API responses.
"""

import datetime
from uuid import uuid4
from typing import Dict, List, Any, Optional


class ProlificAPIFixtures:
    """
    Accurate mock responses based on Prolific's OpenAPI specification.
    
    All schemas match the official API documentation at docs/prolific_api.yaml
    """
    
    @staticmethod
    def study_response(
        study_id: Optional[str] = None,
        status: str = "UNPUBLISHED",
        **overrides
    ) -> Dict[str, Any]:
        """
        Mock Study schema response based on OpenAPI spec.
        
        Status options: UNPUBLISHED, SCHEDULED, PUBLISHING, ACTIVE, 
                       AWAITING REVIEW, PAUSED, COMPLETED
        """
        study_id = study_id or f"study_{uuid4().hex[:8]}"
        base_response = {
            "id": study_id,
            "name": "Cognitive Assessment Study",
            "internal_name": "internal_cog_study_v1",
            "description": "A study investigating cognitive processes in decision making.",
            "external_study_url": f"https://deploy.expfactory.org/prolific/serve/123/consent?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}",
            "prolific_id_option": "url_parameters",
            "completion_codes": [
                {
                    "code": "test_completion_123",
                    "code_type": "COMPLETED",
                    "actions": [{"action": "AUTOMATICALLY_APPROVE"}]
                }
            ],
            "estimated_completion_time": 30,
            "reward": 500,  # In pence (5.00 GBP)
            "total_available_places": 100,
            "status": status,
            "device_compatibility": ["desktop"],
            "filters": [],
            "project": f"proj_{uuid4().hex[:8]}",
            "workspace": f"ws_{uuid4().hex[:8]}",
            "created_at": datetime.datetime.now().isoformat() + "Z",
            "updated_at": datetime.datetime.now().isoformat() + "Z",
            "publish_at": None,
            "maximum_allowed_time": 3600,  # seconds
            "naivety_distribution_rate": 0.0,
            "is_pilot": False
        }
        base_response.update(overrides)
        return base_response
    
    @staticmethod
    def submission_response(
        submission_id: Optional[str] = None,
        study_id: Optional[str] = None,
        status: str = "APPROVED",
        **overrides
    ) -> Dict[str, Any]:
        """
        Mock Submission schema response.
        
        Status options: APPROVED, AWAITING REVIEW, REJECTED, RETURNED, TIMED_OUT
        """
        submission_id = submission_id or f"submission_{uuid4().hex[:8]}"
        study_id = study_id or f"study_{uuid4().hex[:8]}"
        
        base_response = {
            "id": submission_id,
            "started_at": (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat() + "Z",
            "status": status,
            "study_id": study_id,
            "completed_at": (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat() + "Z",
            "participant": f"participant_{uuid4().hex[:8]}",
            "time_taken": 3600,  # seconds
            "bonus_payments": [],
            "fee": 500,  # In pence
            "is_complete": True
        }
        base_response.update(overrides)
        return base_response
    
    @staticmethod
    def participant_group_response(
        group_id: Optional[str] = None,
        name: str = "Test Participant Group",
        **overrides
    ) -> Dict[str, Any]:
        """Mock ParticipantGroup schema response."""
        group_id = group_id or f"pg_{uuid4().hex[:8]}"
        
        base_response = {
            "id": group_id,
            "name": name,
            "project_id": None,  # Can be null according to spec
            "workspace_id": f"ws_{uuid4().hex[:8]}",
            "created_at": datetime.datetime.now().isoformat() + "Z",
            "updated_at": datetime.datetime.now().isoformat() + "Z"
        }
        base_response.update(overrides)
        return base_response
    
    @staticmethod
    def user_me_response(**overrides) -> Dict[str, Any]:
        """Mock /api/v1/users/me/ response for token validation."""
        base_response = {
            "id": f"user_{uuid4().hex[:8]}",
            "email": "researcher@example.com",
            "name": "Test Researcher",
            "institution": "Test University",
            "is_institution_admin": False,
            "balance": {"available_balance": 10000},  # In pence
            "country": "GB"
        }
        base_response.update(overrides)
        return base_response
    
    @staticmethod
    def create_study_request(
        name: str = "Test Study",
        description: str = "Test study description",
        external_study_url: str = "https://example.com/study",
        **overrides
    ) -> Dict[str, Any]:
        """Mock CreateStudy request payload."""
        base_request = {
            "name": name,
            "description": description,
            "external_study_url": external_study_url,
            "prolific_id_option": "url_parameters",
            "completion_codes": [
                {
                    "code": f"completion_{uuid4().hex[:8]}",
                    "code_type": "COMPLETED",
                    "actions": [{"action": "AUTOMATICALLY_APPROVE"}]
                }
            ],
            "estimated_completion_time": 30,
            "reward": 500,
            "total_available_places": 100,
            "device_compatibility": ["desktop"]
        }
        base_request.update(overrides)
        return base_request
    
    @staticmethod
    def list_studies_response(count: int = 3, **overrides) -> Dict[str, Any]:
        """Mock paginated studies list response."""
        base_response = {
            "results": [
                ProlificAPIFixtures.study_response(study_id=f"study_{i}")
                for i in range(count)
            ],
            "count": count,
            "next": None,
            "previous": None
        }
        base_response.update(overrides)
        return base_response
    
    @staticmethod
    def list_submissions_response(
        study_id: Optional[str] = None,
        count: int = 10,
        **overrides
    ) -> Dict[str, Any]:
        """Mock paginated submissions list response."""
        study_id = study_id or f"study_{uuid4().hex[:8]}"
        
        base_response = {
            "results": [
                ProlificAPIFixtures.submission_response(
                    study_id=study_id,
                    submission_id=f"submission_{i}"
                )
                for i in range(count)
            ],
            "count": count,
            "next": None,
            "previous": None
        }
        base_response.update(overrides)
        return base_response
    
    @staticmethod
    def participant_group_participants_response(
        group_id: Optional[str] = None,
        count: int = 5,
        **overrides
    ) -> Dict[str, Any]:
        """Mock participant group members response."""
        group_id = group_id or f"pg_{uuid4().hex[:8]}"
        
        base_response = {
            "results": [
                {
                    "participant_id": f"participant_{uuid4().hex[:8]}",
                    "status": "ACTIVE",
                    "added_at": datetime.datetime.now().isoformat() + "Z"
                }
                for _ in range(count)
            ],
            "count": count
        }
        base_response.update(overrides)
        return base_response
    
    @staticmethod
    def error_response(
        status_code: int = 400,
        detail: str = "Bad Request",
        errors: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Mock API error response."""
        response = {
            "detail": detail
        }
        if errors:
            response["errors"] = errors
        return response
    
    @staticmethod
    def validation_error_response() -> Dict[str, Any]:
        """Mock validation error for study creation."""
        return ProlificAPIFixtures.error_response(
            status_code=400,
            detail="Validation failed",
            errors={
                "external_study_url": ["This field is required."],
                "reward": ["Ensure this value is greater than or equal to 100."]
            }
        )
    
    @staticmethod
    def rate_limit_error_response() -> Dict[str, Any]:
        """Mock rate limit error response."""
        return ProlificAPIFixtures.error_response(
            status_code=429,
            detail="Rate limit exceeded"
        )
    
    @staticmethod
    def authentication_error_response() -> Dict[str, Any]:
        """Mock authentication error response."""
        return ProlificAPIFixtures.error_response(
            status_code=401,
            detail="Authentication credentials were not provided."
        )
    
    @staticmethod
    def send_message_request(
        participant_id: str,
        body: str,
        study_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mock send message request payload."""
        request = {
            "recipient_id": participant_id,
            "body": body
        }
        if study_id:
            request["study_id"] = study_id
        return request
    
    @staticmethod
    def send_message_response(**overrides) -> Dict[str, Any]:
        """Mock send message success response."""
        base_response = {
            "id": f"message_{uuid4().hex[:8]}",
            "status": "SENT",
            "sent_at": datetime.datetime.now().isoformat() + "Z"
        }
        base_response.update(overrides)
        return base_response
    
    @staticmethod
    def publish_study_request() -> Dict[str, Any]:
        """Mock publish study request payload."""
        return {"action": "PUBLISH"}
    
    @staticmethod
    def participant_id_list(participant_ids: List[str]) -> Dict[str, Any]:
        """Mock ParticipantIDList for adding/removing from groups."""
        return {"participant_ids": participant_ids}


class MockProlificResponse:
    """
    Mock HTTP response object that simulates the structure
    expected by the existing outgoing_api.py code.
    """
    
    def __init__(
        self, 
        data: Dict[str, Any], 
        status_code: int = 200,
        headers: Optional[Dict] = None
    ):
        self.data = data
        self.status_code = status_code
        self.headers = headers or {}
        self.parsed = MockParsedResponse(data)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.data


class MockParsedResponse:
    """Mock parsed response object."""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        return self.data


# Test constants based on the current test file
TEST_PROJECT_ID = "65d65f5231592c82a95db12c"
TEST_WORKSPACE_ID = "6410d74c29d97f193806ca67"
TEST_STUDY_ID = "test_study_12345"
TEST_PARTICIPANT_GROUP_ID = "test_pg_67890"
TEST_PARTICIPANT_ID = "test_participant_abcde"
TEST_SUBMISSION_ID = "test_submission_fghij"