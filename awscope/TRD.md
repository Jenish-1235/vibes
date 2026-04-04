# awscope — Technical Requirements Document

## Platform

Python 3.12+. CLI-first, with an optional local web server. Runs entirely on the developer's machine.

- Config: `~/.awscope/config.toml`
- Scan cache: `~/.awscope/cache.json` (lightweight JSON, always written)
- Pipeline store: DynamoDB Local container (optional; stores per-run resource data and Claude responses for prompt construction and history)
- Export store: MinIO container (optional; S3-compatible object storage, receives a copy of every Excel export)

---

## Tech Stack


| Concern         | Choice                                     | Reason                                                                                 |
| --------------- | ------------------------------------------ | -------------------------------------------------------------------------------------- |
| Language        | Python 3.12+                               | boto3, anthropic SDK, and openpyxl are all Python-native; no impedance mismatch        |
| CLI             | Typer                                      | Decorator-based command definition, auto-generates help, pairs naturally with Rich     |
| Terminal output | Rich                                       | Tables, progress spinners, colored status — zero effort                                |
| Web server      | FastAPI                                    | Minimal, fast; serves both JSON API and static HTML from the same process              |
| HTML/JS         | Plain HTML + vanilla JS                    | No build step, no npm, no framework; a single `index.html` is sufficient               |
| AWS SDK         | boto3                                      | Standard. No alternative.                                                              |
| AI grouping     | anthropic Python SDK (model configurable)  | Semantic grouping requires language understanding, not regex                           |
| Config          | TOML via `tomllib` (stdlib, 3.11+)         | No extra dependency; human-writable                                                    |
| Env vars        | python-dotenv                              | Load `.env` from project root; supports `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `CLAUDE_MODEL` |
| Cache           | JSON file (`~/.awscope/cache.json`)        | Trivial to write/read; inspectable with any text editor or `jq`                        |
| Excel export    | openpyxl                                   | Pure Python, no LibreOffice or Excel dependency, produces proper `.xlsx`               |
| Data models     | Python dataclasses                         | Lightweight; no validation overhead needed — data comes from trusted AWS API responses |
| Export storage  | MinIO (Docker container)                   | S3-compatible local object store; receives a copy of every Excel export alongside the local file |
| Pipeline store  | DynamoDB Local (Docker container)          | Stores per-run scan data and raw Claude responses; used for prompt construction and run history |
| Containers      | Docker + docker-compose                    | Orchestrates awscope-web, MinIO, and DynamoDB Local as a single stack                 |


---

## Directory Structure

```
awscope/
├── README.md
├── PRD.md
├── TRD.md
├── requirements.txt
├── pyproject.toml              ← entry point: `awscope` CLI command
├── Dockerfile                  ← builds awscope-web container (port 8080)
├── docker-compose.yml          ← orchestrates awscope-web + minio + dynamodb-local
├── .env.example                ← template for environment variables (committed)
├── .env                        ← actual env vars — NOT committed (in .gitignore)
└── awscope/                    ← Python package root
    ├── __init__.py
    ├── cli.py                  ← Typer app, all CLI commands
    ├── web.py                  ← FastAPI app, all routes
    ├── scanner.py              ← boto3 scanning logic, per-service collectors
    ├── grouper.py              ← Claude API call, loads prompt from prompts/, parses response
    ├── cache.py                ← read/write ~/.awscope/cache.json
    ├── store.py                ← DynamoDB Local read/write (pipeline run history)
    ├── object_store.py         ← MinIO upload (Excel export copies)
    ├── config.py               ← load config.toml + .env, AccountConfig dataclass
    ├── exporter.py             ← openpyxl Excel generation
    ├── models.py               ← AwsResource, ResourceGroup, ScanResult, PipelineRun dataclasses
    ├── prompts/
    │   └── system_grouping.md  ← Claude system prompt for resource grouping (user-editable)
    └── static/
        └── index.html          ← single-file web dashboard (HTML + inline JS)
```

Entry point: `python -m awscope.cli` or `awscope` if installed via `pyproject.toml` script entry.

---

## Environment Variables (.env)

`python-dotenv` loads `.env` from the project root (where the user runs `awscope`). All variables are optional — they can also be set as real shell environment variables, which take precedence.

**`.env.example`** (committed to repo as template):
```dotenv
# ── Claude ──────────────────────────────────────────────────────────────────
# API key — required for AI grouping (auto-skipped if not set)
ANTHROPIC_API_KEY=sk-ant-...

