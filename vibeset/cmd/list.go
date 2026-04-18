package cmd

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/charmbracelet/lipgloss"
	"github.com/spf13/cobra"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
	"github.com/jenish-1235/vibes/vibeset/internal/state"
)

var listCmd = &cobra.Command{
	Use:   "list",
	Short: "List all defined vibes",
	RunE:  runList,
}

func runList(cmd *cobra.Command, args []string) error {
	names, err := config.ListVibes()
	if err != nil {
		return err
	}

	if len(names) == 0 {
		fmt.Println("No vibes defined yet. Run `vibes create` to get started.")
		return nil
	}

	activeName, _ := state.GetActive()

	titleStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("#1565C0"))
	activeStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("#2E7D32")).Bold(true)
	dimStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("#757575"))

	fmt.Println(titleStyle.Render("Your vibes:"))
	fmt.Println()

	for _, name := range names {
		marker := "  "
		nameStr := name
		if name == activeName {
			marker = activeStyle.Render("▸ ")
			nameStr = activeStyle.Render(name)
		} else {
			nameStr = fmt.Sprintf("  %s", name)
		}

		// Get last modified time of the yml file
		ymlPath := filepath.Join(config.EnvsDir(), name+".yml")
		info, err := os.Stat(ymlPath)
		var lastUsed string
		if err == nil {
			lastUsed = dimStyle.Render(humanTime(info.ModTime()))
		}

		if name == activeName {
			fmt.Printf("%s%s  %s\n", marker, "", lastUsed)
		} else {
			fmt.Printf("%s  %s\n", nameStr, lastUsed)
		}
	}

	return nil
}

func humanTime(t time.Time) string {
	d := time.Since(t)
	switch {
	case d < time.Minute:
		return "just now"
	case d < time.Hour:
		return fmt.Sprintf("%dm ago", int(d.Minutes()))
	case d < 24*time.Hour:
		return fmt.Sprintf("%dh ago", int(d.Hours()))
	default:
		return t.Format("Jan 02")
	}
}
