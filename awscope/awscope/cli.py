from __future__ import annotations

import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="awscope", help="AI-powered AWS resource inventory and grouping dashboard")
console = Console()


# ── init ───────────────────────────────────────────────────────────────────

@app.command()
def init():
    """Interactively add one AWS account alias to config."""
    from awscope.config import AccountConfig, CONFIG_DIR, save_account

    console.print("[bold]Add AWS account alias[/bold]")
    alias = typer.prompt("Alias (e.g. personal, clientx)")

    auth_choices = ["profile", "profile+role", "ambient+role", "static", "sso"]
    console.print("Auth type:")
    for i, c in enumerate(auth_choices, 1):
        console.print(f"  {i}. {c}")
    choice = typer.prompt("Choice", default="1")
    try:
        auth_type = auth_choices[int(choice) - 1]
    except (ValueError, IndexError):
        auth_type = "profile"

    profile = role_arn = role_session_name = external_id = None
    access_key_id = secret_access_key = session_token = None

    if auth_type in ("profile", "profile+role", "sso"):
        profile = typer.prompt("AWS CLI profile name", default="default")

    if auth_type in ("profile+role", "ambient+role"):
        role_arn = typer.prompt("Role ARN")
        role_session_name = typer.prompt("Role session name", default="awscope")
        ext = typer.prompt("External ID (leave blank if none)", default="")
        external_id = ext or None

    if auth_type == "static":
        access_key_id = typer.prompt("AWS Access Key ID")
        secret_access_key = typer.prompt("AWS Secret Access Key", hide_input=True)
        token = typer.prompt("Session token (leave blank if none)", default="")
        session_token = token or None

    account = AccountConfig(
        alias=alias, auth_type=auth_type, profile=profile,
        role_arn=role_arn, role_session_name=role_session_name or "awscope",
        external_id=external_id, access_key_id=access_key_id,
        secret_access_key=secret_access_key, session_token=session_token,
    )
    save_account(account)
    console.print(f"[green]✓[/green] Added account [bold]{alias}[/bold] to {CONFIG_DIR / 'config.toml'}")


# ── import-profiles ────────────────────────────────────────────────────────

@app.command(name="import-profiles")
def import_profiles():
    """Bulk-import AWS CLI profiles from ~/.aws/config."""
    import configparser

    aws_config = Path.home() / ".aws" / "config"
    if not aws_config.exists():
        console.print("[red]~/.aws/config not found[/red]")
        raise typer.Exit(1)

    parser = configparser.ConfigParser()
    parser.read(aws_config)

    profiles = []
    for section in parser.sections():
        name = section.replace("profile ", "").strip()
        if name != "default":
            profiles.append(name)
        elif section == "default":
            profiles.append("default")

    if not profiles:
        console.print("No profiles found in ~/.aws/config")
        raise typer.Exit(0)

    console.print(f"Found {len(profiles)} profile(s):")
    for i, p in enumerate(profiles, 1):
        console.print(f"  {i}. {p}")

    selected = typer.prompt("Enter numbers to import (comma-separated, or 'all')", default="all")

    if selected.strip().lower() == "all":
        chosen = profiles
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selected.split(",")]
            chosen = [profiles[i] for i in indices if 0 <= i < len(profiles)]
        except (ValueError, IndexError):
            console.print("[red]Invalid selection[/red]")
            raise typer.Exit(1)

    from awscope.config import AccountConfig, save_account

    for profile_name in chosen:
        alias = typer.prompt(f"Alias for profile '{profile_name}'", default=profile_name)
        account = AccountConfig(alias=alias, auth_type="profile", profile=profile_name)
        save_account(account)
        console.print(f"[green]✓[/green] Imported [bold]{alias}[/bold]")


# ── accounts ───────────────────────────────────────────────────────────────

