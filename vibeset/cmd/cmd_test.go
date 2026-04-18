package cmd

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func setupCmdTestHome(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	t.Setenv("HOME", dir)
	envsDir := filepath.Join(dir, ".vibes", "envs")
	os.MkdirAll(envsDir, 0755)
	return dir
}

func TestHumanTime(t *testing.T) {
	tests := []struct {
		name     string
		offset   time.Duration
		expected string
	}{
		{"just now", 10 * time.Second, "just now"},
		{"minutes", 5 * time.Minute, "5m ago"},
		{"hours", 3 * time.Hour, "3h ago"},
		{"days", 48 * time.Hour, time.Now().Add(-48 * time.Hour).Format("Jan 02")},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			result := humanTime(time.Now().Add(-tc.offset))
			if result != tc.expected {
				t.Errorf("humanTime(%v ago) = %q, want %q", tc.offset, result, tc.expected)
			}
		})
	}
}

func TestRunStatus_NoActiveVibe(t *testing.T) {
	setupCmdTestHome(t)
	err := runStatus(nil, nil)
	if err != nil {
		t.Errorf("runStatus should not error when no active vibe: %v", err)
	}
}

func TestRunList_NoVibes(t *testing.T) {
	setupCmdTestHome(t)
	err := runList(nil, nil)
	if err != nil {
		t.Errorf("runList should not error with no vibes: %v", err)
	}
}

func TestRunList_WithVibes(t *testing.T) {
	home := setupCmdTestHome(t)
	envsDir := filepath.Join(home, ".vibes", "envs")
	os.WriteFile(filepath.Join(envsDir, "test.yml"), []byte("name: test"), 0644)

	err := runList(nil, nil)
	if err != nil {
		t.Errorf("runList should not error: %v", err)
	}
}

func TestRunSet_VibeNotFound(t *testing.T) {
	setupCmdTestHome(t)
	err := runSet(nil, []string{"nonexistent"})
	if err == nil {
		t.Error("expected error for nonexistent vibe")
	}
}

func TestRunResume_NoPausedVibe(t *testing.T) {
	setupCmdTestHome(t)
	err := runResume(nil, nil)
	if err != nil {
		t.Errorf("runResume should not error when no paused vibe: %v", err)
	}
}

func TestRunPause_NoActiveVibe(t *testing.T) {
	setupCmdTestHome(t)
	err := runPause(nil, nil)
	if err != nil {
		t.Errorf("runPause should not error when no active vibe: %v", err)
	}
}

func TestRunEdit_VibeNotFound(t *testing.T) {
	setupCmdTestHome(t)
	err := runEdit(nil, []string{"nonexistent"})
	if err == nil {
		t.Error("expected error for nonexistent vibe")
	}
}
