# VibeSet

Named environment snapshots for your full dev setup — terminals, browser tabs, IDE windows, apps — switched with one command.

## Status: 🚧 In progress

## What it does

- Define named "vibes" as YML files describing your full working environment
- `vibes set <name>` tears down current context and sets up the target one
- Supports WezTerm, Chrome, Cursor/VSCode, and macOS app management

## Tech Stack

- Go, single static binary
- Cobra (CLI), Viper (config), Bubbletea (TUI), Lipgloss (styling)
- macOS-first (AppleScript for browser/app control)

## Quick Start

```bash
cd vibeset/
go build -o vibes .
./vibes create        # interactive wizard
./vibes set my-project
./vibes list
./vibes status
```

## Project Structure

See [TRD.md](TRD.md) for full architecture details.