@app.command()
def accounts():
    """List configured accounts and check connection status."""
    from awscope.config import build_session, load_config

    try:
        configs = load_config()
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    table = Table(title="Configured Accounts")
    table.add_column("Alias", style="cyan")
    table.add_column("Auth Type")
    table.add_column("Profile")
    table.add_column("Role ARN")
    table.add_column("Status")
    table.add_column("Account ID")

    for acc in configs:
        try:
            session = build_session(acc)
            identity = session.client("sts", region_name="us-east-1").get_caller_identity()
            status = "[green]connected[/green]"
            account_id = identity["Account"]
        except Exception as e:
            status = f"[red]error: {e}[/red]"
            account_id = ""
        table.add_row(acc.alias, acc.auth_type, acc.profile or "", acc.role_arn or "", status, account_id)

    console.print(table)


# ── scan ───────────────────────────────────────────────────────────────────

@app.command()
def scan(
    account_filter: str = typer.Option(None, "--accounts", help="Comma-separated aliases to scan"),
    no_group: bool = typer.Option(False, "--no-group", help="Skip AI grouping"),
):
    """Scan all configured accounts and cache results."""
    from awscope.cache import write_cache
    from awscope.config import build_session, get_anthropic_settings, load_config
    from awscope.grouper import group_resources
    from awscope.models import PipelineRun, ScanResult
    from awscope.scanner import scan_account
    from awscope.store import write_pipeline_run

    try:
        all_configs = load_config()
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    configs = all_configs
    if account_filter:
        wanted = {a.strip() for a in account_filter.split(",")}
        configs = [c for c in all_configs if c.alias in wanted]
        if not configs:
            console.print(f"[red]No matching accounts found for: {account_filter}[/red]")
            raise typer.Exit(1)

    settings = get_anthropic_settings()
    if not no_group and not settings["api_key"]:
        console.print("[yellow]ANTHROPIC_API_KEY not set — skipping AI grouping. Use --no-group to suppress this warning.[/yellow]")
        no_group = True

    run_id = str(uuid.uuid4())
    start_time = time.time()
    scanned_at = datetime.now(timezone.utc).isoformat()
    all_resources = []

    for acc in configs:
        try:
            session = build_session(acc)
            account_id = session.client("sts", region_name="us-east-1").get_caller_identity()["Account"]
        except Exception as e:
            console.print(f"[red]Failed to connect to {acc.alias}: {e}[/red]")
            continue

        console.print(f"[cyan]Scanning {acc.alias} ({account_id})...[/cyan]")
        resources = scan_account(
            session, acc.alias, account_id,
            progress_callback=lambda msg: console.print(f"  {msg}"),
        )
        all_resources.extend(resources)
        console.print(f"  [green]✓[/green] {len(resources)} resources found")

    if not all_resources:
        console.print("[yellow]No resources found.[/yellow]")

    if no_group:
        from awscope.models import ResourceGroup
        groups = [ResourceGroup(group_name="miscellaneous", resources=all_resources)]
        claude_batches = []
    else:
        console.print("[cyan]Grouping resources with Claude...[/cyan]")
        groups, claude_batches = group_resources(
            all_resources,
            progress_callback=lambda msg: console.print(f"  {msg}"),
        )

    duration = time.time() - start_time
    result = ScanResult(
        scanned_at=scanned_at,
        accounts=[c.alias for c in configs],
        resources=all_resources,
        groups=groups,
    )
    write_cache(result)

    pipeline_run = PipelineRun(
        run_id=run_id,
        scanned_at=scanned_at,
        accounts=[c.alias for c in configs],
        total_resources=len(all_resources),
        total_groups=len(groups),
        claude_batches=claude_batches,
        duration_seconds=duration,
    )
    write_pipeline_run(pipeline_run)

    # Summary table
    table = Table(title=f"Scan Complete — {len(all_resources)} resources in {len(groups)} groups")
    table.add_column("Group", style="cyan")
    table.add_column("Resources", justify="right")
    table.add_column("Types")
    table.add_column("Accounts")
    for g in sorted(groups, key=lambda x: x.group_name):
        types = ", ".join(sorted({r.resource_type for r in g.resources}))
        accts = ", ".join(sorted({r.account_alias for r in g.resources}))
        table.add_row(g.group_name, str(len(g.resources)), types[:60], accts)
    console.print(table)
    console.print(f"[dim]Duration: {duration:.1f}s  |  Run ID: {run_id}[/dim]")


