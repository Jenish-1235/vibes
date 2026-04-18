package executor

import (
	"fmt"
	"os/exec"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
	"github.com/jenish-1235/vibes/vibeset/internal/state"
)

type GitExecutor struct{}

func (g *GitExecutor) Setup(cfg *config.VibeConfig) error {
	if cfg.Git.Name == "" && cfg.Git.Email == "" {
		return nil
	}
	state.SaveGitRestore() // best-effort; non-fatal if it fails
	if cfg.Git.Name != "" {
		if err := exec.Command("git", "config", "--global", "user.name", cfg.Git.Name).Run(); err != nil {
			return fmt.Errorf("failed to set git user.name: %w", err)
		}
	}
	if cfg.Git.Email != "" {
		if err := exec.Command("git", "config", "--global", "user.email", cfg.Git.Email).Run(); err != nil {
			return fmt.Errorf("failed to set git user.email: %w", err)
		}
	}
	return nil
}

func (g *GitExecutor) Teardown(cfg *config.VibeConfig) error {
	if cfg.Git.Name == "" && cfg.Git.Email == "" {
		return nil
	}
	restore, err := state.LoadGitRestore()
	if err != nil {
		return nil // no backup to restore
	}
	if restore.Name != "" {
		exec.Command("git", "config", "--global", "user.name", restore.Name).Run()
	}
	if restore.Email != "" {
		exec.Command("git", "config", "--global", "user.email", restore.Email).Run()
	}
	state.ClearGitRestore()
	return nil
}
