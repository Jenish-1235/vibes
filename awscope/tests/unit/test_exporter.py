from io import BytesIO

from openpyxl import load_workbook

from awscope.exporter import build_excel
from awscope.models import AwsResource, ResourceGroup, ScanResult


def _resource(rid, name, rtype, region="us-east-1", tags=None):
    return AwsResource(
        resource_id=rid, name=name, resource_type=rtype, arn=f"arn::{rid}",
        region=region, account_alias="personal", account_id="123",
        status="active", tags=tags or {}, raw={},
    )


def _make_result():
    resources = [
        _resource("i-123", "hagrid-api", "ec2:instance"),
        _resource("my-bucket", "my-bucket", "s3:bucket", region="global"),
        _resource("user-alice", "alice", "iam:user"),
        _resource("vpc-abc", "vpc-abc", "ec2:vpc"),
        _resource("sg-xyz", "my-sg", "ec2:security-group", tags={"Name": "my-sg"}),
    ]
    groups = [
        ResourceGroup(group_name="hagrid", resources=resources[:2]),
        ResourceGroup(group_name="miscellaneous", resources=resources[2:]),
    ]
    return ScanResult(
        scanned_at="2026-04-04T10:00:00Z",
        accounts=["personal"],
        resources=resources,
        groups=groups,
    )


def test_build_excel_returns_bytes():
    result = _make_result()
    buf = build_excel(result)
    assert isinstance(buf, BytesIO)
    assert buf.tell() == 0  # seek(0) was called


def test_excel_has_four_sheets():
    result = _make_result()
    buf = build_excel(result)
    wb = load_workbook(buf)
    assert set(wb.sheetnames) == {"Summary", "All Resources", "IAM Audit", "Networking"}


def test_summary_sheet_has_groups():
    result = _make_result()
    buf = build_excel(result)
    wb = load_workbook(buf)
    ws = wb["Summary"]
    rows = list(ws.iter_rows(values_only=True))
    headers = rows[0]
    assert "Group" in headers
    group_names = [r[0] for r in rows[1:] if r[0]]
    assert "hagrid" in group_names
    assert "miscellaneous" in group_names


def test_all_resources_excludes_iam_and_net():
    result = _make_result()
    buf = build_excel(result)
    wb = load_workbook(buf)
    ws = wb["All Resources"]
    rows = list(ws.iter_rows(values_only=True))
    types_in_sheet = {r[2] for r in rows[1:] if r[2]}
    assert "iam:user" not in types_in_sheet
    assert "ec2:vpc" not in types_in_sheet
    # ec2:instance and s3:bucket should be there
    assert "ec2:instance" in types_in_sheet


def test_iam_sheet_has_users_section():
    result = _make_result()
    buf = build_excel(result)
    wb = load_workbook(buf)
    ws = wb["IAM Audit"]
    all_values = [str(c.value or "") for row in ws.iter_rows() for c in row]
    assert any("IAM Users" in v or "Username" in v for v in all_values)


def test_networking_sheet_has_vpc_section():
    result = _make_result()
    buf = build_excel(result)
    wb = load_workbook(buf)
    ws = wb["Networking"]
    all_values = [str(c.value or "") for row in ws.iter_rows() for c in row]
    assert any("VPC" in v for v in all_values)
