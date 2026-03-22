"""
Boto3 client factory with local infrastructure support.

When DYNAMODB_ENDPOINT or S3_ENDPOINT environment variables are set,
clients connect to local services (DynamoDB Local / MinIO) instead of AWS.
This allows drop-in replacement without changing business logic.
"""

import os
import boto3
from constants import (
    DEFAULT_REGION,
    ENV_AWS_REGION,
    ENV_DYNAMODB_ENDPOINT,
    ENV_S3_ENDPOINT,
    ENV_S3_ACCESS_KEY,
    ENV_S3_SECRET_KEY,
)

REGION = os.environ.get(ENV_AWS_REGION, DEFAULT_REGION)
_DYNAMODB_ENDPOINT = os.environ.get(ENV_DYNAMODB_ENDPOINT)
_S3_ENDPOINT = os.environ.get(ENV_S3_ENDPOINT)
_S3_ACCESS_KEY = os.environ.get(ENV_S3_ACCESS_KEY)
_S3_SECRET_KEY = os.environ.get(ENV_S3_SECRET_KEY)


def get_dynamodb_resource():
    """Return a boto3 DynamoDB resource, using local endpoint when configured."""
    kwargs = {"region_name": REGION}
    if _DYNAMODB_ENDPOINT:
        kwargs["endpoint_url"] = _DYNAMODB_ENDPOINT
        kwargs.setdefault("aws_access_key_id", "local")
        kwargs.setdefault("aws_secret_access_key", "local")
    return boto3.resource("dynamodb", **kwargs)


def get_s3_client():
    """Return a boto3 S3 client, using MinIO endpoint when configured."""
    kwargs = {"region_name": REGION}
    if _S3_ENDPOINT:
        kwargs["endpoint_url"] = _S3_ENDPOINT
        kwargs["aws_access_key_id"] = _S3_ACCESS_KEY or "minioadmin"
        kwargs["aws_secret_access_key"] = _S3_SECRET_KEY or "minioadmin"
    return boto3.client("s3", **kwargs)