# ── list ───────────────────────────────────────────────────────────────────

@app.command(name="list")
def list_groups(
    account_filter: str = typer.Option(None, "--account", help="Filter to one account alias"),
):
    """Print grouped summary from cache."""
    from awscope.cache import read_cache

    try:
        result = read_cache()
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    groups = result.groups
    if account_filter:
        groups = [
            type(g)(group_name=g.group_name, resources=[r for r in g.resources if r.account_alias == account_filter])
            for g in groups
        ]
        groups = [g for g in groups if g.resources]

    table = Table(title=f"Resource Groups (scanned {result.scanned_at})")
    table.add_column("Group", style="cyan")
    table.add_column("Resources", justify="right")
    table.add_column("Resource Types")
    table.add_column("Accounts")
    table.add_column("Regions")
    for g in sorted(groups, key=lambda x: x.group_name):
        types = ", ".join(sorted({r.resource_type for r in g.resources}))
        accts = ", ".join(sorted({r.account_alias for r in g.resources}))
        regions = ", ".join(sorted({r.region for r in g.resources}))
        table.add_row(g.group_name, str(len(g.resources)), types[:50], accts, regions[:30])
    console.print(table)


# ── show ───────────────────────────────────────────────────────────────────

@app.command()
def show(group: str = typer.Argument(..., help="Group name to inspect")):
    """Print all resources in a group."""
    from awscope.cache import read_cache

    try:
        result = read_cache()
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    matched = next((g for g in result.groups if g.group_name.lower() == group.lower()), None)
    if not matched:
        console.print(f"[red]Group '{group}' not found.[/red]")
        console.print("Available groups: " + ", ".join(g.group_name for g in result.groups))
        raise typer.Exit(1)

    table = Table(title=f"Group: {matched.group_name} ({len(matched.resources)} resources)")
    table.add_column("Name", style="cyan")
    table.add_column("Type")
    table.add_column("Region")
    table.add_column("Account")
    table.add_column("Status")
    table.add_column("ARN")
    for r in sorted(matched.resources, key=lambda x: (x.resource_type, x.name)):
        table.add_row(r.name, r.resource_type, r.region, r.account_alias, r.status, r.arn[:60])
    console.print(table)


# ── export ─────────────────────────────────────────────────────────────────

@app.command()
def export(
    output: str = typer.Option(None, "--output", help="Output file path"),
):
    """Export audit report to Excel (.xlsx)."""
    from datetime import datetime
    from awscope.cache import read_cache
    from awscope.exporter import build_excel
    from awscope.object_store import upload_export

    try:
        result = read_cache()
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    if not output:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"awscope_export_{ts}.xlsx"

    buf = build_excel(result)

    with open(output, "wb") as f:
        f.write(buf.getvalue())
    console.print(f"[green]✓[/green] Exported to [bold]{output}[/bold]")

    ts_path = datetime.now().strftime("%Y-%m-%d")
    object_key = f"exports/{ts_path}/{Path(output).name}"
    url = upload_export(buf, object_key)
    if url:
        console.print(f"[dim]Uploaded to MinIO: {url}[/dim]")


# ── web ────────────────────────────────────────────────────────────────────

@app.command()
def web(
    port: int = typer.Option(8080, "--port"),
    host: str = typer.Option("127.0.0.1", "--host"),
):
    """Start the local web dashboard."""
    import uvicorn
    console.print(f"[cyan]Starting awscope web on http://{host}:{port}[/cyan]")
    uvicorn.run("awscope.web:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
