# PRD — outreach

## Problem

I'm running customer discovery for a product. The people I need to talk to are on
Twitter/X, but showing up there consistently is a grind: finding relevant
conversations, writing replies that don't sound like a sales bot, keeping my own
account active with content, and following up with promising people in DMs to get
them on a discovery call. Doing this manually eats hours every day; not doing it
means zero pipeline.

## What it does

A CLI agent that runs from my machine, reads a context document describing what
I'm building and who I'm trying to reach, and then:

1. **Scans** X for recent posts matching my keywords, scores each one for
   relevance with an LLM, and drafts a reply for the good ones.
2. **Composes** original posts (takes, threads-of-one, build-in-public updates)
   in my voice from the context doc.
3. **Drafts DMs** to specific people I point it at, with the goal of opening a
   conversation that leads to a discovery call.
4. **Queues everything for my review.** I approve, edit, or reject each draft in
   the terminal, then the agent sends the approved batch through the official X
   API with daily caps and randomized pacing.

The LLM side runs through litellm, so it works with my LiteLLM proxy key or my
Azure AI Studio key interchangeably — just config.

## Core loop

```
edit context/PRODUCT.md  →  scan / compose / dm  →  review  →  send
```

## Goals

- One context document is the single source of truth for voice, product, ICP,
  and the call-to-action (the discovery-call ask).
- Drafts that sound like me and add something to the conversation, not
  "Great post! Check out my tool 👇".
- Everything outbound is visible and editable before it leaves my account.
- Daily caps so the account behaves like a person, not a firehose.

## Non-goals (guardrails, not oversights)

- **No mass unsolicited DM blasts.** DMs are drafted per-person, reviewed
  individually, and capped per day. X's automation rules prohibit bulk
  unsolicited DMs and that's a fast way to lose the account.
- **No engagement farming** — no follow/unfollow churn, no auto-likes, no reply
  spam on trending posts.
- **No scraping or unofficial APIs.** Official X API v2 only.
- No web dashboard, no multi-account support, no scheduling service. It's a CLI
  I run when I'm working.

## Success criteria

v0 is done when I can go from a fresh context doc to an approved-and-sent batch
of replies + one original post + one DM draft in a single sitting, without
touching the X website except to read responses.