# Optional: override API base URL (e.g. for litellm proxy or custom endpoint)
ANTHROPIC_BASE_URL=https://litellm.internal/v1

# Optional: Claude model to use (default: claude-sonnet-4-6)
CLAUDE_MODEL=claude-sonnet-4-6

# ── MinIO (Excel export object store) ───────────────────────────────────────
# Leave blank to disable MinIO upload (local-only export still works)
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=awscope-exports

# ── DynamoDB Local (pipeline run store) ─────────────────────────────────────
# Leave blank to disable DynamoDB storage (cache.json still written)
DYNAMODB_ENDPOINT=http://localhost:8000
```

**Resolution order** for each variable: shell env var → `.env` file → built-in default.

`config.py` exposes:
- `get_anthropic_settings() -> dict` — reads `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `CLAUDE_MODEL`
- `get_minio_settings() -> dict | None` — returns None if `MINIO_ENDPOINT` is unset (disables upload)
- `get_dynamodb_settings() -> dict | None` — returns None if `DYNAMODB_ENDPOINT` is unset (disables store)

---

## Config Model

**Location**: `~/.awscope/config.toml`

Supports five credential modes per account:

```toml
# Mode 1 — named AWS CLI profile (most common)
[accounts.personal]
profile = "default"

# Mode 2 — named profile + assume an IAM role
[accounts.clientx]
profile = "clientx-base"
role_arn = "arn:aws:iam::123456789012:role/ReadOnlyAuditRole"
role_session_name = "awscope"          # optional, default: "awscope"
external_id = "client-external-id"    # optional, only if trust policy requires it

# Mode 3 — ambient credentials + assume role (EC2/ECS/Lambda execution role, GitHub Actions OIDC, etc.)
[accounts.cross-account]
role_arn = "arn:aws:iam::987654321098:role/AuditRole"
# no profile — boto3 default credential chain

# Mode 4 — static access keys (least preferred; use only for temporary/short-lived creds)
[accounts.temp-client]
access_key_id = "AKIAIOSFODNN7EXAMPLE"
secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
session_token = "FwoGZXIvYXdzE..."    # optional, for temporary STS credentials

# Mode 5 — AWS SSO / IAM Identity Center profile
[accounts.sso-prod]
profile = "sso-prod"                  # must match a profile in ~/.aws/config with sso_* fields
auth_type = "sso"                     # marks this as SSO so the web UI shows a "Login" button
```

**Note on static keys**: Storing long-lived access keys in a config file is the least secure option. Prefer profiles, SSO, or role assumption. Use Mode 4 only for short-lived STS session tokens or one-off audits. The config file lives at `~/.awscope/` (not in the project directory) to reduce accidental exposure.

**SSO prerequisite**: For Mode 5, run `aws sso login --profile <profile>` in a terminal before scanning. The web dashboard shows per-account auth status and a "Re-authenticate SSO" button that spawns this subprocess for SSO accounts.

**Bulk import shortcut**: `awscope import-profiles` reads `~/.aws/config`, lists all named profiles, and lets you select which ones to add as aliases in a single interactive pass.

**Dataclass** (`config.py`):

```python
@dataclass
class AccountConfig:
    alias: str
    auth_type: str              # "profile" | "profile+role" | "ambient+role" | "static" | "sso"
    profile: str | None
    role_arn: str | None
    role_session_name: str      # default: "awscope"
    external_id: str | None
    access_key_id: str | None   # Mode 4 only
    secret_access_key: str | None
    session_token: str | None
```

**Session construction** (`config.py → build_session(account: AccountConfig) -> boto3.Session`):

| Mode | Logic |
|---|---|
| `profile` | `boto3.Session(profile_name=profile)` |
| `profile+role` | profile session → `STS.assume_role(RoleArn, SessionName, ExternalId?)` → new Session from temp creds |
| `ambient+role` | `boto3.Session()` → `STS.assume_role(...)` → new Session from temp creds |
| `static` | `boto3.Session(aws_access_key_id=..., aws_secret_access_key=..., aws_session_token=...)` |
| `sso` | `boto3.Session(profile_name=profile)` — boto3 handles SSO token refresh automatically if `aws sso login` was run |

`load_config() -> list[AccountConfig]` reads the TOML, infers `auth_type` from which fields are present, validates at least one account is present, raises `ConfigError` if malformed.

`awscope init` interactively prompts: alias → auth type (menu) → relevant fields for that type. Creates `~/.awscope/` and the file if they do not exist.

