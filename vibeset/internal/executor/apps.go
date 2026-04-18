package executor

import (
	"fmt"
	"os/exec"
	"runtime"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
)

type AppExecutor struct{}

func (a *AppExecutor) Setup(cfg *config.VibeConfig) error {
	for _, app := range cfg.Apps.Open {
		if err := openApp(app); err != nil {
			return fmt.Errorf("failed to open %q: %w", app, err)
		}
	}
	return nil
}

func (a *AppExecutor) Teardown(cfg *config.VibeConfig) error {
	for _, app := range cfg.Apps.Close {
		if err := closeApp(app); err != nil {
			// Log but don't fail — app might already be closed
			fmt.Printf("warning: could not close %q: %v\n", app, err)
		}
	}

	for _, app := range cfg.Teardown.CloseApps {
		if err := closeApp(app); err != nil {
			fmt.Printf("warning: could not close %q: %v\n", app, err)
		}
	}
	return nil
}

func openApp(name string) error {
	if runtime.GOOS == "darwin" {
		return exec.Command("open", "-a", name).Run()
	}
	// Linux fallback
	return exec.Command(name).Start()
}

func closeApp(name string) error {
	if runtime.GOOS == "darwin" {
		// Graceful quit via AppleScript — never kill -9
		script := fmt.Sprintf(`tell application "%s" to quit`, name)
		return exec.Command("osascript", "-e", script).Run()
	}
	// Linux fallback: pkill with SIGTERM
	return exec.Command("pkill", "-f", name).Run()
}
