from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path

from awscope.models import AwsResource, ResourceGroup, ScanResult

_DEFAULT_CACHE = Path.home() / ".awscope" / "cache.json"


def _cache_path() -> Path:
    env = os.getenv("AWSCOPE_CACHE_PATH")
    return Path(env) if env else _DEFAULT_CACHE


def _json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def write_cache(result: ScanResult) -> None:
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(_scan_result_to_dict(result), f, indent=2, default=_json_default)


def read_cache() -> ScanResult:
    path = _cache_path()
    if not path.exists():
        raise FileNotFoundError(
            f"No scan data found at {path}. Run 'awscope scan' first."
        )
    with open(path) as f:
        return _scan_result_from_dict(json.load(f))


# ── serialization helpers ──────────────────────────────────────────────────

def _resource_to_dict(r: AwsResource) -> dict:
    return {
        "resource_id": r.resource_id,
        "name": r.name,
        "resource_type": r.resource_type,
        "arn": r.arn,
        "region": r.region,
        "account_alias": r.account_alias,
        "account_id": r.account_id,
        "status": r.status,
        "tags": r.tags,
        "raw": r.raw,
    }


def _resource_from_dict(d: dict) -> AwsResource:
    return AwsResource(
        resource_id=d["resource_id"],
        name=d["name"],
        resource_type=d["resource_type"],
        arn=d["arn"],
        region=d["region"],
        account_alias=d["account_alias"],
        account_id=d["account_id"],
        status=d["status"],
        tags=d.get("tags", {}),
        raw=d.get("raw", {}),
    )


def _scan_result_to_dict(result: ScanResult) -> dict:
    return {
        "scanned_at": result.scanned_at,
        "accounts": result.accounts,
        "resources": [_resource_to_dict(r) for r in result.resources],
        "groups": [
            {
                "group_name": g.group_name,
                "resources": [_resource_to_dict(r) for r in g.resources],
            }
            for g in result.groups
        ],
    }


def _scan_result_from_dict(d: dict) -> ScanResult:
    resources = [_resource_from_dict(r) for r in d.get("resources", [])]
    groups = [
        ResourceGroup(
            group_name=g["group_name"],
            resources=[_resource_from_dict(r) for r in g.get("resources", [])],
        )
        for g in d.get("groups", [])
    ]
    return ScanResult(
        scanned_at=d["scanned_at"],
        accounts=d.get("accounts", []),
        resources=resources,
        groups=groups,
    )
