from __future__ import annotations

import json
import logging

import boto3
from botocore.exceptions import ClientError

from awscope.config import get_dynamodb_settings
from awscope.models import PipelineRun

log = logging.getLogger(__name__)

_TABLE = "PipelineRuns"


def _client():
    settings = get_dynamodb_settings()
    if not settings:
        return None
    return boto3.client(
        "dynamodb",
        endpoint_url=settings["endpoint_url"],
        region_name="us-east-1",
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )


def _ensure_table(client) -> None:
    try:
        client.describe_table(TableName=_TABLE)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise
        client.create_table(
            TableName=_TABLE,
            KeySchema=[
                {"AttributeName": "run_id", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "run_id", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        # Poll instead of waiter — DynamoDB Local responds immediately
        import time
        for _ in range(10):
            try:
                client.describe_table(TableName=_TABLE)
                break
            except ClientError:
                time.sleep(0.3)
        log.info("Created DynamoDB table: %s", _TABLE)


def write_pipeline_run(run: PipelineRun) -> None:
    client = _client()
    if client is None:
        return

    try:
        _ensure_table(client)

        # Metadata item
        client.put_item(
            TableName=_TABLE,
            Item={
                "run_id": {"S": run.run_id},
                "sk": {"S": "META"},
                "scanned_at": {"S": run.scanned_at},
                "accounts": {"S": json.dumps(run.accounts)},
                "total_resources": {"N": str(run.total_resources)},
                "total_groups": {"N": str(run.total_groups)},
                "duration_seconds": {"N": str(run.duration_seconds)},
            },
        )

        # Claude batch items
        for batch in run.claude_batches:
            client.put_item(
                TableName=_TABLE,
                Item={
                    "run_id": {"S": run.run_id},
                    "sk": {"S": f"BATCH#{batch.batch_number:04d}"},
                    "batch_number": {"N": str(batch.batch_number)},
                    "prompt_sent": {"S": batch.prompt_sent},
                    "raw_response": {"S": batch.raw_response},
                    "parsed": {"BOOL": batch.parsed},
                    "resource_count": {"N": str(batch.resource_count)},
                },
            )

        log.info("Stored pipeline run %s to DynamoDB Local", run.run_id)
    except Exception as e:
        log.warning("Failed to write pipeline run to DynamoDB Local: %s — continuing", e)


def list_pipeline_runs() -> list[dict]:
    client = _client()
    if client is None:
        return []
    try:
        _ensure_table(client)
        response = client.query(
            TableName=_TABLE,
            IndexName=None,
            KeyConditionExpression="sk = :meta",
            ExpressionAttributeValues={":meta": {"S": "META"}},
            FilterExpression=None,
        )
        return [_deserialize_meta(item) for item in response.get("Items", [])]
    except Exception:
        # Fallback: scan for META records
        try:
            response = client.scan(
                TableName=_TABLE,
                FilterExpression="sk = :meta",
                ExpressionAttributeValues={":meta": {"S": "META"}},
            )
            return [_deserialize_meta(item) for item in response.get("Items", [])]
        except Exception as e:
            log.warning("Failed to list pipeline runs: %s", e)
            return []


def _deserialize_meta(item: dict) -> dict:
    return {
        "run_id": item["run_id"]["S"],
        "scanned_at": item.get("scanned_at", {}).get("S", ""),
        "accounts": json.loads(item.get("accounts", {}).get("S", "[]")),
        "total_resources": int(item.get("total_resources", {}).get("N", 0)),
        "total_groups": int(item.get("total_groups", {}).get("N", 0)),
        "duration_seconds": float(item.get("duration_seconds", {}).get("N", 0)),
    }
