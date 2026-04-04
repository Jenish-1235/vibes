from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class AwsResource:
    resource_id: str
    name: str
    resource_type: str       # e.g. "ec2:instance", "s3:bucket", "iam:user"
    arn: str                 # empty string when unavailable
    region: str              # "global" for IAM, S3, CloudFront, Route53
    account_alias: str
    account_id: str
    status: str
    tags: dict[str, str]
    raw: dict


@dataclass
class ResourceGroup:
    group_name: str          # "hagrid", "miscellaneous", etc.
    resources: list[AwsResource] = field(default_factory=list)


@dataclass
class ScanResult:
    scanned_at: str          # ISO 8601
    accounts: list[str]
    resources: list[AwsResource]
    groups: list[ResourceGroup]


@dataclass
class ClaudeBatch:
    batch_number: int
    prompt_sent: str         # user message JSON sent to Claude
    raw_response: str        # raw text from Claude
    parsed: bool             # whether json.loads succeeded
    resource_count: int


@dataclass
class PipelineRun:
    run_id: str              # UUID
    scanned_at: str          # ISO 8601
    accounts: list[str]
    total_resources: int
    total_groups: int
    claude_batches: list[ClaudeBatch] = field(default_factory=list)
    duration_seconds: float = 0.0
