package state

import (
	"testing"
)

func TestSaveAndLoadPause(t *testing.T) {
	setupTestHome(t)

	if err := SavePause("paused-vibe"); err != nil {
		t.Fatalf("SavePause failed: %v", err)
	}

	state, err := LoadPause()
	if err != nil {
		t.Fatalf("LoadPause failed: %v", err)
	}
	if state.VibeName != "paused-vibe" {
		t.Errorf("expected 'paused-vibe', got %q", state.VibeName)
	}
}

func TestLoadPause_NoFile(t *testing.T) {
	setupTestHome(t)
	_, err := LoadPause()
	if err == nil {
		t.Fatal("expected error when no pause file exists")
	}
}

func TestClearPause(t *testing.T) {
	setupTestHome(t)

	SavePause("to-clear")
	if err := ClearPause(); err != nil {
		t.Fatalf("ClearPause failed: %v", err)
	}

	_, err := LoadPause()
	if err == nil {
		t.Fatal("expected error after clearing pause")
	}
}

func TestClearPause_NoFile(t *testing.T) {
	setupTestHome(t)
	if err := ClearPause(); err != nil {
		t.Fatalf("ClearPause on missing file failed: %v", err)
	}
}

func TestSavePause_Overwrite(t *testing.T) {
	setupTestHome(t)

	SavePause("first")
	SavePause("second")

	state, err := LoadPause()
	if err != nil {
		t.Fatalf("LoadPause failed: %v", err)
	}
	if state.VibeName != "second" {
		t.Errorf("expected 'second', got %q", state.VibeName)
	}
}
