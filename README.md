# Keyboard OBS Controller

This small project provides a Tkinter GUI and helper scripts to control OBS via the WebSocket interface.

## Requirements

Install the Python dependencies with:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file lists:

- `keyboard` – used to register global hotkeys.
- `obs-websocket-py` – Python client for controlling OBS Studio via WebSocket.

You will also need the OBS WebSocket plugin. OBS Studio 28 and later ships
with it already enabled. For older versions, download the plugin from
[the obs-websocket releases page](https://github.com/obsproject/obs-websocket/releases)
and install it. Once installed, enable the server from **Tools → WebSocket Server Settings** in OBS.

## Environment variables

The OBS connection settings can be configured with the following variables:

- `OBS_HOST` – address of the OBS WebSocket server (defaults to `localhost`).
- `OBS_PORT` – port of the WebSocket server (defaults to `4455`).
- `OBS_PASSWORD` – password for the WebSocket server (defaults to an empty string or the value used in the GUI).

When these variables are not set, the original hard coded defaults are used.

## Usage

Start the GUI controller with:

```bash
python main.py
```

The application will connect to OBS using the environment variables above. For example:

```bash
OBS_HOST=192.168.1.2 OBS_PASSWORD=secret python main.py
```

## Hotkeys

When running the GUI, global hotkeys for **F13** through **F24** are registered for the numbered keys.
Each function key corresponds to the buttons shown in the interface in order: `F13` → Key 1, `F14` → Key 2 and so on.
Pressing one of these keys will trigger the assigned action without clicking the GUI button.

On Linux systems the `keyboard` module may require elevated privileges to
capture global events. If the hotkeys do not work, try running the application
with `sudo` or as an administrator.
