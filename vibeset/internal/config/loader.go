package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"
)

func VibesDir() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".vibes")
}

func EnvsDir() string {
	return filepath.Join(VibesDir(), "envs")
}

func EnsureDirs() error {
	return os.MkdirAll(EnvsDir(), 0755)
}

func LoadVibe(name string) (*VibeConfig, error) {
	path := filepath.Join(EnvsDir(), name+".yml")
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("vibe %q not found: %w", name, err)
	}

	var cfg VibeConfig
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("invalid vibe config %q: %w", name, err)
	}

	if cfg.Name == "" {
		cfg.Name = name
	}

	cfg.expandPaths()
	return &cfg, nil
}

func SaveVibe(cfg *VibeConfig) error {
	if err := EnsureDirs(); err != nil {
		return err
	}

	data, err := yaml.Marshal(cfg)
	if err != nil {
		return fmt.Errorf("failed to marshal vibe: %w", err)
	}

	path := filepath.Join(EnvsDir(), cfg.Name+".yml")
	return os.WriteFile(path, data, 0644)
}

func ListVibes() ([]string, error) {
	entries, err := os.ReadDir(EnvsDir())
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}

	var names []string
	for _, e := range entries {
		if !e.IsDir() && strings.HasSuffix(e.Name(), ".yml") {
			names = append(names, strings.TrimSuffix(e.Name(), ".yml"))
		}
	}
	return names, nil
}

func LoadGlobalConfig() (*GlobalConfig, error) {
	path := filepath.Join(VibesDir(), "config.yml")
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return &GlobalConfig{
				DefaultTerminal: "wezterm",
				DefaultBrowser:  "chrome",
				DefaultIDE:      "cursor",
			}, nil
		}
		return nil, err
	}

	var cfg GlobalConfig
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, err
	}
	return &cfg, nil
}

func (c *VibeConfig) expandPaths() {
	home, _ := os.UserHomeDir()
	expand := func(p string) string {
		if strings.HasPrefix(p, "~/") {
			return filepath.Join(home, p[2:])
		}
		return p
	}

	for i := range c.Terminal.Sessions {
		c.Terminal.Sessions[i].Dir = expand(c.Terminal.Sessions[i].Dir)
	}
	for i := range c.IDE.Windows {
		c.IDE.Windows[i].Path = expand(c.IDE.Windows[i].Path)
	}
}
