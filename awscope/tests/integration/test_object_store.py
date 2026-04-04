"""
Integration tests for object_store.py against a real MinIO container.

Prerequisites:
  docker compose up minio

Run with:
  MINIO_ENDPOINT=http://localhost:9000 pytest tests/integration/test_object_store.py -v
"""
import os
from io import BytesIO

import pytest

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")


def _skip_if_no_minio():
    if not MINIO_ENDPOINT:
        pytest.skip("MINIO_ENDPOINT not set — skipping MinIO integration tests")


@pytest.fixture(autouse=True)
def require_minio():
    _skip_if_no_minio()


@pytest.fixture(autouse=True)
def set_minio_env(monkeypatch):
    monkeypatch.setenv("MINIO_ENDPOINT", MINIO_ENDPOINT)
    monkeypatch.setenv("MINIO_ACCESS_KEY", os.getenv("MINIO_ACCESS_KEY", "minioadmin"))
    monkeypatch.setenv("MINIO_SECRET_KEY", os.getenv("MINIO_SECRET_KEY", "minioadmin"))
    monkeypatch.setenv("MINIO_BUCKET", "awscope-test-bucket")


def _excel_bytes() -> BytesIO:
    buf = BytesIO(b"PK fake xlsx content")
    buf.seek(0)
    return buf


def test_upload_creates_object():
    from awscope.object_store import upload_export
    buf = _excel_bytes()
    url = upload_export(buf, "exports/2026-04-04/test_upload.xlsx")
    assert url is not None
    assert "test_upload.xlsx" in url


def test_upload_returns_none_when_disabled(monkeypatch):
    monkeypatch.delenv("MINIO_ENDPOINT")
    from awscope.object_store import upload_export
    buf = _excel_bytes()
    url = upload_export(buf, "exports/2026-04-04/should_not_upload.xlsx")
    assert url is None


def test_upload_multiple_objects():
    from awscope.object_store import upload_export
    keys = ["exports/2026-04-04/file1.xlsx", "exports/2026-04-04/file2.xlsx"]
    for key in keys:
        url = upload_export(_excel_bytes(), key)
        assert url is not None


def test_bucket_auto_created():
    import boto3
    from botocore.exceptions import ClientError
    from awscope.object_store import upload_export

    # Use a unique bucket name to test auto-creation
    import os
    os.environ["MINIO_BUCKET"] = "awscope-autocreate-test"

    client = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    )
    # Delete bucket if exists (best effort)
    try:
        client.delete_bucket(Bucket="awscope-autocreate-test")
    except ClientError:
        pass

    buf = _excel_bytes()
    url = upload_export(buf, "exports/test.xlsx")
    assert url is not None
