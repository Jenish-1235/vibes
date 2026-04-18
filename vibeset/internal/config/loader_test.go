package config

import (
	"os"
	"path/filepath"
	"testing"
)

func setupTestVibesDir(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	t.Setenv("HOME", dir)
	envsDir := filepath.Join(dir, ".vibes", "envs")
	if err := os.MkdirAll(envsDir, 0755); err != nil {
		t.Fatal(err)
	}
	return dir
}

func TestLoadVibe_ValidFile(t *testing.T) {
	home := setupTestVibesDir(t)
	yml := `
schema_version: 1
name: test-vibe
description: "A test vibe"
terminal:
  tool: wezterm
  sessions:
    - name: dev
      dir: ~/projects/test
      command: npm run dev
browser:
  tool: chrome
  tabs:
    - https://example.com
ide:
  tool: cursor
  windows:
    - path: ~/projects/test
apps:
  open:
    - Slack
  close:
    - Spotify
teardown:
  kill_processes:
    - "node server"
  close_apps:
    - TablePlus
`
	path := filepath.Join(home, ".vibes", "envs", "test-vibe.yml")
	if err := os.WriteFile(path, []byte(yml), 0644); err != nil {
		t.Fatal(err)
	}

	cfg, err := LoadVibe("test-vibe")
	if err != nil {
		t.Fatalf("LoadVibe failed: %v", err)
	}

	if cfg.Name != "test-vibe" {
		t.Errorf("expected name 'test-vibe', got %q", cfg.Name)
	}
	if cfg.Description != "A test vibe" {
		t.Errorf("expected description 'A test vibe', got %q", cfg.Description)
	}
	if cfg.Terminal.Tool != "wezterm" {
		t.Errorf("expected terminal tool 'wezterm', got %q", cfg.Terminal.Tool)
	}
	if len(cfg.Terminal.Sessions) != 1 {
		t.Fatalf("expected 1 session, got %d", len(cfg.Terminal.Sessions))
	}
	if cfg.Terminal.Sessions[0].Name != "dev" {
		t.Errorf("expected session name 'dev', got %q", cfg.Terminal.Sessions[0].Name)
	}
	if cfg.Terminal.Sessions[0].Command != "npm run dev" {
		t.Errorf("expected command 'npm run dev', got %q", cfg.Terminal.Sessions[0].Command)
	}
	// Verify ~ expansion happened
	expectedDir := filepath.Join(home, "projects/test")
	if cfg.Terminal.Sessions[0].Dir != expectedDir {
		t.Errorf("expected dir %q, got %q", expectedDir, cfg.Terminal.Sessions[0].Dir)
	}
	if cfg.Browser.Tool != "chrome" {
		t.Errorf("expected browser 'chrome', got %q", cfg.Browser.Tool)
	}
	if len(cfg.Browser.Tabs) != 1 || cfg.Browser.Tabs[0] != "https://example.com" {
		t.Errorf("unexpected tabs: %v", cfg.Browser.Tabs)
	}
	if cfg.IDE.Tool != "cursor" {
		t.Errorf("expected ide 'cursor', got %q", cfg.IDE.Tool)
	}
	if len(cfg.IDE.Windows) != 1 {
		t.Fatalf("expected 1 IDE window, got %d", len(cfg.IDE.Windows))
	}
	expectedIDEPath := filepath.Join(home, "projects/test")
	if cfg.IDE.Windows[0].Path != expectedIDEPath {
		t.Errorf("expected IDE path %q, got %q", expectedIDEPath, cfg.IDE.Windows[0].Path)
	}
	if len(cfg.Apps.Open) != 1 || cfg.Apps.Open[0] != "Slack" {
		t.Errorf("unexpected open apps: %v", cfg.Apps.Open)
	}
	if len(cfg.Apps.Close) != 1 || cfg.Apps.Close[0] != "Spotify" {
		t.Errorf("unexpected close apps: %v", cfg.Apps.Close)
	}
	if len(cfg.Teardown.KillProcesses) != 1 || cfg.Teardown.KillProcesses[0] != "node server" {
		t.Errorf("unexpected kill_processes: %v", cfg.Teardown.KillProcesses)
	}
}

func TestLoadVibe_NotFound(t *testing.T) {
	setupTestVibesDir(t)
	_, err := LoadVibe("nonexistent")
	if err == nil {
		t.Fatal("expected error for nonexistent vibe")
	}
}

func TestLoadVibe_InvalidYAML(t *testing.T) {
	home := setupTestVibesDir(t)
	path := filepath.Join(home, ".vibes", "envs", "bad.yml")
	if err := os.WriteFile(path, []byte("{{invalid yaml:::"), 0644); err != nil {
		t.Fatal(err)
	}

	_, err := LoadVibe("bad")
	if err == nil {
		t.Fatal("expected error for invalid YAML")
	}
}

func TestLoadVibe_DefaultsNameFromFilename(t *testing.T) {
	home := setupTestVibesDir(t)
	yml := `description: "no name field"`
	path := filepath.Join(home, ".vibes", "envs", "unnamed.yml")
	if err := os.WriteFile(path, []byte(yml), 0644); err != nil {
		t.Fatal(err)
	}

	cfg, err := LoadVibe("unnamed")
	if err != nil {
		t.Fatalf("LoadVibe failed: %v", err)
	}
	if cfg.Name != "unnamed" {
		t.Errorf("expected name 'unnamed', got %q", cfg.Name)
	}
}

