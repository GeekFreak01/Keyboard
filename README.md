# Keyboard OBS Controller

This small project provides a Tkinter GUI and helper scripts to control OBS via the WebSocket interface.

## Environment variables

The OBS connection settings can be configured with the following variables:

- `OBS_HOST` – address of the OBS WebSocket server (defaults to `localhost`).
- `OBS_PORT` – port of the WebSocket server (defaults to `4455`).
- `OBS_PASSWORD` – password for the WebSocket server (defaults to an empty string or the value used in the GUI).

When these variables are not set, the original hard coded defaults are used.