---

## Data Model

All defined in `models.py`. Plain Python dataclasses. No ORM, no Pydantic.

```python
@dataclass
class AwsResource:
    resource_id: str       # service-specific ID (instance ID, bucket name, function name, etc.)
    name: str              # best-effort human name (from Name tag, or resource_id as fallback)
    resource_type: str     # e.g. "ec2:instance", "s3:bucket", "rds:db", "lambda:function"
    arn: str               # full ARN where available; empty string if the service does not provide one
    region: str            # e.g. "us-east-1"; "global" for S3 and CloudFront
    account_alias: str     # alias from config, e.g. "personal"
    account_id: str        # numeric AWS account ID resolved via STS
    status: str            # service-specific status string, e.g. "running", "available", "active"
    tags: dict[str, str]   # raw tag dict from AWS API
    raw: dict              # full raw boto3 response dict (for debug / future use)

@dataclass
class ResourceGroup:
    group_name: str        # canonical group name assigned by Claude, e.g. "hagrid"
    resources: list[AwsResource]

@dataclass
class ScanResult:
    scanned_at: str        # ISO 8601 timestamp, e.g. "2026-04-04T10:30:00Z"
    accounts: list[str]    # account aliases scanned
    resources: list[AwsResource]
    groups: list[ResourceGroup]

@dataclass
class ClaudeBatch:
    batch_number: int
    prompt_sent: str       # full user message sent to Claude (JSON array of resource descriptors)
    raw_response: str      # raw text response from Claude
    parsed: bool           # whether json.loads succeeded
    resource_count: int

@dataclass
class PipelineRun:
    run_id: str            # UUID, generated at scan start
    scanned_at: str        # ISO 8601
    accounts: list[str]
    total_resources: int
    total_groups: int
    claude_batches: list[ClaudeBatch]   # one entry per Claude API call made
    duration_seconds: float
```

`ScanResult` is the `cache.json` payload. `PipelineRun` is written to DynamoDB Local (if configured) and is separate from the cache. Serialization handled by thin helpers in `cache.py` and `store.py` respectively — no third-party serialization library.

---

## Core Pipeline

```
awscope scan
    │
    ├─ 1. load_config()                        config.py
    │       └─ parse ~/.awscope/config.toml
    │
    ├─ 2. scan_all_accounts(configs)           scanner.py
    │       for each AccountConfig:
    │         build_session(account) → boto3.Session  (handles all 5 auth modes)
    │         STS.get_caller_identity() → account_id
    │         ec2.describe_regions(Filters=[opt-in-not-required, opted-in]) → all enabled regions
    │         ── Global collectors (once per account, always against us-east-1) ──
    │           collect_iam_users()              + inline/attached policies, groups, MFA status
    │           collect_iam_groups()             + inline/attached policies, member count
    │           collect_iam_roles()              + inline/attached policies, trust policy
    │           collect_iam_customer_policies()  customer-managed only (Scope='Local')
    │           collect_s3_buckets()
    │           collect_cloudfront_distributions()
    │           collect_route53_hosted_zones()
    │         ── Per-region collectors ──
    │         for each region:
    │           # Compute
    │           collect_ec2_instances()
    │           collect_autoscaling_groups()
    │           collect_lambda_functions()
    │           collect_ecs_clusters()
    │           collect_eks_clusters()
    │           # Storage & DB
    │           collect_rds_instances()
    │           collect_dynamodb_tables()
    │           collect_elasticache_clusters()
    │           collect_elasticache_replication_groups()
    │           collect_redshift_clusters()
    │           collect_opensearch_domains()
    │           collect_kinesis_streams()
    │           collect_ecr_repositories()
    │           # Messaging
    │           collect_sqs_queues()
    │           collect_sns_topics()
    │           # Networking
    │           collect_vpcs()
    │           collect_subnets()
    │           collect_security_groups()
    │           collect_internet_gateways()
    │           collect_nat_gateways()
    │           collect_vpc_endpoints()
    │           collect_route_tables()
    │           collect_network_acls()
    │           collect_transit_gateways()
    │           collect_vpc_peering_connections()
    │           collect_load_balancers_v2()       (ALB + NLB via elbv2)
    │           collect_load_balancers_classic()  (ELB classic)
    │           # API & Security
    │           collect_apigateway_rest_apis()
    │           collect_apigatewayv2_http_apis()
    │           collect_acm_certificates()
    │           collect_secretsmanager_secrets()
    │       returns flat list[AwsResource]
    │
    ├─ 3. group_resources(resources)           grouper.py
    │       load system prompt from awscope/prompts/system_grouping.md
    │       chunk resources into batches of 200
    │       for each batch:
    │         build user message (JSON array of resource descriptors)
    │         call Claude API → raw response text
    │         parse JSON → {resource_id: group_name}
    │         resources with no name match → group_name = "miscellaneous"
    │         append ClaudeBatch to PipelineRun.claude_batches
    │       assemble list[ResourceGroup]
    │
    ├─ 4. write_cache(ScanResult)              cache.py
    │       serialize → ~/.awscope/cache.json
    │
    ├─ 5. write_pipeline_run(PipelineRun)      store.py
    │       if DYNAMODB_ENDPOINT configured:
    │         put PipelineRun metadata → PipelineRuns table (PK=run_id, SK=META)
    │         put each AwsResource → PipelineRuns table (PK=run_id, SK=RESOURCE#{resource_id})
    │         put each ClaudeBatch → PipelineRuns table (PK=run_id, SK=BATCH#{batch_number})
    │       else: skip silently
    │
    └─ 6. print summary Rich table            cli.py

    Export path (awscope export / web /api/export):
    ├─ exporter.py generates .xlsx in memory (BytesIO)
    ├─ write to local disk (CLI) or stream as HTTP response (web)
    └─ object_store.py uploads copy to MinIO  (if MINIO_ENDPOINT configured)
           bucket: awscope-exports
           object key: exports/{YYYY-MM-DD}/{run_id}_{timestamp}.xlsx
           failure is non-fatal — warn and continue
```

