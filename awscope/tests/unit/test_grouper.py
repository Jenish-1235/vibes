import json
from unittest.mock import MagicMock, patch

import pytest

from awscope.grouper import _build_user_message, _parse_response, group_resources
from awscope.models import AwsResource


def _resource(rid, name, rtype="ec2:instance", tags=None):
    return AwsResource(
        resource_id=rid, name=name, resource_type=rtype,
        arn="", region="us-east-1", account_alias="personal",
        account_id="123", status="running", tags=tags or {}, raw={},
    )


def test_build_user_message():
    resources = [_resource("i-123", "hagrid-api", tags={"Env": "prod"})]
    msg = _build_user_message(resources)
    data = json.loads(msg)
    assert data[0]["resource_id"] == "i-123"
    assert data[0]["tags"] == {"Env": "prod"}


def test_parse_response_success():
    raw = '[{"resource_id":"i-123","group_name":"hagrid"},{"resource_id":"i-456","group_name":"payments"}]'
    mapping, ok = _parse_response(raw, {"i-123", "i-456"})
    assert ok is True
    assert mapping["i-123"] == "hagrid"
    assert mapping["i-456"] == "payments"


def test_parse_response_missing_id_fallback():
    raw = '[{"resource_id":"i-123","group_name":"hagrid"}]'
    mapping, ok = _parse_response(raw, {"i-123", "i-missing"})
    assert ok is True
    assert mapping["i-missing"] == "miscellaneous"


def test_parse_response_strips_markdown_fences():
    raw = '```json\n[{"resource_id":"i-123","group_name":"hagrid"}]\n```'
    mapping, ok = _parse_response(raw, {"i-123"})
    assert ok is True
    assert mapping["i-123"] == "hagrid"


def test_parse_response_invalid_json():
    mapping, ok = _parse_response("not json", {"i-123"})
    assert ok is False
    assert mapping["i-123"] == "miscellaneous"


def test_group_resources_no_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    resources = [_resource("i-123", "hagrid-api")]
    groups, batches = group_resources(resources)
    assert len(groups) == 1
    assert groups[0].group_name == "miscellaneous"
    assert batches == []


def test_group_resources_with_mock_claude(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    mock_content = MagicMock()
    mock_content.text = '[{"resource_id":"i-123","group_name":"hagrid"}]'
    mock_response = MagicMock()
    mock_response.content = [mock_content]

    with patch("awscope.grouper.anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = mock_response

        resources = [_resource("i-123", "hagrid-api")]
        groups, batches = group_resources(resources)

    assert len(groups) == 1
    assert groups[0].group_name == "hagrid"
    assert batches[0].parsed is True


def test_group_resources_api_failure_fallback(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    with patch("awscope.grouper.anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.side_effect = Exception("API down")

        resources = [_resource("i-123", "hagrid-api")]
        groups, batches = group_resources(resources)

    assert groups[0].group_name == "miscellaneous"
    assert batches[0].parsed is False
