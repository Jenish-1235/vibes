package cmd

import (
	"fmt"

	"github.com/spf13/cobra"

	"github.com/jenish-1235/vibes/vibeset/internal/state"
)

var resumeCmd = &cobra.Command{
	Use:   "resume",
	Short: "Resume the last paused vibe",
	RunE:  runResume,
}

func runResume(cmd *cobra.Command, args []string) error {
	paused, err := state.LoadPause()
	if err != nil {
		fmt.Println("No paused vibe to resume.")
		return nil
	}

	if paused.VibeName == "" {
		fmt.Println("No paused vibe to resume.")
		return nil
	}

	// Clear pause state before resuming
	state.ClearPause()

	// Delegate to set command
	return runSet(cmd, []string{paused.VibeName})
}