---

## AWS Services — v1

All services are queried across **all enabled regions** unless marked as Global. Global services are collected exactly once per account (on the `us-east-1` pass) to avoid duplicates.

Region enumeration: `ec2.describe_regions(Filters=[{'Name': 'opt-in-status', 'Values': ['opt-in-not-required', 'opted-in']}])` — captures all regions the account has access to, including opted-in regions.

**Global services collected once per account**: IAM, S3, CloudFront, Route 53. The scanner uses a `collected_globals: set[str]` per account to skip on subsequent region passes.

### IAM & Identity (Global)

| Service              | resource_type              | Key boto3 Call                                    | Notes |
| -------------------- | -------------------------- | ------------------------------------------------- | ----- |
| IAM User             | `iam:user`                 | `list_users` + `list_attached_user_policies` + `list_user_policies` + `list_groups_for_user` + `list_mfa_devices` | MFA status, attached + inline policies, group membership |
| IAM Group            | `iam:group`                | `list_groups` + `list_attached_group_policies` + `list_group_policies` + `get_group` | Attached + inline policies, member list |
| IAM Role             | `iam:role`                 | `list_roles` + `list_attached_role_policies` + `list_role_policies` | Trust policy, attached + inline policies; excludes AWS service-linked roles unless configured |
| IAM Policy (custom)  | `iam:policy`               | `list_policies(Scope='Local')` + `get_policy_version` | Customer-managed only; includes policy document |

### Compute (Per-region)

| Service      | resource_type        | Key boto3 Call                         | Filter          |
| ------------ | -------------------- | -------------------------------------- | --------------- |
| EC2          | `ec2:instance`       | `describe_instances`                   | state = running |
| Auto Scaling | `autoscaling:group`  | `describe_auto_scaling_groups`         | None            |
| Lambda       | `lambda:function`    | `list_functions`                       | None            |
| ECS          | `ecs:cluster`        | `list_clusters` + `describe_clusters`  | None            |
| EKS          | `eks:cluster`        | `list_clusters` + `describe_cluster`   | None            |

### Storage & Databases (Global / Per-region)

| Service          | resource_type                   | Key boto3 Call                               | Scope      |
| ---------------- | ------------------------------- | -------------------------------------------- | ---------- |
| S3               | `s3:bucket`                     | `list_buckets`                               | Global     |
| RDS              | `rds:db`                        | `describe_db_instances`                      | Per-region |
| DynamoDB         | `dynamodb:table`                | `list_tables` + `describe_table`             | Per-region |
| ElastiCache      | `elasticache:cluster`           | `describe_cache_clusters`                    | Per-region |
| ElastiCache RG   | `elasticache:replication-group` | `describe_replication_groups`                | Per-region |
| Redshift         | `redshift:cluster`              | `describe_clusters`                          | Per-region |
| OpenSearch       | `opensearch:domain`             | `list_domain_names` + `describe_domains`     | Per-region |
| Kinesis          | `kinesis:stream`                | `list_streams` + `describe_stream_summary`   | Per-region |
| ECR              | `ecr:repository`                | `describe_repositories`                      | Per-region |

