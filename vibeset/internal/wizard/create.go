package wizard

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"github.com/jenish-1235/vibes/vibeset/internal/config"
)

func RunCreateWizard() (*config.VibeConfig, error) {
	reader := bufio.NewReader(os.Stdin)

	cfg := &config.VibeConfig{
		SchemaVersion: 1,
	}

	fmt.Print("Vibe name: ")
	name, _ := reader.ReadString('\n')
	cfg.Name = strings.TrimSpace(name)
	if cfg.Name == "" {
		return nil, fmt.Errorf("name is required")
	}

	fmt.Print("Description (optional): ")
	desc, _ := reader.ReadString('\n')
	cfg.Description = strings.TrimSpace(desc)

	// Terminal
	fmt.Print("\nTerminal tool [wezterm/iterm2/kitty] (enter to skip): ")
	termTool, _ := reader.ReadString('\n')
	termTool = strings.TrimSpace(termTool)
	if termTool != "" {
		cfg.Terminal.Tool = termTool
		fmt.Println("Add terminal sessions (empty name to stop):")
		for {
			fmt.Print("  Session name: ")
			sessName, _ := reader.ReadString('\n')
			sessName = strings.TrimSpace(sessName)
			if sessName == "" {
				break
			}

			fmt.Print("  Directory: ")
			dir, _ := reader.ReadString('\n')
			dir = strings.TrimSpace(dir)

			fmt.Print("  Command (optional): ")
			command, _ := reader.ReadString('\n')
			command = strings.TrimSpace(command)

			cfg.Terminal.Sessions = append(cfg.Terminal.Sessions, config.TerminalSession{
				Name:    sessName,
				Dir:     dir,
				Command: command,
			})
		}
	}

	// Browser
	fmt.Print("\nBrowser tool [chrome/arc/firefox] (enter to skip): ")
	browserTool, _ := reader.ReadString('\n')
	browserTool = strings.TrimSpace(browserTool)
	if browserTool != "" {
		cfg.Browser.Tool = browserTool
		fmt.Println("Add URLs (empty to stop):")
		for {
			fmt.Print("  URL: ")
			url, _ := reader.ReadString('\n')
			url = strings.TrimSpace(url)
			if url == "" {
				break
			}
			cfg.Browser.Tabs = append(cfg.Browser.Tabs, url)
		}
	}

	// IDE
	fmt.Print("\nIDE tool [cursor/vscode/zed/idea] (enter to skip): ")
	ideTool, _ := reader.ReadString('\n')
	ideTool = strings.TrimSpace(ideTool)
	if ideTool != "" {
		cfg.IDE.Tool = ideTool
		fmt.Println("Add project paths (empty to stop):")
		for {
			fmt.Print("  Path: ")
			path, _ := reader.ReadString('\n')
			path = strings.TrimSpace(path)
			if path == "" {
				break
			}
			cfg.IDE.Windows = append(cfg.IDE.Windows, config.IDEWindow{Path: path})
		}
	}

	// Apps
	fmt.Print("\nApps to open (comma-separated, enter to skip): ")
	openApps, _ := reader.ReadString('\n')
	openApps = strings.TrimSpace(openApps)
	if openApps != "" {
		for _, app := range strings.Split(openApps, ",") {
			app = strings.TrimSpace(app)
			if app != "" {
				cfg.Apps.Open = append(cfg.Apps.Open, app)
			}
		}
	}

	fmt.Print("Apps to close on teardown (comma-separated, enter to skip): ")
	closeApps, _ := reader.ReadString('\n')
	closeApps = strings.TrimSpace(closeApps)
	if closeApps != "" {
		for _, app := range strings.Split(closeApps, ",") {
			app = strings.TrimSpace(app)
			if app != "" {
				cfg.Apps.Close = append(cfg.Apps.Close, app)
			}
		}
	}

	return cfg, nil
}
