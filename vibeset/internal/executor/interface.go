package executor

import "github.com/jenish-1235/vibes/vibeset/internal/config"

type Executor interface {
	Setup(cfg *config.VibeConfig) error
	Teardown(cfg *config.VibeConfig) error
}

func AllExecutors() []Executor {
	return []Executor{
		&ProcessExecutor{},
		&AppExecutor{},
		&TerminalExecutor{},
		&BrowserExecutor{},
		&IDEExecutor{},
	}
}
