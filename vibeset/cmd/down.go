package cmd

import (
	"fmt"
	"os"

	"github.com/charmbracelet/lipgloss"
	"github.com/spf13/cobra"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
	"github.com/jenish-1235/vibes/vibeset/internal/executor"
	"github.com/jenish-1235/vibes/vibeset/internal/state"
)

var downCmd = &cobra.Command{
	Use:   "down",
	Short: "Tear down the current vibe and clear active state",
	RunE:  runDown,
}

func runDown(cmd *cobra.Command, args []string) error {
	activeName, err := state.GetActive()
	if err != nil {
		return err
	}

	if activeName == "" {
		fmt.Println("No active vibe.")
		return nil
	}

	cfg, err := config.LoadVibe(activeName)
	if err != nil {
		return err
	}

	fmt.Printf("tearing down %s...\n", activeName)
	for _, ex := range executor.AllExecutors() {
		if err := ex.Teardown(cfg); err != nil {
			fmt.Fprintf(os.Stderr, "warning: teardown error: %v\n", err)
		}
	}

	if err := state.ClearActive(); err != nil {
		return err
	}

	style := lipgloss.NewStyle().Foreground(lipgloss.Color("#B71C1C")).Bold(true)
	fmt.Println(style.Render(fmt.Sprintf("✓ vibe %s is down", activeName)))
	return nil
}
