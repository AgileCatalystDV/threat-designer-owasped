"""
Boto3 client factory with local infrastructure support for the app layer.

When DYNAMODB_ENDPOINT or S3_ENDPOINT environment variables are set,
clients connect to local services (DynamoDB Local / MinIO) instead of AWS.
"""

import os
import boto3
from botocore.config import Config

REGION = os.environ.get("REGION", os.environ.get("AWS_REGION", "us-east-1"))
_DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")
_S3_ENDPOINT = os.environ.get("S3_ENDPOINT")
_S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
_S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")
# Public endpoint used for presigned URLs (must be browser-reachable)
_S3_PUBLIC_ENDPOINT = os.environ.get("S3_PUBLIC_ENDPOINT", _S3_ENDPOINT)


def get_dynamodb_resource():
    """Return a boto3 DynamoDB resource, using local endpoint when configured."""
    kwargs = {"region_name": REGION}
    if _DYNAMODB_ENDPOINT:
        kwargs["endpoint_url"] = _DYNAMODB_ENDPOINT
        kwargs["aws_access_key_id"] = "local"
        kwargs["aws_secret_access_key"] = "local"
    return boto3.resource("dynamodb", **kwargs)


def get_s3_client():
    """Return a boto3 S3 client, using MinIO endpoint when configured."""
    kwargs = {"region_name": REGION}
    if _S3_ENDPOINT:
        kwargs["endpoint_url"] = _S3_ENDPOINT
        kwargs["aws_access_key_id"] = _S3_ACCESS_KEY or "minioadmin"
        kwargs["aws_secret_access_key"] = _S3_SECRET_KEY or "minioadmin"
    return boto3.client("s3", **kwargs)


def get_s3_presign_client():
    """
    Return an S3 client configured for presigned URL generation.

    In local mode, uses S3_PUBLIC_ENDPOINT (default: same as S3_ENDPOINT)
    so generated URLs are reachable from the browser (localhost:9000).
    In AWS mode, uses virtual-hosted style + s3v4 signature.
    """
    if _S3_PUBLIC_ENDPOINT:
        return boto3.client(
            "s3",
            endpoint_url=_S3_PUBLIC_ENDPOINT,
            aws_access_key_id=_S3_ACCESS_KEY or "minioadmin",
            aws_secret_access_key=_S3_SECRET_KEY or "minioadmin",
            region_name=REGION,
        )
    return boto3.client(
        "s3",
        region_name=REGION,
        endpoint_url=f"https://s3.{REGION}.amazonaws.com",
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )
