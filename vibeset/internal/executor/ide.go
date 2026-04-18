package executor

import (
	"fmt"
	"os/exec"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
)

type IDEExecutor struct{}

func (e *IDEExecutor) Setup(cfg *config.VibeConfig) error {
	if len(cfg.IDE.Windows) == 0 {
		return nil
	}

	tool := cfg.IDE.Tool
	if tool == "" {
		tool = "cursor"
	}

	bin, err := ideBinary(tool)
	if err != nil {
		return err
	}

	for _, w := range cfg.IDE.Windows {
		if err := exec.Command(bin, w.Path).Start(); err != nil {
			return fmt.Errorf("failed to open %s at %q: %w", tool, w.Path, err)
		}
	}
	return nil
}

func (e *IDEExecutor) Teardown(cfg *config.VibeConfig) error {
	// IDE windows are never force-closed per safety rules.
	return nil
}

func ideBinary(tool string) (string, error) {
	switch tool {
	case "cursor":
		return "cursor", nil
	case "vscode", "code":
		return "code", nil
	case "zed":
		return "zed", nil
	case "idea":
		return "idea", nil
	default:
		return "", fmt.Errorf("unsupported IDE: %s", tool)
	}
}