### Messaging (Per-region)

| Service | resource_type   | Key boto3 Call  |
| ------- | --------------- | --------------- |
| SQS     | `sqs:queue`     | `list_queues`   |
| SNS     | `sns:topic`     | `list_topics`   |

### Networking & Security (Global / Per-region)

| Service                   | resource_type                      | Key boto3 Call                         | Scope      |
| ------------------------- | ---------------------------------- | -------------------------------------- | ---------- |
| VPC                       | `ec2:vpc`                          | `describe_vpcs`                        | Per-region |
| Subnet                    | `ec2:subnet`                       | `describe_subnets`                     | Per-region |
| Security Group            | `ec2:security-group`               | `describe_security_groups`             | Per-region |
| Internet Gateway          | `ec2:internet-gateway`             | `describe_internet_gateways`           | Per-region |
| NAT Gateway               | `ec2:nat-gateway`                  | `describe_nat_gateways`                | Per-region |
| VPC Endpoint              | `ec2:vpc-endpoint`                 | `describe_vpc_endpoints`               | Per-region |
| Route Table               | `ec2:route-table`                  | `describe_route_tables`                | Per-region |
| Network ACL               | `ec2:network-acl`                  | `describe_network_acls`                | Per-region |
| Transit Gateway           | `ec2:transit-gateway`              | `describe_transit_gateways`            | Per-region |
| VPC Peering               | `ec2:vpc-peering-connection`       | `describe_vpc_peering_connections`     | Per-region |
| Load Balancer (ALB/NLB)   | `elbv2:load-balancer`              | `describe_load_balancers` (elbv2)      | Per-region |
| Load Balancer (Classic)   | `elb:load-balancer`                | `describe_load_balancers` (elb)        | Per-region |
| CloudFront                | `cloudfront:distribution`          | `list_distributions`                   | Global     |
| Route 53                  | `route53:hosted-zone`              | `list_hosted_zones`                    | Global     |
| ACM Certificate           | `acm:certificate`                  | `list_certificates`                    | Per-region |

### API & Secrets (Per-region)

| Service         | resource_type              | Key boto3 Call   |
| --------------- | -------------------------- | ---------------- |
| API Gateway v1  | `apigateway:rest-api`      | `get_rest_apis`  |
| API Gateway v2  | `apigateway:http-api`      | `get_apis`       |
| Secrets Manager | `secretsmanager:secret`    | `list_secrets`   |

---

## Prompts Directory

**Location**: `awscope/prompts/`

System prompts are stored as Markdown files in this directory, not hardcoded in Python. `grouper.py` loads the relevant prompt file at runtime using `Path(__file__).parent / "prompts" / "system_grouping.md"`. This allows the prompt to be edited, versioned, and iterated on without touching source code.

```
awscope/prompts/
└── system_grouping.md    ← system prompt for Claude resource grouping
                             (placeholder content; master prompt to be designed separately)
```

The file is read once per `group_resources()` call. If the file is missing, `grouper.py` raises a clear error: `"Prompt file not found: prompts/system_grouping.md"`.

Additional prompt files can be added here as new Claude use-cases are introduced (e.g. cost analysis, security review). Each file is named after its purpose.

---

## Claude API — Grouping Prompt Design

**Module**: `grouper.py`
**Model**: Configurable via `CLAUDE_MODEL` env var / `.env`. Default: `claude-sonnet-4-6`. Read at runtime — no hard-code in source.
**Base URL**: Configurable via `ANTHROPIC_BASE_URL`. Routes through a custom endpoint (e.g. litellm proxy) when set.
**Batch size**: 200 resources per API call (sequential, no parallelism)
**System prompt**: Loaded from `awscope/prompts/system_grouping.md` at runtime

**Placeholder rules in `system_grouping.md`** (to be replaced by master prompt):

