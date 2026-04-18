package cmd

import (
	"fmt"

	"github.com/charmbracelet/lipgloss"
	"github.com/spf13/cobra"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
	"github.com/jenish-1235/vibes/vibeset/internal/wizard"
)

var createCmd = &cobra.Command{
	Use:   "create",
	Short: "Create a new vibe via interactive wizard",
	RunE:  runCreate,
}

func runCreate(cmd *cobra.Command, args []string) error {
	cfg, err := wizard.RunCreateWizard()
	if err != nil {
		return err
	}

	if err := config.SaveVibe(cfg); err != nil {
		return fmt.Errorf("failed to save vibe: %w", err)
	}

	success := lipgloss.NewStyle().Foreground(lipgloss.Color("#2E7D32")).Bold(true)
	dim := lipgloss.NewStyle().Foreground(lipgloss.Color("#757575"))

	fmt.Println()
	fmt.Println(success.Render(fmt.Sprintf("✓ created vibe: %s", cfg.Name)))
	fmt.Println(dim.Render(fmt.Sprintf("  Run `vibes set %s` to activate it", cfg.Name)))
	fmt.Println(dim.Render(fmt.Sprintf("  Run `vibes edit %s` to tweak the config", cfg.Name)))
	return nil
}
