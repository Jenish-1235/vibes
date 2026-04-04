import json
import tempfile
from pathlib import Path

import pytest

from awscope.cache import (
    _resource_from_dict,
    _resource_to_dict,
    _scan_result_from_dict,
    _scan_result_to_dict,
    read_cache,
    write_cache,
)
from awscope.models import AwsResource, ResourceGroup, ScanResult


def _resource():
    return AwsResource(
        resource_id="i-123", name="myapp-api", resource_type="ec2:instance",
        arn="arn:aws:ec2:us-east-1:123:instance/i-123",
        region="us-east-1", account_alias="personal", account_id="123",
        status="running", tags={"Name": "myapp-api"}, raw={"InstanceId": "i-123"},
    )


def test_resource_roundtrip():
    r = _resource()
    d = _resource_to_dict(r)
    r2 = _resource_from_dict(d)
    assert r2.resource_id == r.resource_id
    assert r2.tags == r.tags
    assert r2.raw == r.raw


def test_scan_result_roundtrip():
    r = _resource()
    g = ResourceGroup(group_name="myapp", resources=[r])
    result = ScanResult(
        scanned_at="2026-04-04T10:00:00Z",
        accounts=["personal"],
        resources=[r],
        groups=[g],
    )
    d = _scan_result_to_dict(result)
    result2 = _scan_result_from_dict(d)
    assert result2.scanned_at == result.scanned_at
    assert len(result2.groups) == 1
    assert result2.groups[0].group_name == "myapp"
    assert result2.groups[0].resources[0].resource_id == "i-123"


def test_write_and_read_cache(tmp_path, monkeypatch):
    cache_file = tmp_path / "cache.json"
    monkeypatch.setenv("AWSCOPE_CACHE_PATH", str(cache_file))

    r = _resource()
    g = ResourceGroup(group_name="myapp", resources=[r])
    result = ScanResult(
        scanned_at="2026-04-04T10:00:00Z",
        accounts=["personal"],
        resources=[r],
        groups=[g],
    )
    write_cache(result)
    assert cache_file.exists()

    loaded = read_cache()
    assert loaded.scanned_at == "2026-04-04T10:00:00Z"
    assert loaded.groups[0].group_name == "myapp"


def test_read_cache_missing_file(tmp_path, monkeypatch):
    monkeypatch.setenv("AWSCOPE_CACHE_PATH", str(tmp_path / "nope.json"))
    with pytest.raises(FileNotFoundError, match="Run 'awscope scan'"):
        read_cache()