```
You are a resource grouping assistant for an AWS infrastructure auditing tool.
Assign each AWS resource to a logical product or service group based on its name, type, and tags.

Rules:
- Group name must be a short, lowercase identifier (e.g. "hagrid", "myapp", "data-pipeline")
- Resources with similar name prefixes belong to the same group:
  "hagrid-api", "hagrid-prod", "hagrid-staging" → "hagrid"
- Ignore environment/version suffixes: -prod, -staging, -dev, -test, -qa, -v2, -old, -new, -1, -2
- Use tags (especially "Project", "Application", "Service", "product", "app") as a secondary signal
- Resources whose name does not match any other resource or tag pattern → group as "miscellaneous"
- Auto-generated IDs with no informative tags → group as "miscellaneous"
- Return a flat JSON array only — no explanation text, no markdown, no code fences
```

**User message**: JSON array of `{"resource_id": "...", "name": "...", "resource_type": "...", "tags": {...}}` objects.

**Expected response** (raw JSON, no markdown):

```json
[
  {"resource_id": "i-0abc123", "group_name": "hagrid"},
  {"resource_id": "hagrid-assets", "group_name": "hagrid"},
  {"resource_id": "i-0xyz789", "group_name": "miscellaneous"}
]
```

**Parsing**: `json.loads(raw_response)` → `{resource_id: group_name}` dict. On parse failure: log warning, assign entire batch to `"miscellaneous"`. Any resource_id not present in the response (omitted by Claude) is also assigned `"miscellaneous"`.

**API parameters**: `max_tokens=4096`. No streaming.

---

## CLI Commands


| Command                    | Description                                                        | Flags                                                              |
| -------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `awscope init`             | Interactively add one account alias to config (menu for auth type) | —                                                                  |
| `awscope import-profiles`  | Bulk-import from `~/.aws/config` — select profiles to alias        | —                                                                  |
| `awscope accounts`         | List configured accounts + connection status (STS check)           | —                                                                  |
| `awscope scan`             | Scan accounts, group via Claude, write cache                       | `--accounts TEXT` (comma-sep aliases), `--no-group` (skip Claude)  |
| `awscope list`             | Print grouped summary from cache                                   | `--account TEXT` (filter to one alias)                             |
| `awscope show <group>`     | Print all resources in a group                                     | —                                                                  |
| `awscope export`           | Write Excel file (4 sheets) to current dir                         | `--output TEXT` (default: timestamped filename)                    |
| `awscope web`              | Start FastAPI local server                                         | `--port INT` (default: 8080), `--host TEXT` (default: 127.0.0.1)  |


---

## Web Routes (FastAPI)

### Dashboard data

| Method | Path                       | Description                                                                  |
| ------ | -------------------------- | ---------------------------------------------------------------------------- |
| GET    | `/`                        | Serve `static/index.html`                                                    |
| GET    | `/api/summary`             | `{scanned_at, accounts, group_count, resource_count}`                        |
| GET    | `/api/groups`              | List of `{group_name, resource_count, resource_types, accounts}` for sidebar |
| GET    | `/api/groups/{group_name}` | Full resource list for one group                                             |
| GET    | `/api/export`              | Stream `.xlsx` file as `Content-Disposition: attachment` download            |

### Account management

| Method | Path                                  | Description                                                                 |
| ------ | ------------------------------------- | --------------------------------------------------------------------------- |
| GET    | `/api/accounts`                       | List configured accounts with auth_type and connection status (calls STS.get_caller_identity per account, returns `connected` / `expired` / `error`) |
| POST   | `/api/accounts/{alias}/sso-login`     | For `auth_type=sso` accounts only — spawns `aws sso login --profile <profile>` as a subprocess; returns `{status: "browser_opened"}` or error |
| GET    | `/api/accounts/{alias}/status`        | Re-check connection status for one account (STS call)                      |

**`/api/accounts`** is used by the web dashboard's "Connections" panel to show a per-account health table: alias, auth type, account ID (if connected), status badge.

**`/api/accounts/{alias}/sso-login`** is the backend for the "Re-authenticate SSO" button. It spawns the `aws sso login` subprocess which opens the user's default browser to the SSO login page. The endpoint returns immediately; the user completes login in the browser and the token is stored by the AWS CLI. Subsequent API calls use the refreshed token automatically.

`/api/export` uses the same `exporter.py` logic as the CLI but writes to a `BytesIO` buffer and returns a `StreamingResponse`. No file is written to disk in the web export path.

Static files: `awscope/static/` mounted at `/static/` via FastAPI `StaticFiles`. `index.html` fetches all data from the `/api/*` routes via `fetch()`.

---

## Excel Export Schema (openpyxl)

Output: single `.xlsx` file with **four sheets**. Bold headers, light blue fill (`A8D8EA`) on all headers.

### Sheet 1 — "Summary"

