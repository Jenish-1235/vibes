# awscope

AI-powered AWS resource inventory and grouping dashboard. Scans all running resources across multiple AWS accounts and uses Claude to group them by product or service — with a CLI and local web dashboard, both with Excel export.

## Status: 🚧 In progress

## What it does

- Connects to multiple AWS accounts via **5 auth modes**: named profile, profile + role assumption, ambient credentials + role, static access keys, or AWS SSO / IAM Identity Center
- Scans all resources across **all enabled regions** — compute, storage, databases, messaging, networking, and IAM
- **IAM full audit**: users (MFA status, policies, groups), roles (trust policies, attachments), groups, customer-managed policies
- **Networking audit**: VPCs, subnets, security groups, internet/NAT gateways, VPC endpoints, route tables, NACLs, transit gateways, VPC peering, load balancers (ALB/NLB/Classic), ACM certificates
- **Other services**: EC2, S3, RDS, Lambda, ECS, EKS, CloudFront, DynamoDB, SQS, SNS, ElastiCache, Route 53, API Gateway (v1+v2), Secrets Manager, OpenSearch, Kinesis, ECR, Redshift
- Uses Claude (model + endpoint configurable via `.env`) to semantically group resources by product name — fuzzy matching, not just tags
- Falls back to ungrouped mode automatically if `ANTHROPIC_API_KEY` is not set
- Presents results in a CLI (Rich tables) and a local web dashboard (FastAPI + plain HTML) with per-account connection status panel and SSO re-authenticate button
- Exports 4-sheet audit report to `.xlsx`: Summary, All Resources, IAM Audit, Networking — saved locally and optionally uploaded to a MinIO container
- `docker-compose.yml` orchestrates web dashboard + MinIO (export storage) + DynamoDB Local (pipeline run history)
- System prompt for Claude lives in `awscope/prompts/system_grouping.md` — edit without touching Python code
- Resources that don't match any product name are grouped as `miscellaneous`

## Prerequisites

- Python 3.12+
- AWS CLI configured with named profiles for each account
- `ANTHROPIC_API_KEY` in `.env` or shell env (optional — scan works without it, grouping is skipped)

## Setup

```bash
cd awscope/
cp .env.example .env          # fill in ANTHROPIC_API_KEY and optionally ANTHROPIC_BASE_URL, CLAUDE_MODEL
pip install -r requirements.txt
pip install -e .
awscope init                  # add first account alias, or:
awscope import-profiles       # bulk-import from ~/.aws/config
```

## Usage

```bash
# Add one AWS account alias interactively (prompts for auth type)
awscope init

# Bulk-import from ~/.aws/config
awscope import-profiles

# Check connection status for all configured accounts
awscope accounts

# Scan all accounts and group resources via Claude
awscope scan

# Scan without AI grouping (auto if ANTHROPIC_API_KEY is not set)
awscope scan --no-group

# Scan specific account aliases only
awscope scan --accounts personal,clientx

# List grouped summary
awscope list

# Inspect a specific group
awscope show hagrid

# Export 4-sheet audit report to Excel (Summary, All Resources, IAM Audit, Networking)
awscope export

# Launch web dashboard (localhost:8080)
# Includes: grouped resource view, IAM audit, networking view, account status panel
awscope web
```

## Docker

```bash
# Full stack: web dashboard + MinIO (export storage) + DynamoDB Local (pipeline history)
docker compose up

# Storage containers only (run CLI on host, store to containers)
docker compose up minio dynamodb-local

# Web dashboard only
docker build -t awscope .
docker run -p 8080:8080 -v ~/.awscope/cache.json:/app/cache.json awscope
```

Run `awscope scan` on your host first to populate the cache. The web container reads it via a mounted volume.

MinIO console: http://localhost:9001 (default credentials: minioadmin / minioadmin)

## Config

`~/.awscope/config.toml` — AWS account aliases, profiles, and optional IAM role ARNs.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | No | — | Claude API key. If unset, AI grouping is skipped. |
| `ANTHROPIC_BASE_URL` | No | Anthropic API | Override endpoint (e.g. litellm proxy). |
| `CLAUDE_MODEL` | No | `claude-sonnet-4-6` | Claude model to use for grouping. |
| `MINIO_ENDPOINT` | No | — | MinIO API URL. If unset, exports are local-only. |
| `MINIO_ACCESS_KEY` | No | `minioadmin` | MinIO access key. |
| `MINIO_SECRET_KEY` | No | `minioadmin` | MinIO secret key. |
| `MINIO_BUCKET` | No | `awscope-exports` | Bucket name for Excel uploads. |
| `DYNAMODB_ENDPOINT` | No | — | DynamoDB Local URL. If unset, pipeline history is disabled. |

## Cache

`~/.awscope/cache.json` — last scan results. Overwritten on every `awscope scan`. Delete and re-scan if the schema changes after an update.

## Project Docs

- [PRD.md](PRD.md) — what it does and why
- [TRD.md](TRD.md) — tech stack, architecture, data model

