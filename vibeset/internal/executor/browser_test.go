package executor

import (
	"testing"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
)

func TestBrowserExecutor_Setup_UnsupportedTool(t *testing.T) {
	ex := &BrowserExecutor{}
	cfg := &config.VibeConfig{
		Browser: config.BrowserConfig{
			Tool: "unknown-browser",
			Tabs: []string{"https://example.com"},
		},
	}

	err := ex.Setup(cfg)
	if err == nil {
		t.Error("expected error for unsupported browser")
	}
}

func TestBrowserExecutor_Setup_NoTabs(t *testing.T) {
	ex := &BrowserExecutor{}
	cfg := &config.VibeConfig{
		Browser: config.BrowserConfig{
			Tool: "chrome",
		},
	}

	err := ex.Setup(cfg)
	if err != nil {
		t.Errorf("expected no error for empty tabs, got: %v", err)
	}
}

func TestBrowserExecutor_Teardown_AlwaysNoOp(t *testing.T) {
	ex := &BrowserExecutor{}
	cfg := &config.VibeConfig{
		Browser: config.BrowserConfig{
			Tool: "chrome",
			Tabs: []string{"https://example.com"},
		},
	}

	err := ex.Teardown(cfg)
	if err != nil {
		t.Errorf("teardown should be no-op, got: %v", err)
	}
}
