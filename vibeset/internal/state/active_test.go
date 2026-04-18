package state

import (
	"os"
	"path/filepath"
	"testing"
)

func setupTestHome(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	t.Setenv("HOME", dir)
	os.MkdirAll(filepath.Join(dir, ".vibes"), 0755)
	return dir
}

func TestGetActive_NoFile(t *testing.T) {
	setupTestHome(t)
	name, err := GetActive()
	if err != nil {
		t.Fatalf("GetActive failed: %v", err)
	}
	if name != "" {
		t.Errorf("expected empty, got %q", name)
	}
}

func TestSetAndGetActive(t *testing.T) {
	setupTestHome(t)

	if err := SetActive("my-vibe"); err != nil {
		t.Fatalf("SetActive failed: %v", err)
	}

	name, err := GetActive()
	if err != nil {
		t.Fatalf("GetActive failed: %v", err)
	}
	if name != "my-vibe" {
		t.Errorf("expected 'my-vibe', got %q", name)
	}
}

func TestSetActive_Overwrite(t *testing.T) {
	setupTestHome(t)

	SetActive("first")
	SetActive("second")

	name, _ := GetActive()
	if name != "second" {
		t.Errorf("expected 'second', got %q", name)
	}
}

func TestClearActive(t *testing.T) {
	setupTestHome(t)

	SetActive("to-clear")
	if err := ClearActive(); err != nil {
		t.Fatalf("ClearActive failed: %v", err)
	}

	name, _ := GetActive()
	if name != "" {
		t.Errorf("expected empty after clear, got %q", name)
	}
}

func TestClearActive_NoFile(t *testing.T) {
	setupTestHome(t)
	// Should not error when there's nothing to clear
	if err := ClearActive(); err != nil {
		t.Fatalf("ClearActive on missing file failed: %v", err)
	}
}
