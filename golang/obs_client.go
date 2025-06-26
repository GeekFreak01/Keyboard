package main

import (
	"context"
	"fmt"

	"github.com/andreykaipov/goobs"
	"github.com/andreykaipov/goobs/api/requests/filters"
	"github.com/andreykaipov/goobs/api/requests/inputs"
	"github.com/andreykaipov/goobs/api/requests/outputs"
	"github.com/andreykaipov/goobs/api/requests/scenes"
)

// OBSClient wraps goobs.Client for common actions.
type OBSClient struct {
	client *goobs.Client
}

// NewOBSClient connects to the OBS WebSocket server.
func NewOBSClient(host string, port int, password string) (*OBSClient, error) {
	addr := fmt.Sprintf("%s:%d", host, port)
	cli, err := goobs.New(addr, goobs.WithPassword(password))
	if err != nil {
		return nil, err
	}
	return &OBSClient{client: cli}, nil
}

// Disconnect closes the connection.
func (o *OBSClient) Disconnect() {
	if o.client != nil {
		o.client.Disconnect()
	}
}

// SetScene switches the current program scene.
func (o *OBSClient) SetScene(name string) error {
	_, err := o.client.Scenes.SetCurrentProgramScene(
		context.Background(),
		&scenes.SetCurrentProgramSceneParams{SceneName: name},
	)
	return err
}

// ToggleMic toggles the mute state of "Mic/Aux" input.
func (o *OBSClient) ToggleMic() error {
	_, err := o.client.Inputs.ToggleInputMute(
		context.Background(),
		&inputs.ToggleInputMuteParams{InputName: "Mic/Aux"},
	)
	return err
}

// ToggleStreaming starts or stops streaming depending on state.
func (o *OBSClient) ToggleStreaming() error {
	_, err := o.client.Outputs.ToggleStream(context.Background())
	return err
}

// ToggleRecording starts or stops recording depending on state.
func (o *OBSClient) ToggleRecording() error {
	_, err := o.client.Outputs.ToggleRecord(context.Background())
	return err
}

// ToggleFilter toggles the specified filter on a source.
func (o *OBSClient) ToggleFilter(source, filter string) error {
	state, err := o.client.Filters.GetSourceFilter(
		context.Background(),
		&filters.GetSourceFilterParams{SourceName: source, FilterName: filter},
	)
	if err != nil {
		return err
	}
	_, err = o.client.Filters.SetSourceFilterEnabled(
		context.Background(),
		&filters.SetSourceFilterEnabledParams{
			SourceName:    source,
			FilterName:    filter,
			FilterEnabled: !state.FilterEnabled,
		},
	)
	return err
}

// ListInputs returns the available input names.
func (o *OBSClient) ListInputs() ([]string, error) {
	resp, err := o.client.Inputs.GetInputList(context.Background(), nil)
	if err != nil {
		return nil, err
	}
	var names []string
	for _, i := range resp.Inputs {
		names = append(names, i.InputName)
	}
	return names, nil
}

// ListFilters returns filter names for a given source.
func (o *OBSClient) ListFilters(source string) ([]string, error) {
	resp, err := o.client.Filters.GetSourceFilterList(
		context.Background(),
		&filters.GetSourceFilterListParams{SourceName: source},
	)
	if err != nil {
		return nil, err
	}
	var names []string
	for _, f := range resp.Filters {
		names = append(names, f.FilterName)
	}
	return names, nil
}

// Version returns the current OBS version.
