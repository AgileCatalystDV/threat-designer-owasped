"""
Pytest configuration and fixtures for route tests.

This module provides autouse fixtures that mock service functions
before the route modules are imported, ensuring proper test isolation.
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest

# Add backend/app to path for imports
backend_path = str(Path(__file__).parent.parent.parent.parent / "backend" / "app")
sys.path.insert(0, backend_path)

# Mock environment variables before importing services
os.environ["JOB_STATUS_TABLE"] = "test-status-table"
os.environ["AGENT_STATE_TABLE"] = "test-agent-table"
os.environ["AGENT_TRAIL_TABLE"] = "test-trail-table"
os.environ["THREAT_DESIGNER_URL"] = "http://threat-designer:8080"
os.environ["ARCHITECTURE_BUCKET"] = "test-bucket"
os.environ["SHARING_TABLE"] = "test-sharing-table"
os.environ["LOCKS_TABLE"] = "test-locks-table"
os.environ["DYNAMODB_ENDPOINT"] = "http://localhost:8001"
os.environ["LOCAL_USER"] = "local-user"


@pytest.fixture(scope="session", autouse=True)
def mock_boto3_session():
    """Mock boto3 at session level before any imports."""
    from unittest.mock import patch

    with patch("boto3.resource") as mock_resource, patch("boto3.client") as mock_client:
        # Mock DynamoDB resource
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_table.get_item.return_value = {"Item": {}}
        mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        mock_table.update_item.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }
        mock_table.delete_item.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }
        mock_table.query.return_value = {"Items": [], "Count": 0}
        mock_table.scan.return_value = {"Items": [], "Count": 0}
        mock_dynamodb.Table.return_value = mock_table

        # Mock S3 client
        mock_s3 = Mock()
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/presigned"
        mock_s3.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        mock_s3.delete_object.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 204}
        }

        def resource_side_effect(service_name, **kwargs):
            if service_name == "dynamodb":
                return mock_dynamodb
            return Mock()

        def client_side_effect(service_name, **kwargs):
            if service_name == "s3":
                return mock_s3
            return Mock()

        mock_resource.side_effect = resource_side_effect
        mock_client.side_effect = client_side_effect

        yield {
            "dynamodb": mock_dynamodb,
            "table": mock_table,
            "s3": mock_s3,
        }
