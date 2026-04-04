"""
Integration tests for store.py against a real DynamoDB Local container.

Prerequisites:
  docker compose up dynamodb-local

Run with:
  DYNAMODB_ENDPOINT=http://localhost:8000 pytest tests/integration/test_store.py -v
"""
import os
import uuid

import pytest

from awscope.models import ClaudeBatch, PipelineRun

DYNAMO_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT")


def _skip_if_no_dynamo():
    if not DYNAMO_ENDPOINT:
        pytest.skip("DYNAMODB_ENDPOINT not set — skipping DynamoDB integration tests")


@pytest.fixture(autouse=True)
def require_dynamodb():
    _skip_if_no_dynamo()


def _make_run(accounts=None):
    return PipelineRun(
        run_id=str(uuid.uuid4()),
        scanned_at="2026-04-04T10:00:00Z",
        accounts=accounts or ["personal"],
        total_resources=5,
        total_groups=2,
        claude_batches=[
            ClaudeBatch(
                batch_number=1,
                prompt_sent='[{"resource_id":"i-123","name":"hagrid-api"}]',
                raw_response='[{"resource_id":"i-123","group_name":"hagrid"}]',
                parsed=True,
                resource_count=1,
            )
        ],
        duration_seconds=3.5,
    )


def test_write_pipeline_run():
    from awscope.store import write_pipeline_run
    run = _make_run()
    # Should not raise
    write_pipeline_run(run)


def test_write_and_list_pipeline_runs():
    from awscope.store import list_pipeline_runs, write_pipeline_run
    run = _make_run(accounts=["integration-test"])
    write_pipeline_run(run)

    runs = list_pipeline_runs()
    # At least the run we just wrote is present
    run_ids = [r["run_id"] for r in runs]
    assert run["run_id"] in run_ids or any(r["accounts"] == ["integration-test"] for r in runs)


def test_write_multiple_runs():
    from awscope.store import write_pipeline_run
    runs = [_make_run() for _ in range(3)]
    for r in runs:
        write_pipeline_run(r)
    # No exception = success


def test_write_run_with_multiple_batches():
    from awscope.store import write_pipeline_run
    run = PipelineRun(
        run_id=str(uuid.uuid4()),
        scanned_at="2026-04-04T10:00:00Z",
        accounts=["personal"],
        total_resources=400,
        total_groups=5,
        claude_batches=[
            ClaudeBatch(
                batch_number=i,
                prompt_sent=f'[batch {i}]',
                raw_response=f'[response {i}]',
                parsed=False,
                resource_count=200,
            )
            for i in range(1, 3)
        ],
        duration_seconds=12.0,
    )
    write_pipeline_run(run)  # no exception
