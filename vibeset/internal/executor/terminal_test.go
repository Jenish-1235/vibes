package executor

import (
	"testing"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
)

func TestTerminalExecutor_Setup_UnsupportedTool(t *testing.T) {
	ex := &TerminalExecutor{}
	cfg := &config.VibeConfig{
		Terminal: config.TerminalConfig{
			Tool: "unknown-terminal",
			Sessions: []config.TerminalSession{
				{Name: "test", Dir: "/tmp"},
			},
		},
	}

	err := ex.Setup(cfg)
	if err == nil {
		t.Error("expected error for unsupported terminal tool")
	}
}

func TestTerminalExecutor_Setup_NoSessions(t *testing.T) {
	ex := &TerminalExecutor{}
	cfg := &config.VibeConfig{
		Terminal: config.TerminalConfig{
			Tool: "wezterm",
		},
	}

	err := ex.Setup(cfg)
	if err != nil {
		t.Errorf("expected no error for empty sessions, got: %v", err)
	}
}

func TestTerminalExecutor_Teardown_AlwaysNoOp(t *testing.T) {
	ex := &TerminalExecutor{}
	cfg := &config.VibeConfig{
		Terminal: config.TerminalConfig{
			Tool: "wezterm",
			Sessions: []config.TerminalSession{
				{Name: "test", Dir: "/tmp", Command: "echo hello"},
			},
		},
	}

	err := ex.Teardown(cfg)
	if err != nil {
		t.Errorf("teardown should be no-op, got: %v", err)
	}
}

func TestTerminalExecutor_Setup_DefaultsTool(t *testing.T) {
	ex := &TerminalExecutor{}
	cfg := &config.VibeConfig{
		Terminal: config.TerminalConfig{
			Sessions: []config.TerminalSession{
				{Name: "test", Dir: "/tmp"},
			},
		},
	}

	// Will fail because wezterm isn't installed in CI, but the error
	// should be a wezterm error, not "unsupported terminal"
	err := ex.Setup(cfg)
	if err == nil {
		return // wezterm happened to be installed
	}
	// Should have attempted wezterm (the default), not failed with "unsupported"
	if err.Error() == "unsupported terminal: " {
		t.Error("should default to wezterm, not empty tool")
	}
}
