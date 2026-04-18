package cmd

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/spf13/cobra"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
)

var editCmd = &cobra.Command{
	Use:   "edit <name>",
	Short: "Open a vibe config in your editor",
	Args:  cobra.ExactArgs(1),
	RunE:  runEdit,
}

func runEdit(cmd *cobra.Command, args []string) error {
	name := args[0]
	path := filepath.Join(config.EnvsDir(), name+".yml")

	if _, err := os.Stat(path); os.IsNotExist(err) {
		return fmt.Errorf("vibe %q not found", name)
	}

	editor := os.Getenv("EDITOR")
	if editor == "" {
		editor = "vim"
	}

	c := exec.Command(editor, path)
	c.Stdin = os.Stdin
	c.Stdout = os.Stdout
	c.Stderr = os.Stderr
	return c.Run()
}
