package state

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
)

func activePath() string {
	return filepath.Join(config.VibesDir(), "active")
}

func GetActive() (string, error) {
	data, err := os.ReadFile(activePath())
	if err != nil {
		if os.IsNotExist(err) {
			return "", nil
		}
		return "", err
	}
	return strings.TrimSpace(string(data)), nil
}

func SetActive(name string) error {
	if err := config.EnsureDirs(); err != nil {
		return err
	}
	return os.WriteFile(activePath(), []byte(name+"\n"), 0644)
}

func ClearActive() error {
	err := os.Remove(activePath())
	if os.IsNotExist(err) {
		return nil
	}
	return err
}
