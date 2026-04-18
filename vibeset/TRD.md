# VibeSet — Technical Requirements Document

## Platform

macOS-first. Minimum macOS 12 (Monterey). Linux support in v0.2. Windows: never.

## Language and Build

Go. Single static binary. Fast startup (sub-50ms). Distribution via curl install script or Homebrew tap.

## Dependencies

| Package | Purpose |
|---------|---------|
| `cobra` | CLI command structure and flag parsing |
| `viper` | Global config management |
| `go-yaml/yaml` | YML read/write |
| `bubbletea` | Interactive TUI wizard for `vibes create` |
| `lipgloss` | Terminal output styling |

Zero runtime dependencies. Ships as a single binary.

## Directory Layout (User Machine)

```
~/.vibes/
├── config.yml          # global config (default terminal, browser, ide)
├── active              # plaintext: name of current active vibe
├── paused.yml          # snapshot of last paused state
└── envs/
    ├── fampay-infra.yml
    └── safespace.yml
```

## Project Structure

```
vibeset/
├── cmd/
│   ├── root.go         # cobra root, global flags
│   ├── create.go       # vibes create — TUI wizard
│   ├── set.go          # vibes set <name>
│   ├── pause.go        # vibes pause
│   ├── resume.go       # vibes resume
│   ├── list.go         # vibes list
│   ├── edit.go         # vibes edit <name>
│   └── status.go       # vibes status
├── internal/
│   ├── config/
│   │   ├── schema.go   # Go structs matching yml schema
│   │   └── loader.go   # load + validate vibe yml files
│   ├── executor/
│   │   ├── interface.go    # Executor interface
│   │   ├── terminal.go     # wezterm / iterm2 / kitty
│   │   ├── browser.go      # AppleScript browser control
│   │   ├── ide.go          # cursor / vscode / zed
│   │   ├── apps.go         # open / close macOS apps
│   │   └── process.go      # kill named process patterns
│   ├── state/
│   │   ├── active.go       # read/write ~/.vibes/active
│   │   └── pause.go        # pause snapshot serialisation
│   └── wizard/
│       └── create.go       # bubbletea TUI
├── main.go
├── PRD.md
├── TRD.md
└── README.md
```

## Core Interface — Executor

```go
type Executor interface {
    Setup(cfg *config.VibeConfig) error
    Teardown(cfg *config.VibeConfig) error
}
```

## Key Constraints

- SIGTERM only for process teardown, never SIGKILL
- Browser tabs always open in new window
- IDE never force-closed
- All AppleScript isolated in executor files for easy patching
- Schema version field in yml from day one
