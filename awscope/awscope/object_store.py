from __future__ import annotations

import logging
from io import BytesIO

import boto3
from botocore.exceptions import ClientError

from awscope.config import get_minio_settings

log = logging.getLogger(__name__)


def _client_and_bucket() -> tuple | None:
    settings = get_minio_settings()
    if not settings:
        return None
    client = boto3.client(
        "s3",
        endpoint_url=settings["endpoint_url"],
        aws_access_key_id=settings["aws_access_key_id"],
        aws_secret_access_key=settings["aws_secret_access_key"],
    )
    return client, settings["bucket"]


def _ensure_bucket(client, bucket: str) -> None:
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
            client.create_bucket(Bucket=bucket)
            log.info("Created MinIO bucket: %s", bucket)
        else:
            raise


def upload_export(data: BytesIO, object_key: str) -> str | None:
    result = _client_and_bucket()
    if result is None:
        return None

    client, bucket = result
    try:
        _ensure_bucket(client, bucket)
        data.seek(0)
        client.upload_fileobj(data, bucket, object_key)
        url = f"{get_minio_settings()['endpoint_url']}/{bucket}/{object_key}"
        log.info("Uploaded export to MinIO: %s", url)
        return url
    except Exception as e:
        log.warning("Failed to upload to MinIO: %s — export saved locally only", e)
        return None
