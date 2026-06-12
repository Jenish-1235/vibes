"""CLI: scan → review → send, plus compose and dm. Run as `python -m twagent`."""

import random
import time

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import prompts
from .config import load_context_doc, load_settings
from .llm import LLM
from .store import Store
from .xapi import TierError, XClient

app = typer.Typer(no_args_is_help=True, help="Twitter/X customer-discovery outreach agent.")
console = Console()


def _setup(need_x: bool = True, need_llm: bool = True):
    try:
        settings = load_settings()
        llm, sysprompt = None, None
        if need_llm:
            context = load_context_doc()
            llm = LLM(settings)
            sysprompt = prompts.system_prompt(context, settings.voice_notes)
        x = XClient(settings) if need_x else None
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    return settings, llm, sysprompt, x, Store()


def _show_item(item: dict) -> None:
    target = item.get("target") or {}
    header = f"[bold]{item['kind'].upper()}[/bold]  id={item['id']}  status={item['status']}"
    body = ""
    if item["kind"] == "reply":
        body += f"[dim]replying to @{target.get('author')}:[/dim]\n[dim]{target.get('tweet_text', '')}[/dim]\n"
        body += f"[dim]relevance {item.get('score')}/10 — {item.get('reason')}[/dim]\n\n"
    elif item["kind"] == "dm":
        body += f"[dim]to @{target.get('username')}[/dim]\n\n"
    body += item["text"]
    console.print(Panel(body, title=header, border_style="cyan"))


@app.command()
def scan(limit: int = typer.Option(None, help="Max tweets to evaluate (default from config)")):
    """Search X for relevant posts, score them, and draft replies into the queue."""
    settings, llm, sysprompt, x, store = _setup()
    limit = limit or settings.scan_max_tweets
    console.print(f"Searching for: [bold]{', '.join(settings.keywords)}[/bold]")
    try:
        tweets = x.search_recent(settings.keywords, limit)
    except TierError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    me = x.me()
    fresh = [t for t in tweets if not store.is_seen(t["tweet_id"]) and t["author_id"] != str(me.id)][:limit]
    console.print(f"{len(tweets)} results, {len(fresh)} new. Scoring...")

    drafted = 0
    for t in fresh:
        store.mark_seen(t["tweet_id"])
        try:
            verdict = llm.complete_json(
                sysprompt, prompts.RELEVANCE_USER.format(author=t["author"], tweet=t["text"]))
            score = int(verdict.get("score", 0))
        except (ValueError, KeyError) as e:
            console.print(f"[yellow]skip {t['tweet_id']}: bad LLM verdict ({e})[/yellow]")
            continue
        if score < settings.relevance_threshold:
            console.print(f"  [dim]@{t['author']} — {score}/10, skipped[/dim]")
            continue
        reply = llm.complete(sysprompt, prompts.REPLY_USER.format(
            author=t["author"], tweet=t["text"], reason=verdict.get("reason", "")))
        item = store.add_item(
            "reply", reply,
            target={"tweet_id": t["tweet_id"], "author": t["author"],
                    "author_id": t["author_id"], "tweet_text": t["text"]},
            score=score, reason=verdict.get("reason"))
        drafted += 1
        _show_item(item)
    store.save()
    console.print(f"\n[green]{drafted} reply drafts queued.[/green] Run [bold]review[/bold] next.")


@app.command()
def compose(n: int = typer.Option(3, help="How many post drafts to generate")):
    """Generate original post drafts from the context document."""
    settings, llm, sysprompt, _, store = _setup(need_x=False)
    out = llm.complete_json(sysprompt, prompts.COMPOSE_USER.format(n=n))
    posts = out.get("posts", [])
    for p in posts:
        _show_item(store.add_item("post", p))
    store.save()
    console.print(f"\n[green]{len(posts)} post drafts queued.[/green] Run [bold]review[/bold] next.")


@app.command()
def dm(handle: str, note: str = typer.Option("", help="Why this person / anything to reference")):
    """Draft a personalized first DM to a specific person."""
    settings, llm, sysprompt, x, store = _setup()
    user = x.get_user(handle)
    note_line = f"Founder's note about why we're reaching out: {note}" if note else ""
    text = llm.complete(sysprompt, prompts.DM_USER.format(
        handle=user["username"], bio=user["bio"], note_line=note_line))
    item = store.add_item("dm", text, target={"user_id": user["id"], "username": user["username"]})
    store.save()
    _show_item(item)
    console.print("\n[green]DM draft queued.[/green] Run [bold]review[/bold] next.")


@app.command()
def review():
    """Approve / edit / reject pending drafts interactively."""
    _, _, _, _, store = _setup(need_x=False, need_llm=False)
    pending = store.items(status="pending")
    if not pending:
        console.print("Nothing pending.")
        return
    for item in pending:
        _show_item(item)
        choice = typer.prompt("[a]pprove / [e]dit / [r]eject / [s]kip", default="s").lower().strip()
        if choice == "a":
            item["status"] = "approved"
        elif choice == "e":
            console.print("[dim]Enter new text (single line):[/dim]")
            item["text"] = typer.prompt("text", default=item["text"])
            item["status"] = "approved"
        elif choice == "r":
            item["status"] = "rejected"
        store.save()
    console.print("\n[green]Review done.[/green] Run [bold]send[/bold] to push approved items.")


@app.command()
def send(dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be sent")):
    """Send approved items through the X API, respecting daily caps and pacing."""
    settings, _, _, x, store = _setup(need_x=not dry_run, need_llm=False)
    approved = sorted(store.items(status="approved"), key=lambda i: i["created_at"])
    if not approved:
        console.print("Nothing approved. Run [bold]review[/bold] first.")
        return

    sent_any = False
    for item in approved:
        kind, cap = item["kind"], settings.caps.for_kind(item["kind"])
        if store.sent_today(kind) >= cap:
            console.print(f"[yellow]Daily cap reached for {kind} ({cap}). Leaving {item['id']} approved for tomorrow.[/yellow]")
            continue
        if dry_run:
            console.print(f"[dim]would send {kind} {item['id']}: {item['text'][:80]}...[/dim]")
            continue
        if sent_any:
            gap = random.randint(settings.min_send_gap_seconds, settings.max_send_gap_seconds)
            console.print(f"[dim]waiting {gap}s...[/dim]")
            time.sleep(gap)
        try:
            if kind == "reply":
                x.post(item["text"], in_reply_to=item["target"]["tweet_id"])
            elif kind == "post":
                x.post(item["text"])
            elif kind == "dm":
                x.send_dm(item["target"]["user_id"], item["text"])
            store.record_sent(item)
            sent_any = True
            console.print(f"[green]sent {kind} {item['id']}[/green]")
        except TierError as e:
            console.print(f"[red]{e}[/red]")
            break
        except Exception as e:
            item["status"] = "failed"
            console.print(f"[red]failed {kind} {item['id']}: {e}[/red]")
        store.save()


@app.command()
def status():
    """Queue counts and today's cap usage."""
    settings, _, _, _, store = _setup(need_x=False, need_llm=False)
    table = Table(title="queue")
    table.add_column("status"); table.add_column("count", justify="right")
    for st in ["pending", "approved", "sent", "rejected", "failed"]:
        table.add_row(st, str(len(store.items(status=st))))
    console.print(table)
    caps = Table(title="today")
    caps.add_column("kind"); caps.add_column("sent / cap", justify="right")
    for kind in ["reply", "post", "dm"]:
        caps.add_row(kind, f"{store.sent_today(kind)} / {settings.caps.for_kind(kind)}")
    console.print(caps)


if __name__ == "__main__":
    app()
