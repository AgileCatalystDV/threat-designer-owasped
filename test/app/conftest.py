"""
Shared pytest fixtures for backend/app tests.

This module provides common fixtures for testing backend/app components:
- Mock AWS service clients (DynamoDB, S3)
- Test data fixtures (threat models, users, locks, sharing records)
- Environment variable mocking
- Time mocking for consistent timestamps
"""

import sys
import os
from pathlib import Path
from decimal import Decimal
from unittest.mock import Mock, MagicMock
import pytest

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))


# ============================================================================
# AWS Service Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_dynamodb_resource():
    """Mock boto3 DynamoDB resource."""
    mock_resource = Mock()
    return mock_resource


@pytest.fixture
def mock_dynamodb_table(mock_dynamodb_resource):
    """
    Mock DynamoDB table with common operations.

    Returns a mock table that can be configured for specific test scenarios.
    """
    mock_table = Mock()

    # Default responses for common operations
    mock_table.get_item.return_value = {"Item": {}}
    mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    mock_table.update_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    mock_table.delete_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    mock_table.query.return_value = {"Items": [], "Count": 0}
    mock_table.scan.return_value = {"Items": [], "Count": 0}

    # Configure the resource to return this table
    mock_dynamodb_resource.Table.return_value = mock_table

    return mock_table


@pytest.fixture
def mock_s3_client():
    """Mock boto3 S3 client."""
    mock_client = Mock()

    # Default responses
    mock_client.delete_object.return_value = {
        "ResponseMetadata": {"HTTPStatusCode": 204}
    }
    mock_client.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    mock_client.get_object.return_value = {
        "Body": Mock(read=Mock(return_value=b'{"test": "data"}')),
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }
    mock_client.generate_presigned_url.return_value = (
        "https://s3.example.com/presigned-url"
    )

    return mock_client



# ============================================================================
# Environment Variable Fixtures
# ============================================================================


@pytest.fixture
def mock_environment():
    """
    Mock environment variables for backend/app.

    Returns a dict of environment variables that can be used with patch.dict.
    """
    return {
        "JOB_STATUS_TABLE": "test-status-table",
        "AGENT_STATE_TABLE": "test-agent-table",
        "LOCKS_TABLE": "test-locks-table",
        "SHARING_TABLE": "test-sharing-table",
        "ARCHITECTURE_BUCKET": "test-bucket",
        "THREAT_DESIGNER_URL": "http://threat-designer:8080",
        "DYNAMODB_ENDPOINT": "http://localhost:8001",
        "S3_ENDPOINT": "http://localhost:9000",
        "LOCAL_USER": "local-user",
    }


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_threat_model():
    """Sample threat model data structure."""
    return {
        "job_id": "test-job-123",
        "owner": "user-123",
        "title": "Test Threat Model",
        "s3_location": "test-key.json",
        "description": "Test description for threat model",
        "assumptions": ["assumption1", "assumption2"],
        "threat_list": [],
        "assets": [],
        "system_architecture": {},
        "last_modified_at": "2024-01-01T00:00:00Z",
        "last_modified_by": "user-123",
        "content_hash": "abc123def456",
        "is_shared": False,
        "version": Decimal("1"),
    }


@pytest.fixture
def sample_user():
    """Sample user data structure."""
    return {
        "user_id": "user-123",
        "username": "testuser",
        "email": "test@example.com",
        "sub": "user-123",
    }


@pytest.fixture
def sample_collaborator():
    """Sample collaborator user data."""
    return {
        "user_id": "user-456",
        "username": "collaborator",
        "email": "collaborator@example.com",
        "sub": "user-456",
    }


@pytest.fixture
def sample_lock():
    """Sample lock data structure."""
    return {
        "threat_model_id": "test-job-123",
        "user_id": "user-123",
        "lock_token": "token-123",
        "lock_timestamp": Decimal("1704067200"),  # 2024-01-01 00:00:00
        "acquired_at": "2024-01-01T00:00:00Z",
        "ttl": Decimal("1704070800"),  # 1 hour later
    }


@pytest.fixture
def sample_sharing_record():
    """Sample sharing record data structure."""
    return {
        "threat_model_id": "test-job-123",
        "user_id": "user-456",
        "access_level": "EDIT",
        "shared_by": "user-123",
        "shared_at": "2024-01-01T00:00:00Z",
        "owner": "user-123",
    }


@pytest.fixture
def sample_job_status():
    """Sample job status data structure."""
    return {
        "job_id": "test-job-123",
        "status": "COMPLETED",
        "execution_owner": "user-123",
        "retry_count": Decimal("0"),
        "detail": "Processing complete",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:05:00Z",
    }


# ============================================================================
# Time Mocking Fixtures
# ============================================================================


@pytest.fixture
def mock_time():
    """
    Mock time.time() for consistent timestamps.

    Returns a fixed timestamp: 1704067200 (2024-01-01 00:00:00 UTC)
    """
    return 1704067200.0


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent datetime operations."""
    from datetime import datetime, timezone

    return datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


