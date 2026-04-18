package state

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
	"gopkg.in/yaml.v3"
)

type GitRestoreState struct {
	Name  string `yaml:"name"`
	Email string `yaml:"email"`
}

func gitRestorePath() string {
	return filepath.Join(config.VibesDir(), "git_restore.yml")
}

func SaveGitRestore() error {
	if err := config.EnsureDirs(); err != nil {
		return err
	}
	s := GitRestoreState{
		Name:  gitConfigGet("user.name"),
		Email: gitConfigGet("user.email"),
	}
	data, err := yaml.Marshal(&s)
	if err != nil {
		return err
	}
	return os.WriteFile(gitRestorePath(), data, 0644)
}

func LoadGitRestore() (*GitRestoreState, error) {
	data, err := os.ReadFile(gitRestorePath())
	if err != nil {
		return nil, err
	}
	var s GitRestoreState
	if err := yaml.Unmarshal(data, &s); err != nil {
		return nil, err
	}
	return &s, nil
}

func ClearGitRestore() error {
	err := os.Remove(gitRestorePath())
	if os.IsNotExist(err) {
		return nil
	}
	return err
}

func gitConfigGet(key string) string {
	out, err := exec.Command("git", "config", "--global", key).Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(out))
}
