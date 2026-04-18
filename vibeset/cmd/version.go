package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

// Version is set at build time via -ldflags "-X github.com/jenish-1235/vibes/vibeset/cmd.Version=vX.Y.Z"
var Version = "dev"

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print the vibes version",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("vibes %s\n", Version)
	},
}