Columns: `Group` | `Resource Count` | `Resource Types` | `Accounts` | `Regions`

One row per group. "Resource Types", "Accounts", "Regions" are comma-joined unique values.

### Sheet 2 — "All Resources"

Columns: `Group` | `Name` | `Resource Type` | `Resource ID` | `ARN` | `Region` | `Account Alias` | `Account ID` | `Status` | `Tags`

One row per resource (all resource types except IAM and networking — those have dedicated sheets). "Tags" serialized as `key=value, key=value` (sorted by key). Rows sorted by Group → Resource Type → Name.

### Sheet 3 — "IAM Audit"

Two sub-tables in one sheet, separated by a blank row and a bold section header:

**Users table** — one row per IAM user:
`Account` | `Username` | `ARN` | `Created` | `Last Login` | `MFA Enabled` | `Groups` | `Attached Policies` | `Inline Policies` | `Tags`

**Roles table** — one row per IAM role (excluding AWS service-linked roles unless opted in):
`Account` | `Role Name` | `ARN` | `Created` | `Trust Principals` | `Attached Policies` | `Inline Policies` | `Tags`

**Groups table** — one row per IAM group:
`Account` | `Group Name` | `ARN` | `Members` | `Attached Policies` | `Inline Policies`

**Custom Policies table** — one row per customer-managed policy:
`Account` | `Policy Name` | `ARN` | `Description` | `Attached To` | `Version` | `Tags`

Multi-value fields (groups, policies, members) are newline-joined within the cell. Cells with wrap text enabled.

### Sheet 4 — "Networking"

**VPCs table** — one row per VPC:
`Account` | `Region` | `VPC ID` | `Name` | `CIDR` | `Default` | `State` | `Tags`

**Security Groups table** — one row per security group:
`Account` | `Region` | `Group ID` | `Group Name` | `VPC ID` | `Description` | `Inbound Rules` | `Outbound Rules` | `Tags`

Inbound/Outbound Rules are serialized as `protocol:port-range:source/dest` per rule, newline-joined.

**Subnets table** — one row per subnet:
`Account` | `Region` | `Subnet ID` | `Name` | `VPC ID` | `CIDR` | `AZ` | `Public` | `Tags`

**Gateways & Endpoints table** — one row per gateway/endpoint (IGW, NAT GW, VPC Endpoint, Transit GW):
`Account` | `Region` | `Resource Type` | `ID` | `Name` | `VPC ID` | `State` | `Tags`

**Load Balancers table** — one row per load balancer:
`Account` | `Region` | `Name` | `Type` | `Scheme` | `DNS Name` | `VPC ID` | `State` | `Tags`

---

## Docker

Three containers are orchestrated via `docker-compose.yml`:

| Container | Image | Port | Purpose |
|---|---|---|---|
| `awscope-web` | Built from `Dockerfile` | 8080 | FastAPI web dashboard (reads mounted cache) |
| `minio` | `minio/minio:latest` | 9000 (API), 9001 (console) | S3-compatible object store for Excel exports |
| `dynamodb-local` | `amazon/dynamodb-local:latest` | 8000 | Local DynamoDB for pipeline run history |

### Dockerfile (awscope-web only)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY awscope/ ./awscope/
EXPOSE 8080
ENV AWSCOPE_CACHE_PATH=/app/cache.json
CMD ["uvicorn", "awscope.web:app", "--host", "0.0.0.0", "--port", "8080"]
```

`web.py` reads the cache path from `AWSCOPE_CACHE_PATH` env var, falling back to `~/.awscope/cache.json`.

### docker-compose.yml

```yaml
services:
  awscope-web:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ~/.awscope/cache.json:/app/cache.json:ro
    env_file:
      - .env
    depends_on:
      - minio
      - dynamodb-local

  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio-data:/data
    command: server /data --console-address ":9001"

  dynamodb-local:
    image: amazon/dynamodb-local:latest
    ports:
      - "8000:8000"
    volumes:
      - dynamodb-data:/home/dynamodblocal/data
    command: -jar DynamoDBLocal.jar -sharedDb -dbPath /home/dynamodblocal/data

volumes:
  minio-data:
  dynamodb-data:
```

**Usage**:
```bash
# Start the full stack (web + MinIO + DynamoDB Local)
docker compose up

# Start MinIO + DynamoDB Local only (run CLI on host, use containers for storage)
docker compose up minio dynamodb-local

