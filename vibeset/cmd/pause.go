package cmd

import (
	"fmt"

	"github.com/charmbracelet/lipgloss"
	"github.com/spf13/cobra"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
	"github.com/jenish-1235/vibes/vibeset/internal/executor"
	"github.com/jenish-1235/vibes/vibeset/internal/state"
)

var pauseCmd = &cobra.Command{
	Use:   "pause",
	Short: "Pause the current vibe (teardown + save for resume)",
	RunE:  runPause,
}

func runPause(cmd *cobra.Command, args []string) error {
	activeName, err := state.GetActive()
	if err != nil {
		return err
	}

	if activeName == "" {
		fmt.Println("No active vibe to pause.")
		return nil
	}

	cfg, err := config.LoadVibe(activeName)
	if err != nil {
		return err
	}

	// Save pause state before teardown
	if err := state.SavePause(activeName); err != nil {
		return fmt.Errorf("failed to save pause state: %w", err)
	}

	// Teardown
	for _, ex := range executor.AllExecutors() {
		if err := ex.Teardown(cfg); err != nil {
			fmt.Printf("warning: teardown error: %v\n", err)
		}
	}

	if err := state.ClearActive(); err != nil {
		return err
	}

	style := lipgloss.NewStyle().Foreground(lipgloss.Color("#FF8F00")).Bold(true)
	fmt.Println(style.Render(fmt.Sprintf("⏸ paused %s", activeName)))
	return nil
}
