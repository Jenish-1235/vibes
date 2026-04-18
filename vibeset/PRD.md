# VibeSet — Product Requirements Document

## Problem Statement

Engineers working across multiple projects lose 10–15 minutes per context switch reconstructing their environment — reopening tabs, finding IDE windows, restarting terminal sessions, remembering which tools were running. Multiplied by 4–5 switches a day, that's a real hour of dead time daily.

Nothing ties all of it together under a single named environment with one CLI command.

## Core Mental Model

A **vibe** is a named snapshot of your complete working environment. `vibes set <name>` is a teleport — you leave one context completely and arrive in another, fully set up.

## Target Users

- Engineers working across 2+ active projects simultaneously
- Freelancers and agency devs switching between client contexts
- Students juggling internship + college + side projects
- Anyone who has ever lost 10 minutes reconstructing "where was I"

## Commands

| Command | Description |
|---------|-------------|
| `vibes create` | Interactive wizard — collects tools, tabs, paths, produces `<name>.yml` |
| `vibes set <name>` | Tears down current vibe, sets up named vibe |
| `vibes pause` | Snapshot current state and teardown |
| `vibes resume` | Restore last paused vibe |
| `vibes list` | Show all defined vibes + last used timestamp |
| `vibes edit <name>` | Open yml in `$EDITOR` |
| `vibes status` | Show currently active vibe |

## Teardown Safety Rules

- Terminal sessions — kill only if a `command` was set. Raw shells never killed.
- IDE windows — never force-closed.
- Browser — open tabs in new window. Never close existing unless `aggressive_teardown: true`.
- Apps in `close` list — graceful quit only. Never `kill -9`.
- Unsaved work — tool has no mechanism to force-close anything with unsaved state.

## Explicit Non-Goals

- No Windows support (ever)
- No Linux in v0 (v0.2)
- No cloud sync of vibe configs
- No GUI configuration editor — yml is the config
- No automatic environment detection
- No plugin system in v0
- No Electron or any GUI app in v0

## Success Criteria

Context switch time drops from ~15 minutes to under 30 seconds. At least 3 friends install it without being asked twice.