# Web dashboard only (no storage containers)
docker build -t awscope . && docker run -p 8080:8080 -v ~/.awscope/cache.json:/app/cache.json awscope
```

**MinIO bucket bootstrap**: On first run, `object_store.py` checks if the `awscope-exports` bucket exists and creates it if not (`create_bucket` is idempotent). No manual setup required.

**DynamoDB Local table bootstrap**: On first use, `store.py` calls `create_table` for `PipelineRuns` if it doesn't exist. Table schema:
- Partition key: `run_id` (String)
- Sort key: `sk` (String) — values: `META`, `RESOURCE#{resource_id}`, `BATCH#{batch_number}`
- Billing mode: `PAY_PER_REQUEST`

---

## Key Constraints

1. **Local only (default).** Web server binds `127.0.0.1` by default. No authentication required — not intended to be exposed beyond localhost. Docker run binds `0.0.0.0` but that is opt-in.
2. **No shared code with other vibes projects.** `awscope/` has its own `requirements.txt`. Nothing is imported from `ledge/` or any other project.
3. **One config file, one cache file.** No database, no migrations. If cache schema changes between versions, delete `~/.awscope/cache.json` and re-scan.
4. **No AWS resource writes.** All boto3 calls against AWS are read-only (`describe_*`, `list_*`, `get_*`). No `create`, `delete`, `modify`, `put`, or `attach` calls anywhere. The only exceptions are: (a) SSO login subprocess writes a token to `~/.aws/sso/cache/` — handled by the AWS CLI, not awscope; (b) `store.py` writes to DynamoDB Local — a local container, not AWS.
5. **`ANTHROPIC_API_KEY` is optional — auto-fallback to `--no-group`.** If the key is not set and `--no-group` was not explicitly passed, `scan` prints a warning and proceeds without grouping: `"ANTHROPIC_API_KEY not set — skipping AI grouping. Use --no-group to suppress this warning."` Resources are placed into a single `"miscellaneous"` group. This is the default no-Claude mode.
6. **boto3 errors are non-fatal per service.** If a collector raises a boto3 exception (service not enabled in region, access denied), log a warning and continue. A failed region/service pair does not abort the scan.
7. **No concurrency.** Accounts and regions are iterated sequentially. Sufficient for personal-scale account counts.
8. **Global services collected once per account.** IAM, S3, CloudFront, and Route 53 are collected on the `us-east-1` pass and skipped in subsequent regions via a `collected_globals: set[str]` per account.
9. **MinIO and DynamoDB Local are optional.** If `MINIO_ENDPOINT` is not set, exports are local-only — no upload, no error. If `DYNAMODB_ENDPOINT` is not set, pipeline history is not stored — `cache.json` is the only persistence. Both containers are opt-in; the CLI and web work fully without them.
10. **`"miscellaneous"` is the catch-all group.** Any resource whose name does not fuzzy-match any other resource or tag pattern is assigned to `"miscellaneous"` by Claude. On Claude API parse failure, all resources in the affected batch are also assigned `"miscellaneous"`. Resources omitted from Claude's response are assigned `"miscellaneous"`. There is no "ungrouped" — that term is not used anywhere in the codebase.
11. **System prompt is a file, not a string.** `grouper.py` always loads `awscope/prompts/system_grouping.md` at runtime. Never hardcode prompt text in Python source. If the file is missing, the process exits with a clear error.
12. **Static access keys in config.toml are a security trade-off.** The config lives at `~/.awscope/` (not the project directory) and is not committed to git. Document clearly in README that SSO or profile-based auth is preferred. Keys in config.toml should only be used for short-lived STS session tokens.
10. **IAM role audit excludes AWS service-linked roles by default.** `list_roles` returns all roles including hundreds of AWS-managed service-linked roles (e.g. `AWSServiceRoleFor*`). These are filtered out by default (path prefix `/aws-service-role/`) as they are not customer-created. A future `--include-service-roles` flag can opt into them.
11. **`.env` is not committed.** `.gitignore` must include `.env`. `.env.example` is committed as a template.
13. **`requirements.txt` pins major versions**: `boto3>=1.34`, `anthropic>=0.25`, `fastapi>=0.111`, `uvicorn>=0.29`, `typer>=0.12`, `rich>=13`, `openpyxl>=3.1`, `python-dotenv>=1.0`. MinIO and DynamoDB Local are accessed via `boto3` (S3-compatible endpoint for MinIO, standard DynamoDB client with custom `endpoint_url` for DynamoDB Local) — no extra packages needed.

