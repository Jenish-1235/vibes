package executor

import (
	"fmt"
	"os/exec"
	"strconv"
	"strings"
	"syscall"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
)

type ProcessExecutor struct{}

func (p *ProcessExecutor) Setup(cfg *config.VibeConfig) error {
	// Processes are started by terminal sessions, not directly.
	return nil
}

func (p *ProcessExecutor) Teardown(cfg *config.VibeConfig) error {
	for _, pattern := range cfg.Teardown.KillProcesses {
		if err := killProcessPattern(pattern); err != nil {
			fmt.Printf("warning: could not kill %q: %v\n", pattern, err)
		}
	}
	return nil
}

func killProcessPattern(pattern string) error {
	out, err := exec.Command("pgrep", "-f", pattern).Output()
	if err != nil {
		// pgrep returns exit 1 when no processes match — not an error
		return nil
	}

	for _, pidStr := range strings.Split(strings.TrimSpace(string(out)), "\n") {
		if pidStr == "" {
			continue
		}
		pid, err := strconv.Atoi(pidStr)
		if err != nil {
			continue
		}
		// SIGTERM only — never SIGKILL
		if err := syscall.Kill(pid, syscall.SIGTERM); err != nil {
			fmt.Printf("warning: could not kill pid %d: %v\n", pid, err)
		}
	}
	return nil
}
