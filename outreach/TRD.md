# TRD — outreach

## Stack

- **Python 3.10+** — single package, no framework.
- **litellm** — LLM calls. One `completion()` interface covers both supported
  backends:
  - LiteLLM proxy: `LLM_API_BASE` + `LLM_API_KEY` + any model name the proxy routes.
  - Azure AI Studio / Azure OpenAI: model string `azure/<deployment-name>` +
    `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION`.
- **tweepy** — official X API v2 client (OAuth 1.0a user context for write
  actions; bearer token for search).
- **typer + rich** — CLI and the interactive review UI.
- **python-dotenv, pyyaml** — secrets in `.env`, behavior in `config.yaml`.

No database. No background daemon. No shared code with other projects.

## X API tier reality check

| Capability | Endpoint | Minimum tier |
|---|---|---|
| Post tweet / reply | `POST /2/tweets` | Free |
| Recent search (`scan`) | `GET /2/tweets/search/recent` | Basic (paid) |
| Send DM | `POST /2/dm_conversations/...` | Basic (paid) |

On the Free tier only `compose` + `send` (original posts) work. `scan` and `dm`
need Basic. The code surfaces a clear error instead of failing cryptically.

## Architecture

```
outreach/agent/
├── requirements.txt
├── .env.example            ← all secrets, copy to .env
├── config.yaml             ← keywords, caps, voice notes, model name
├── context/PRODUCT.md      ← THE context document (user-written)
├── data/queue.json         ← created at runtime, gitignored
└── twagent/
    ├── __init__.py
    ├── config.py           ← env + yaml loading, validated dataclasses
    ├── llm.py              ← litellm wrapper: complete(), complete_json()
    ├── xapi.py             ← tweepy wrapper: search, reply, post, dm
    ├── prompts.py          ← system prompt from context doc + task templates
    ├── store.py            ← JSON queue + seen-ids + daily send counters
    └── cli.py              ← typer commands: scan, compose, dm, review, send, status
```

## Data model (`data/queue.json`)

```json
{
  "seen_tweet_ids": ["..."],
  "sent_log": {"2026-06-12": {"reply": 3, "post": 1, "dm": 1}},
  "items": [
    {
      "id": "uuid",
      "kind": "reply | post | dm",
      "status": "pending | approved | rejected | sent | failed",
      "text": "draft text",
      "target": {"tweet_id": "...", "author": "handle", "tweet_text": "..."},
      "score": 8,
      "reason": "why the LLM thought this was relevant",
      "created_at": "iso8601",
      "sent_at": "iso8601 | null"
    }
  ]
}
```

Plain JSON on disk, rewritten atomically (write temp + rename). At this volume
(tens of items/day) anything more is overengineering.

## Command flow

- `scan` — search recent tweets for configured keywords (excluding RTs, own
  tweets, already-seen ids) → one LLM relevance pass per tweet returning
  `{score, reason}` JSON → for tweets ≥ threshold, draft a reply → queue as
  `pending`.
- `compose [-n N]` — generate N original-post drafts from the context doc →
  queue as `pending`.
- `dm <handle> [--note "..."]` — look up user, draft a personalized DM
  (optionally seeded with a note about why this person) → queue as `pending`.
- `review` — interactive: show each pending item, `[a]pprove / [e]dit /
  [r]eject / [s]kip`.
- `send [--dry-run]` — push approved items through the X API oldest-first,
  enforcing per-kind daily caps and a randomized 45–120 s gap between sends.
  DMs are only ever created via per-person drafting and individual review —
  there is no bulk-DM path by design.
- `status` — queue counts and today's caps usage.

## Safety / account-health decisions (deliberate, re-read before changing)

- **Review-before-send is the default for everything.** `send` only touches
  items explicitly approved in `review`.
- **Daily caps** (config, defaults: 10 replies, 4 posts, 5 DMs) — keeps volume
  inside what a human plausibly does and well inside X automation rules.
- **Randomized inter-send delay** — no machine-gun posting.
- **Seen-ids set** — never reply to the same tweet twice.
- The LLM prompt explicitly instructs against fake claims, manufactured
  urgency, and @-mention spam; the CTA is "would love 15 min to hear how you
  handle X", not a pitch.

## Auth & secrets

`.env` (gitignored):

```
# LLM — option A: LiteLLM proxy
LLM_MODEL=...           # e.g. gpt-4o or whatever the proxy routes
LLM_API_BASE=...
LLM_API_KEY=...

# LLM — option B: Azure AI Studio (set LLM_MODEL=azure/<deployment>)
AZURE_API_KEY=...
AZURE_API_BASE=...
AZURE_API_VERSION=2024-08-01-preview

# X API (developer.x.com app with read/write/DM permissions)
X_BEARER_TOKEN=...
X_API_KEY=...
X_API_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_TOKEN_SECRET=...
```
