from awscope.models import AwsResource, ClaudeBatch, PipelineRun, ResourceGroup, ScanResult


def _resource(resource_id="i-123", name="test", resource_type="ec2:instance"):
    return AwsResource(
        resource_id=resource_id, name=name, resource_type=resource_type,
        arn="arn:aws:ec2:us-east-1:123456789012:instance/i-123",
        region="us-east-1", account_alias="personal", account_id="123456789012",
        status="running", tags={"Env": "prod"}, raw={},
    )


def test_aws_resource_fields():
    r = _resource()
    assert r.resource_id == "i-123"
    assert r.name == "test"
    assert r.tags == {"Env": "prod"}


def test_resource_group_defaults_empty_resources():
    g = ResourceGroup(group_name="hagrid")
    assert g.resources == []


def test_scan_result_fields():
    r = _resource()
    g = ResourceGroup(group_name="hagrid", resources=[r])
    result = ScanResult(
        scanned_at="2026-04-04T10:00:00Z",
        accounts=["personal"],
        resources=[r],
        groups=[g],
    )
    assert len(result.groups) == 1
    assert result.groups[0].group_name == "hagrid"


def test_pipeline_run_defaults():
    run = PipelineRun(
        run_id="abc-123",
        scanned_at="2026-04-04T10:00:00Z",
        accounts=["personal"],
        total_resources=5,
        total_groups=2,
    )
    assert run.claude_batches == []
    assert run.duration_seconds == 0.0


def test_claude_batch():
    batch = ClaudeBatch(
        batch_number=1,
        prompt_sent='[{"resource_id":"i-123"}]',
        raw_response='[{"resource_id":"i-123","group_name":"hagrid"}]',
        parsed=True,
        resource_count=1,
    )
    assert batch.parsed is True
