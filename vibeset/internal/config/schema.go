package config

type VibeConfig struct {
	SchemaVersion int            `yaml:"schema_version"`
	Name          string         `yaml:"name"`
	Description   string         `yaml:"description,omitempty"`
	Terminal      TerminalConfig `yaml:"terminal,omitempty"`
	Browser       BrowserConfig  `yaml:"browser,omitempty"`
	IDE           IDEConfig      `yaml:"ide,omitempty"`
	Apps          AppsConfig     `yaml:"apps,omitempty"`
	Teardown      TeardownConfig `yaml:"teardown,omitempty"`
	Git           GitConfig      `yaml:"git,omitempty"`
}

type TerminalConfig struct {
	Tool     string            `yaml:"tool"`
	Sessions []TerminalSession `yaml:"sessions,omitempty"`
}

type TerminalSession struct {
	Name    string `yaml:"name"`
	Dir     string `yaml:"dir"`
	Command string `yaml:"command,omitempty"`
}

type BrowserConfig struct {
	Tool    string   `yaml:"tool"`
	Profile string   `yaml:"profile,omitempty"`
	Tabs    []string `yaml:"tabs,omitempty"`
}

type GitConfig struct {
	Name  string `yaml:"name,omitempty"`
	Email string `yaml:"email,omitempty"`
}

type IDEConfig struct {
	Tool    string      `yaml:"tool"`
	Windows []IDEWindow `yaml:"windows,omitempty"`
}

type IDEWindow struct {
	Path string `yaml:"path"`
}

type AppsConfig struct {
	Open  []string `yaml:"open,omitempty"`
	Close []string `yaml:"close,omitempty"`
}

type TeardownConfig struct {
	KillProcesses      []string `yaml:"kill_processes,omitempty"`
	CloseApps          []string `yaml:"close_apps,omitempty"`
	AggressiveTeardown bool     `yaml:"aggressive_teardown,omitempty"`
}

type GlobalConfig struct {
	DefaultTerminal string `yaml:"default_terminal"`
	DefaultBrowser  string `yaml:"default_browser"`
	DefaultIDE      string `yaml:"default_ide"`
}
