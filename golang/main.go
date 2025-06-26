package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"path/filepath"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/widget"
)

// Action defines a button action loaded from config.
type Action struct {
	Action  string `json:"action"`
	Command string `json:"command,omitempty"`
	Source  string `json:"source,omitempty"`
	Filter  string `json:"filter,omitempty"`
}

// loadConfig reads keyboard_config.json if present.
func loadConfig(path string, count int) ([]Action, error) {
	bs, err := ioutil.ReadFile(path)
	if err != nil {
		// return default list of empty actions
		return make([]Action, count), nil
	}
	var acts []Action
	if err := json.Unmarshal(bs, &acts); err != nil {
		return nil, err
	}
	// ensure length
	if len(acts) < count {
		for len(acts) < count {
			acts = append(acts, Action{})
		}
	}
	return acts, nil
}

func main() {
	host := os.Getenv("OBS_HOST")
	if host == "" {
		host = "localhost"
	}
	port := 4455
	if v := os.Getenv("OBS_PORT"); v != "" {
		fmt.Sscanf(v, "%d", &port)
	}
	password := os.Getenv("OBS_PASSWORD")

	obs, err := NewOBSClient(host, port, password)
	if err != nil {
		log.Printf("OBS connection error: %v", err)
	}
	defer obs.Disconnect()

	configPath := filepath.Join("..", "keyboard_config.json")
	acts, err := loadConfig(configPath, 18)
	if err != nil {
		log.Printf("failed to load config: %v", err)
		acts = make([]Action, 18)
	}

	a := app.New()
	w := a.NewWindow("Keyboard Controller")
	grid := container.NewGridWithColumns(5)

	handle := func(act Action) func() {
		return func() {
			switch act.Action {
			case "Run Program":
				if act.Command != "" {
					go func(cmd string) {
						_ = exec.Command("/bin/sh", "-c", cmd).Start()
					}(act.Command)
				}
			case "Toggle Stream":
				if obs != nil {
					if err := obs.ToggleStreaming(); err != nil {
						log.Println(err)
					}
				}
			case "Toggle Recording":
				if obs != nil {
					if err := obs.ToggleRecording(); err != nil {
						log.Println(err)
					}
				}
			case "Toggle Mic":
				if obs != nil {
					if err := obs.ToggleMic(); err != nil {
						log.Println(err)
					}
				}
			case "Scene 1":
				if obs != nil {
					obs.SetScene("Scene 1")
				}
			case "Scene 2":
				if obs != nil {
					obs.SetScene("Scene 2")
				}
			case "Toggle Filter":
				if obs != nil {
					obs.ToggleFilter(act.Source, act.Filter)
				}
			}
		}
	}

	labels := []string{"Enc 1", "Enc 2", "Enc 3"}
	for i := 1; i <= 15; i++ {
		labels = append(labels, fmt.Sprintf("Key %d", i))
	}

	for i, label := range labels {
		btn := widget.NewButton(label, handle(acts[i]))
		btn.Importance = widget.HighImportance
		btn.Style = widget.PrimaryButton
		grid.Add(btn)
	}
	w.SetContent(container.NewVBox(grid))
	w.Resize(fyne.NewSize(600, 300))
	w.ShowAndRun()
}