func TestSaveVibe(t *testing.T) {
	setupTestVibesDir(t)
	cfg := &VibeConfig{
		SchemaVersion: 1,
		Name:          "saved-vibe",
		Description:   "test save",
		Terminal: TerminalConfig{
			Tool: "kitty",
		},
	}

	if err := SaveVibe(cfg); err != nil {
		t.Fatalf("SaveVibe failed: %v", err)
	}

	loaded, err := LoadVibe("saved-vibe")
	if err != nil {
		t.Fatalf("LoadVibe after save failed: %v", err)
	}
	if loaded.Name != "saved-vibe" {
		t.Errorf("expected name 'saved-vibe', got %q", loaded.Name)
	}
	if loaded.Terminal.Tool != "kitty" {
		t.Errorf("expected terminal tool 'kitty', got %q", loaded.Terminal.Tool)
	}
}

func TestListVibes(t *testing.T) {
	home := setupTestVibesDir(t)
	envsDir := filepath.Join(home, ".vibes", "envs")

	for _, name := range []string{"alpha", "beta", "gamma"} {
		path := filepath.Join(envsDir, name+".yml")
		os.WriteFile(path, []byte("name: "+name), 0644)
	}
	// Non-yml file should be ignored
	os.WriteFile(filepath.Join(envsDir, "notes.txt"), []byte("ignore me"), 0644)

	names, err := ListVibes()
	if err != nil {
		t.Fatalf("ListVibes failed: %v", err)
	}
	if len(names) != 3 {
		t.Fatalf("expected 3 vibes, got %d: %v", len(names), names)
	}
}

func TestListVibes_EmptyDir(t *testing.T) {
	setupTestVibesDir(t)
	names, err := ListVibes()
	if err != nil {
		t.Fatalf("ListVibes failed: %v", err)
	}
	if len(names) != 0 {
		t.Errorf("expected 0 vibes, got %d", len(names))
	}
}

func TestListVibes_NoDirYet(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("HOME", dir)
	// Don't create .vibes dir at all

	names, err := ListVibes()
	if err != nil {
		t.Fatalf("ListVibes failed: %v", err)
	}
	if names != nil {
		t.Errorf("expected nil, got %v", names)
	}
}

func TestLoadGlobalConfig_Defaults(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("HOME", dir)

	cfg, err := LoadGlobalConfig()
	if err != nil {
		t.Fatalf("LoadGlobalConfig failed: %v", err)
	}
	if cfg.DefaultTerminal != "wezterm" {
		t.Errorf("expected default terminal 'wezterm', got %q", cfg.DefaultTerminal)
	}
	if cfg.DefaultBrowser != "chrome" {
		t.Errorf("expected default browser 'chrome', got %q", cfg.DefaultBrowser)
	}
	if cfg.DefaultIDE != "cursor" {
		t.Errorf("expected default IDE 'cursor', got %q", cfg.DefaultIDE)
	}
}

func TestLoadGlobalConfig_CustomFile(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("HOME", dir)
	vibesDir := filepath.Join(dir, ".vibes")
	os.MkdirAll(vibesDir, 0755)

	yml := `
default_terminal: kitty
default_browser: firefox
default_ide: zed
`
	os.WriteFile(filepath.Join(vibesDir, "config.yml"), []byte(yml), 0644)

	cfg, err := LoadGlobalConfig()
	if err != nil {
		t.Fatalf("LoadGlobalConfig failed: %v", err)
	}
	if cfg.DefaultTerminal != "kitty" {
		t.Errorf("expected 'kitty', got %q", cfg.DefaultTerminal)
	}
	if cfg.DefaultBrowser != "firefox" {
		t.Errorf("expected 'firefox', got %q", cfg.DefaultBrowser)
	}
	if cfg.DefaultIDE != "zed" {
		t.Errorf("expected 'zed', got %q", cfg.DefaultIDE)
	}
}

func TestExpandPaths(t *testing.T) {
	home, _ := os.UserHomeDir()
	cfg := &VibeConfig{
		Terminal: TerminalConfig{
			Sessions: []TerminalSession{
				{Dir: "~/work/project"},
				{Dir: "/absolute/path"},
			},
		},
		IDE: IDEConfig{
			Windows: []IDEWindow{
				{Path: "~/code/repo"},
				{Path: "/opt/app"},
			},
		},
	}

	cfg.expandPaths()

	expectedTermDir := filepath.Join(home, "work/project")
	if cfg.Terminal.Sessions[0].Dir != expectedTermDir {
		t.Errorf("expected %q, got %q", expectedTermDir, cfg.Terminal.Sessions[0].Dir)
	}
	if cfg.Terminal.Sessions[1].Dir != "/absolute/path" {
		t.Errorf("absolute path should not change, got %q", cfg.Terminal.Sessions[1].Dir)
	}

	expectedIDEPath := filepath.Join(home, "code/repo")
	if cfg.IDE.Windows[0].Path != expectedIDEPath {
		t.Errorf("expected %q, got %q", expectedIDEPath, cfg.IDE.Windows[0].Path)
	}
	if cfg.IDE.Windows[1].Path != "/opt/app" {
		t.Errorf("absolute path should not change, got %q", cfg.IDE.Windows[1].Path)
	}
}
