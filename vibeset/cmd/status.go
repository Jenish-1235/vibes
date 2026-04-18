package cmd

import (
	"fmt"

	"github.com/charmbracelet/lipgloss"
	"github.com/spf13/cobra"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
	"github.com/jenish-1235/vibes/vibeset/internal/state"
)

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show the currently active vibe",
	RunE:  runStatus,
}

func runStatus(cmd *cobra.Command, args []string) error {
	activeName, err := state.GetActive()
	if err != nil {
		return err
	}

	if activeName == "" {
		dim := lipgloss.NewStyle().Foreground(lipgloss.Color("#757575"))
		fmt.Println(dim.Render("No active vibe. Run `vibes set <name>` to start one."))
		return nil
	}

	cfg, err := config.LoadVibe(activeName)
	if err != nil {
		// Active file references a deleted vibe
		fmt.Printf("Active vibe: %s (config missing)\n", activeName)
		return nil
	}

	active := lipgloss.NewStyle().Foreground(lipgloss.Color("#2E7D32")).Bold(true)
	dim := lipgloss.NewStyle().Foreground(lipgloss.Color("#757575"))

	fmt.Printf("%s %s\n", active.Render("▸"), active.Render(cfg.Name))
	if cfg.Description != "" {
		fmt.Printf("  %s\n", dim.Render(cfg.Description))
	}

	if cfg.Terminal.Tool != "" {
		fmt.Printf("  terminal: %s (%d sessions)\n", cfg.Terminal.Tool, len(cfg.Terminal.Sessions))
	}
	if cfg.Browser.Tool != "" {
		fmt.Printf("  browser:  %s (%d tabs)\n", cfg.Browser.Tool, len(cfg.Browser.Tabs))
	}
	if cfg.IDE.Tool != "" {
		fmt.Printf("  ide:      %s (%d windows)\n", cfg.IDE.Tool, len(cfg.IDE.Windows))
	}

	return nil
}
