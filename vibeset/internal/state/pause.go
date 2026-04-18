package state

import (
	"os"
	"path/filepath"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
	"gopkg.in/yaml.v3"
)

func pausePath() string {
	return filepath.Join(config.VibesDir(), "paused.yml")
}

type PauseState struct {
	VibeName string `yaml:"vibe_name"`
}

func SavePause(vibeName string) error {
	if err := config.EnsureDirs(); err != nil {
		return err
	}

	state := PauseState{VibeName: vibeName}
	data, err := yaml.Marshal(&state)
	if err != nil {
		return err
	}
	return os.WriteFile(pausePath(), data, 0644)
}

func LoadPause() (*PauseState, error) {
	data, err := os.ReadFile(pausePath())
	if err != nil {
		return nil, err
	}

	var state PauseState
	if err := yaml.Unmarshal(data, &state); err != nil {
		return nil, err
	}
	return &state, nil
}

func ClearPause() error {
	err := os.Remove(pausePath())
	if os.IsNotExist(err) {
		return nil
	}
	return err
}
