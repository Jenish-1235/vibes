package executor

import (
	"testing"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
)

func TestAllExecutors_ReturnsAll(t *testing.T) {
	executors := AllExecutors()
	if len(executors) != 5 {
		t.Fatalf("expected 5 executors, got %d", len(executors))
	}

	// Verify types
	types := map[string]bool{}
	for _, ex := range executors {
		switch ex.(type) {
		case *ProcessExecutor:
			types["process"] = true
		case *AppExecutor:
			types["app"] = true
		case *TerminalExecutor:
			types["terminal"] = true
		case *BrowserExecutor:
			types["browser"] = true
		case *IDEExecutor:
			types["ide"] = true
		}
	}
	for _, name := range []string{"process", "app", "terminal", "browser", "ide"} {
		if !types[name] {
			t.Errorf("missing executor type: %s", name)
		}
	}
}

func TestExecutors_SetupNoOp_EmptyConfig(t *testing.T) {
	cfg := &config.VibeConfig{}

	for _, ex := range AllExecutors() {
		if err := ex.Setup(cfg); err != nil {
			t.Errorf("Setup should be no-op for empty config, got error: %v", err)
		}
	}
}

func TestExecutors_TeardownNoOp_EmptyConfig(t *testing.T) {
	cfg := &config.VibeConfig{}

	for _, ex := range AllExecutors() {
		if err := ex.Teardown(cfg); err != nil {
			t.Errorf("Teardown should be no-op for empty config, got error: %v", err)
		}
	}
}
