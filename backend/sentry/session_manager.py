import os
import time
import uuid
from typing import Dict, Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from utils import logger


TABLE_NAME = os.environ.get("SESSION_TABLE", "sentry-sessions-table")
DYNAMODB_ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT", "http://localhost:8001")
REGION = os.environ.get("REGION", os.environ.get("AWS_REGION", "us-east-1"))


def _get_dynamodb_resource():
    return boto3.resource(
        "dynamodb",
        endpoint_url=DYNAMODB_ENDPOINT,
        region_name=REGION,
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )


def _ensure_table_exists(dynamodb) -> None:
    """Create the sentry-sessions-table if it doesn't exist yet."""
    try:
        dynamodb.create_table(
            TableName=TABLE_NAME,
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[{"AttributeName": "session_header", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "session_header", "AttributeType": "S"}
            ],
        )
        logger.debug(f"[session_manager] Created DynamoDB table: {TABLE_NAME}")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ResourceInUseException":
            pass  # already exists
        else:
            logger.warning(f"[session_manager] Could not create table {TABLE_NAME}: {exc}")


class SessionManager:
    def __init__(self):
        self.session_cache: Dict[str, str] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.cache_ttl = 300  # 5 minutes

        self.dynamodb = _get_dynamodb_resource()
        _ensure_table_exists(self.dynamodb)
        self.table = self.dynamodb.Table(TABLE_NAME)

        self._load_cache_from_dynamodb()

    def _load_cache_from_dynamodb(self):
        try:
            current_time = time.time()
            response = self.table.scan()
            for item in response.get("Items", []):
                header = item["session_header"]
                self.session_cache[header] = item["session_id"]
                self.cache_timestamps[header] = current_time
            logger.debug(
                f"[session_manager] Loaded {len(self.session_cache)} sessions from DynamoDB"
            )
        except Exception as exc:
            logger.warning(f"[session_manager] Could not load sessions from DynamoDB: {exc}")

    def _get_session_from_dynamodb(self, session_header: str) -> Optional[str]:
        try:
            response = self.table.get_item(Key={"session_header": session_header})
            if "Item" in response:
                session_id = response["Item"]["session_id"]
                self.session_cache[session_header] = session_id
                self.cache_timestamps[session_header] = time.time()
                return session_id
        except Exception as exc:
            logger.error(f"[session_manager] Error retrieving session from DynamoDB: {exc}")
        return None

    def _save_session_to_dynamodb(self, session_header: str, session_id: str):
        try:
            self.table.put_item(
                Item={
                    "session_header": session_header,
                    "session_id": session_id,
                    "created_at": int(time.time()),
                }
            )
        except Exception as exc:
            logger.error(f"[session_manager] Error saving session to DynamoDB: {exc}")

    def _is_cache_expired(self, session_header: str) -> bool:
        if session_header not in self.cache_timestamps:
            return True
        return time.time() - self.cache_timestamps[session_header] > self.cache_ttl

    def get_or_create_session_id(self, session_header: str) -> str:
        """Return cached session ID or create a new one."""
        if session_header in self.session_cache:
            if not self._is_cache_expired(session_header):
                return self.session_cache[session_header]
            del self.session_cache[session_header]
            del self.cache_timestamps[session_header]

        session_id = self._get_session_from_dynamodb(session_header)
        if session_id:
            return session_id

        # New session — generate a UUID (no AgentCore dependency)
        session_id = str(uuid.uuid4())
        self.session_cache[session_header] = session_id
        self.cache_timestamps[session_header] = time.time()
        self._save_session_to_dynamodb(session_header, session_id)
        logger.debug(
            f"[session_manager] Created new session {session_id} for header: {session_header}"
        )
        return session_id

    def clear_cache(self):
        self.session_cache.clear()
        self.cache_timestamps.clear()

    def delete_session(self, session_header: str):
        self.clear_cache()
        try:
            self.table.delete_item(Key={"session_header": session_header})
        except Exception as exc:
            logger.error(f"[session_manager] Error deleting session from DynamoDB: {exc}")


# Global singleton
session_manager = SessionManager()
