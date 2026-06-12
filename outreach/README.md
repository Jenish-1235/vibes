# outreach

CLI agent that runs my Twitter/X customer-discovery motion: finds relevant
posts and drafts replies, composes original posts in my voice, drafts
personalized DMs — all from one context document — then sends what I approve
through the official X API. LLM calls go through litellm, so it works with a
LiteLLM proxy key or an Azure AI Studio key.

See `PRD.md` for what/why and `TRD.md` for how. Read both before changing code.

## Setup

```bash
cd outreach/agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in LLM + X credentials
$EDITOR context/PRODUCT.md  # ← the important part. The agent is only as good as this doc.
$EDITOR config.yaml         # keywords, daily caps, voice notes
```

X app requirements: a developer.x.com app with **Read + Write** permissions
(plus **Direct Messages** for DMs). Regenerate the access token *after*
setting permissions. `scan` and `dm` need the **Basic (paid)** API tier;
`compose` + `send` of original posts work on Free.

## Daily loop

```bash
python -m twagent scan                 # find relevant tweets, draft replies
python -m twagent compose -n 3        # draft original posts
python -m twagent dm somehandle --note "complained about X yesterday"
python -m twagent review              # approve / edit / reject each draft
python -m twagent send                # push approved items (or --dry-run)
python -m twagent status              # queue + today's caps
```

## How it behaves (deliberate)

- **Nothing goes out without passing `review`.** The agent drafts; you approve.
- Daily caps (10 replies / 4 posts / 5 DMs by default) and randomized 45–120 s
  gaps between sends keep the account looking like a person, because it is one.
- DMs are drafted one person at a time with a reason — there is no bulk-DM
  mode, and that's intentional (X automation rules; also bulk DMs don't book
  calls, they get you blocked).
- Never replies to the same tweet twice (`data/queue.json` tracks seen ids).

## Known limitations

- `review` editing is single-line input; for serious rewrites, edit
  `data/queue.json` directly or reject and re-draft.
- Relevance scoring is one LLM call per tweet — keep `scan_max_tweets` modest.
- No thread support yet (posts are single tweets).
- State is one JSON file; don't run two commands concurrently.
