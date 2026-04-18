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

var setCmd = &cobra.Command{
	Use:   "set <name>",
	Short: "Switch to a named vibe",
	Long:  `Tears down the current vibe and sets up the target one.`,
	Args:  cobra.ExactArgs(1),
	RunE:  runSet,
}

func runSet(cmd *cobra.Command, args []string) error {
	targetName := args[0]

	target, err := config.LoadVibe(targetName)
	if err != nil {
		return err
	}

	executors := executor.AllExecutors()

	// Teardown current vibe if one is active
	currentName, _ := state.GetActive()
	if currentName != "" && currentName != targetName {
		current, err := config.LoadVibe(currentName)
		if err == nil {
			fmt.Printf("tearing down %s...\n", currentName)
			for _, ex := range executors {
				if err := ex.Teardown(current); err != nil {
					fmt.Fprintf(os.Stderr, "warning: teardown error: %v\n", err)
				}
			}
		}
	}

	// Setup target vibe
	fmt.Printf("setting up %s...\n", targetName)
	for _, ex := range executors {
		if err := ex.Setup(target); err != nil {
			fmt.Fprintf(os.Stderr, "warning: setup error: %v\n", err)
		}
	}

	if err := state.SetActive(targetName); err != nil {
		return fmt.Errorf("failed to save active state: %w", err)
	}

	success := lipgloss.NewStyle().Foreground(lipgloss.Color("#2E7D32")).Bold(true)
	fmt.Println(success.Render(fmt.Sprintf("✓ vibing on %s", targetName)))
	return nil
}
