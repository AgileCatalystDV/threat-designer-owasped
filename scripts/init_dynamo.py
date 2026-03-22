"""
DynamoDB Local table initialisation script.

Creates all 6 tables required by threat-designer-owasped, including GSIs and TTL.
Idempotent: skips tables that already exist (ResourceInUseException is swallowed).

Reads table names and endpoint from environment variables so the same script
works for both local Docker (DYNAMODB_ENDPOINT=http://dynamodb-local:8000 — container-poort)
and direct execution against a real AWS account.

Usage:
    python scripts/init_dynamo.py

Docker:
    Image gebouwd via `scripts/Dockerfile.dynamodb-init` (boto3 in image; geen pip bij elke run).

Environment variables:
    DYNAMODB_ENDPOINT   — local DynamoDB endpoint (default: http://localhost:8001)
    AWS_REGION          — region (default: us-east-1)
    AGENT_STATE_TABLE   — default: threat-designer-agent-state
    JOB_STATUS_TABLE    — default: threat-designer-job-status
    AGENT_TRAIL_TABLE   — default: threat-designer-agent-trail
    ATTACK_TREE_TABLE   — default: threat-designer-attack-trees
    LOCK_TABLE          — default: threat-designer-locks
    SHARING_TABLE       — default: threat-designer-sharing
"""

import os
import sys
import time
import boto3
from botocore.exceptions import ClientError

ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT", "http://localhost:8001")
REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))

TABLE_AGENT_STATE = os.environ.get("AGENT_STATE_TABLE", "threat-designer-agent-state")
TABLE_JOB_STATUS = os.environ.get("JOB_STATUS_TABLE", "threat-designer-job-status")
TABLE_AGENT_TRAIL = os.environ.get("AGENT_TRAIL_TABLE", "threat-designer-agent-trail")
TABLE_ATTACK_TREE = os.environ.get("ATTACK_TREE_TABLE", "threat-designer-attack-trees")
TABLE_LOCK = os.environ.get("LOCK_TABLE", "threat-designer-locks")
TABLE_SHARING = os.environ.get("SHARING_TABLE", "threat-designer-sharing")
TABLE_SENTRY_SESSIONS = os.environ.get("SESSION_TABLE", "sentry-sessions-table")


TABLE_DEFINITIONS = [
    # ── threat-designer-agent-state ──────────────────────────────────────────
    # PK: job_id | GSI: owner-job-index (owner, job_id)
    {
        "TableName": TABLE_AGENT_STATE,
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [
            {"AttributeName": "job_id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "job_id", "AttributeType": "S"},
            {"AttributeName": "owner", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "owner-job-index",
                "KeySchema": [
                    {"AttributeName": "owner", "KeyType": "HASH"},
                    {"AttributeName": "job_id", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    },
    # ── threat-designer-job-status ───────────────────────────────────────────
    # PK: id
    {
        "TableName": TABLE_JOB_STATUS,
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "id", "AttributeType": "S"},
        ],
    },
    # ── threat-designer-agent-trail ──────────────────────────────────────────
    # PK: id
    {
        "TableName": TABLE_AGENT_TRAIL,
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "id", "AttributeType": "S"},
        ],
    },
    # ── threat-designer-attack-trees ─────────────────────────────────────────
    # PK: attack_tree_id | GSI: threat_model_id-index
    {
        "TableName": TABLE_ATTACK_TREE,
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [
            {"AttributeName": "attack_tree_id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "attack_tree_id", "AttributeType": "S"},
            {"AttributeName": "threat_model_id", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "threat_model_id-index",
                "KeySchema": [
                    {"AttributeName": "threat_model_id", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    },
    # ── threat-designer-locks ────────────────────────────────────────────────
    # PK: threat_model_id | TTL: ttl
    {
        "TableName": TABLE_LOCK,
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [
            {"AttributeName": "threat_model_id", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "threat_model_id", "AttributeType": "S"},
        ],
    },
    # ── sentry-sessions-table ────────────────────────────────────────────────
    # PK: session_header | Maps composite session key → LangGraph thread_id
    {
        "TableName": TABLE_SENTRY_SESSIONS,
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [
            {"AttributeName": "session_header", "KeyType": "HASH"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "session_header", "AttributeType": "S"},
        ],
    },
    # ── threat-designer-sharing ──────────────────────────────────────────────
    # PK: threat_model_id, SK: user_id | GSIs: owner-index, user-index
    {
        "TableName": TABLE_SHARING,
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [
            {"AttributeName": "threat_model_id", "KeyType": "HASH"},
            {"AttributeName": "user_id", "KeyType": "RANGE"},
        ],
        "AttributeDefinitions": [
            {"AttributeName": "threat_model_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "owner", "AttributeType": "S"},
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "owner-index",
                "KeySchema": [
                    {"AttributeName": "owner", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "user-index",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
    },
]


def wait_for_dynamodb(client: boto3.client, retries: int = 20, delay: float = 2.0) -> None:
    """Poll until DynamoDB Local is reachable."""
    for attempt in range(1, retries + 1):
        try:
            client.list_tables()
            print(f"[init_dynamo] DynamoDB Local reachable at {ENDPOINT}")
            return
        except Exception as exc:
            print(f"[init_dynamo] Waiting for DynamoDB Local... ({attempt}/{retries}): {exc}")
            time.sleep(delay)
    print("[init_dynamo] ERROR: DynamoDB Local not reachable after retries. Exiting.", file=sys.stderr)
    sys.exit(1)


def create_table(client: boto3.client, definition: dict) -> None:
    table_name = definition["TableName"]
    try:
        client.create_table(**definition)
        print(f"[init_dynamo] Created table: {table_name}")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ResourceInUseException":
            print(f"[init_dynamo] Table already exists (skipped): {table_name}")
        else:
            raise


def enable_ttl(client: boto3.client, table_name: str, attribute: str) -> None:
    try:
        client.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={"Enabled": True, "AttributeName": attribute},
        )
        print(f"[init_dynamo] TTL enabled on {table_name}.{attribute}")
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("ValidationException", "ResourceInUseException"):
            print(f"[init_dynamo] TTL already set on {table_name} (skipped)")
        else:
            raise


def main() -> None:
    print(f"[init_dynamo] Connecting to DynamoDB at {ENDPOINT} (region={REGION})")

    client = boto3.client(
        "dynamodb",
        endpoint_url=ENDPOINT,
        region_name=REGION,
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )

    wait_for_dynamodb(client)

    for definition in TABLE_DEFINITIONS:
        create_table(client, definition)

    # TTL is a separate API call (not supported in create_table for DynamoDB Local)
    enable_ttl(client, TABLE_LOCK, "ttl")

    print("[init_dynamo] All tables initialised successfully.")


if __name__ == "__main__":
    main()
