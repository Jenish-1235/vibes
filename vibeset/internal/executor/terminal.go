package executor

import (
	"fmt"
	"os/exec"
	"runtime"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
)

type TerminalExecutor struct{}

func (t *TerminalExecutor) Setup(cfg *config.VibeConfig) error {
	if len(cfg.Terminal.Sessions) == 0 {
		return nil
	}

	tool := cfg.Terminal.Tool
	if tool == "" {
		tool = "wezterm"
	}

	switch tool {
	case "wezterm":
		return setupWezterm(cfg.Terminal.Sessions)
	case "iterm2":
		return setupITerm2(cfg.Terminal.Sessions)
	case "kitty":
		return setupKitty(cfg.Terminal.Sessions)
	default:
		return fmt.Errorf("unsupported terminal: %s", tool)
	}
}

func (t *TerminalExecutor) Teardown(cfg *config.VibeConfig) error {
	// Only kill sessions that had explicit commands (managed processes).
	// Raw shells are never killed per safety rules.
	return nil
}

func setupWezterm(sessions []config.TerminalSession) error {
	for i, s := range sessions {
		var args []string
		if i == 0 {
			args = []string{"cli", "spawn", "--cwd", s.Dir}
		} else {
			args = []string{"cli", "spawn", "--new-tab", "--cwd", s.Dir}
		}

		if err := exec.Command("wezterm", args...).Run(); err != nil {
			return fmt.Errorf("wezterm spawn failed for %q: %w", s.Name, err)
		}

		if s.Command != "" {
			exec.Command("wezterm", "cli", "send-text", "--no-paste", s.Command+"\n").Run()
		}
	}
	return nil
}

func setupITerm2(sessions []config.TerminalSession) error {
	if runtime.GOOS != "darwin" {
		return fmt.Errorf("iterm2 is only supported on macOS")
	}

	for i, s := range sessions {
		var script string
		if i == 0 {
			script = fmt.Sprintf(`tell application "iTerm2"
				create window with default profile
				tell current session of current window
					write text "cd %s"
				end tell
			end tell`, s.Dir)
		} else {
			script = fmt.Sprintf(`tell application "iTerm2"
				tell current window
					create tab with default profile
					tell current session
						write text "cd %s"
					end tell
				end tell
			end tell`, s.Dir)
		}

		if err := exec.Command("osascript", "-e", script).Run(); err != nil {
			return fmt.Errorf("iterm2 setup failed for %q: %w", s.Name, err)
		}

		if s.Command != "" {
			cmdScript := fmt.Sprintf(`tell application "iTerm2"
				tell current session of current window
					write text "%s"
				end tell
			end tell`, s.Command)
			exec.Command("osascript", "-e", cmdScript).Run()
		}
	}
	return nil
}

func setupKitty(sessions []config.TerminalSession) error {
	for i, s := range sessions {
		var args []string
		if i == 0 {
			args = []string{"@", "launch", "--type=tab", "--cwd=" + s.Dir}
		} else {
			args = []string{"@", "launch", "--type=tab", "--cwd=" + s.Dir}
		}

		if s.Command != "" {
			args = append(args, s.Command)
		}

		if err := exec.Command("kitty", args...).Run(); err != nil {
			return fmt.Errorf("kitty launch failed for %q: %w", s.Name, err)
		}
	}
	return nil
}
