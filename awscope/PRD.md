# awscope — Product Requirements Document

## Problem Statement

Running multiple AWS accounts — personal, client, side-project — means resources sprawl invisibly across regions and services. There is no native AWS tool that answers the question: "What is actually deployed across all my accounts, and what does each resource belong to?" The AWS Console requires manual account-switching, per-region navigation, and per-service drilling. It is not built for the audit question.

`awscope` answers that question. It scans all your AWS accounts in one shot, uses Claude to semantically group resources by product or service name (not just by tags), and presents the result in a clean CLI and local web dashboard — with Excel export for sharing or archiving the audit.

---

## Target User

A single engineer who:
- Manages 2–5 AWS accounts (personal, client, or project)
- Has AWS CLI configured with named profiles for each account
- Wants to periodically audit "what's running and what does it belong to"
- Occasionally needs to share a resource inventory with a client or stakeholder as an Excel file
- Does not want to log into the AWS Console across multiple accounts to answer this question

---

## Core Mental Model

**Account → Product → Resources.**

Resources belong to a product. A product is identified by its name — found in the resource name, resource tags, or both. Claude determines group membership using semantic understanding, not just exact tag matching. The result is a clean, grouped inventory tree.

Example: EC2 instances named `hagrid-api`, `hagrid-worker`, `hagrid-prod` plus an RDS instance named `hagrid-db` and an S3 bucket `hagrid-assets` → all grouped under **hagrid**.

---

## User Flows

### Flow 1 — First-time setup
`awscope init` → prompted for alias name + AWS CLI profile name → saved to `~/.awscope/config.toml`. Repeat for each additional account.

### Flow 2 — Scanning and browsing (CLI)
`awscope scan` → connects to each configured account → scans all enabled regions → collects all running resources → sends batches to Claude → groups by product name → caches to `~/.awscope/cache.json` → prints grouped summary table.

`awscope list` → reads cached results → prints grouped summary: Group | Resource Count | Services | Accounts.

`awscope show <group>` → prints all resources in that group: Name | Type | ARN | Region | Account | Status | Tags.

### Flow 3 — Exporting (CLI)
`awscope export` → writes `awscope_export_<timestamp>.xlsx` to current directory → prints confirmation with file path.

### Flow 4 — Web dashboard
`awscope web` → starts local server on `localhost:8080` → open browser → left sidebar shows group names → click a group to see its resources as cards → header shows last scan timestamp → "Export to Excel" button at top right triggers file download.

### Flow 5 — Re-scan
Re-run `awscope scan` at any time. Cache is overwritten. Web dashboard reflects new data on next page reload.

---

## Interfaces

### CLI (terminal)
- `scan`: Progress lines per account/region with spinner, then grouped summary Rich table
- `list`: Grouped summary table from cache
- `show <group>`: Per-resource detail table
- `export`: Confirmation line with output file path

### Web dashboard
- Header: "awscope — last scanned: \<timestamp\>"
- Left sidebar: list of group names, click to filter
- Main area: resource cards for the selected group — name, type, region, account alias, status, ARN, tags
- Top-right: "Export to Excel" button (triggers `.xlsx` download)
- Plain HTML + vanilla JS. No login, no build step, localhost only.

---

## Explicit Non-Goals

- No cloud sync — all data is local to the machine running awscope
- No cost data or billing analysis (planned for a later version)
- No resource modification — read-only audit only; no start/stop/delete
- No real-time updates — scanning is a manual, on-demand action
- No authentication on the web interface — localhost only, single user
- No multi-user or team features
- No alerts, notifications, or scheduled scans
- No Terraform / IaC integration
- No iOS or Android

---

## Success Criteria

Run `awscope scan && awscope web` and answer "What is running across all my AWS accounts, and what does each resource belong to?" in under 5 minutes — without opening the AWS Console.
