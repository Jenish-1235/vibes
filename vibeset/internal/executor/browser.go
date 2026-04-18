package executor

import (
	"fmt"
	"os/exec"
	"runtime"
	"strings"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
)

type BrowserExecutor struct{}

func (b *BrowserExecutor) Setup(cfg *config.VibeConfig) error {
	if len(cfg.Browser.Tabs) == 0 {
		return nil
	}

	tool := cfg.Browser.Tool
	if tool == "" {
		tool = "chrome"
	}

	profile := cfg.Browser.Profile

	switch tool {
	case "chrome":
		return openTabsChrome(cfg.Browser.Tabs, profile)
	case "arc":
		return openTabsArc(cfg.Browser.Tabs, profile)
	case "firefox":
		return openTabsFirefox(cfg.Browser.Tabs, profile)
	default:
		return fmt.Errorf("unsupported browser: %s", tool)
	}
}

func (b *BrowserExecutor) Teardown(cfg *config.VibeConfig) error {
	// Browser tabs are never closed unless aggressive_teardown is set.
	// That's a v0.3 feature.
	return nil
}

func openTabsChrome(tabs []string, profile string) error {
	if runtime.GOOS != "darwin" {
		return openTabsGeneric("google-chrome", tabs)
	}

	if profile != "" {
		// Profile-aware: use CLI to open Chrome with a specific profile directory.
		// Profile names match Chrome's internal directory names: "Default", "Profile 1", "Work", etc.
		args := []string{"-a", "Google Chrome", "--args", "--new-window", "--profile-directory=" + profile}
		args = append(args, tabs...)
		return exec.Command("open", args...).Run()
	}

	var sb strings.Builder
	sb.WriteString(`tell application "Google Chrome"
	activate
	make new window
	set URL of active tab of front window to "`)
	sb.WriteString(tabs[0])
	sb.WriteString(`"`)

	for _, tab := range tabs[1:] {
		sb.WriteString(fmt.Sprintf(`
	tell front window to make new tab with properties {URL:"%s"}`, tab))
	}

	sb.WriteString(`
end tell`)

	return exec.Command("osascript", "-e", sb.String()).Run()
}

func openTabsArc(tabs []string, profile string) error {
	if runtime.GOOS != "darwin" {
		return fmt.Errorf("arc browser is only supported on macOS")
	}

	// Arc uses "Spaces" as profiles. There is no reliable public CLI API for
	// targeting a specific Space, so the profile field is intentionally ignored here.
	var sb strings.Builder
	sb.WriteString(`tell application "Arc"
	activate
	make new window`)

	for _, tab := range tabs {
		sb.WriteString(fmt.Sprintf(`
	tell front window to make new tab with properties {URL:"%s"}`, tab))
	}

	sb.WriteString(`
end tell`)

	return exec.Command("osascript", "-e", sb.String()).Run()
}

func openTabsFirefox(tabs []string, profile string) error {
	if runtime.GOOS != "darwin" {
		return openTabsGeneric("firefox", tabs)
	}

	args := []string{"-a", "Firefox", "--args", "--new-window"}
	if profile != "" {
		args = append(args, "-P", profile)
	}
	args = append(args, tabs[0])
	if err := exec.Command("open", args...).Run(); err != nil {
		return err
	}

	for _, tab := range tabs[1:] {
		exec.Command("open", "-a", "Firefox", "--args", "--new-tab", tab).Run()
	}
	return nil
}

func openTabsGeneric(browser string, tabs []string) error {
	// Linux fallback: use xdg-open or direct browser command
	for _, tab := range tabs {
		if err := exec.Command(browser, tab).Start(); err != nil {
			return fmt.Errorf("failed to open tab %q: %w", tab, err)
		}
	}
	return nil
}
