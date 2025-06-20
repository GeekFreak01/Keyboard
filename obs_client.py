# obs_client.py
from obswebsocket import obsws, requests
import os

class OBSClient:
    def __init__(self, host=None, port=None, password=None):
        host = host if host is not None else os.getenv("OBS_HOST", "localhost")
        env_port = os.getenv("OBS_PORT")
        if port is None:
            port = int(env_port) if env_port is not None else 4455
        password = password if password is not None else os.getenv("OBS_PASSWORD", "")

        self.ws = obsws(host, port, password)
        self.connected = False
    
    def connect(self):
        self.ws.connect()
        self.connected = True
        print("✅ Connected to OBS WebSocket")
    
    def disconnect(self):
        if self.connected:
            self.ws.disconnect()
            self.connected = False
            print("❌ Disconnected from OBS WebSocket")

    def ensure_connection(self):
        if not self.connected:
            try:
                self.connect()
            except Exception as e:
                print(f"OBS connection failed: {e}")
                return False
        return True
    
    def set_scene(self, scene_name):
        if not self.ensure_connection():
            return
        self.ws.call(requests.SetCurrentProgramScene(sceneName=scene_name))
        print(f"🎬 Switched to scene: {scene_name}")
    
    def toggle_mic(self):
        if not self.ensure_connection():
            return
        self.ws.call(requests.ToggleInputMute(inputName='Mic/Aux'))
        print("🎙️ Toggled Mic Mute")
    
    def start_recording(self):
        if not self.ensure_connection():
            return
        self.ws.call(requests.StartRecord())
        print("⏺️ Recording Started")

    def stop_recording(self):
        if not self.ensure_connection():
            return
        self.ws.call(requests.StopRecord())
        print("⏹️ Recording Stopped")

    def start_streaming(self):
        if not self.ensure_connection():
            return
        self.ws.call(requests.StartStreaming())
        print("📡 Streaming Started")

    def stop_streaming(self):
        if not self.ensure_connection():
            return
        self.ws.call(requests.StopStreaming())
        print("🛑 Streaming Stopped")

    def toggle_streaming(self):
        """Start or stop streaming depending on current state."""
        if not self.ensure_connection():
            return
        self.ws.call(requests.ToggleStream())
        print("🔀 Streaming Toggled")

    def toggle_filter(self, source_name, filter_name):
        # Retrieve current filter state
        if not self.ensure_connection():
            return
        resp = self.ws.call(requests.GetSourceFilter(sourceName=source_name, filterName=filter_name))
        current_state = resp.datain.get("filterEnabled")

        # Toggle the filter state
        resp = self.ws.call(
            requests.SetSourceFilterEnabled(
                sourceName=source_name, filterName=filter_name,
                filterEnabled=not current_state
            )
        )

        if resp.status:
            print(f"✨ Toggled filter '{filter_name}' on {source_name}")
        else:
            print(f"❌ Failed to toggle filter '{filter_name}' on {source_name}")

    def toggle_recording(self):
        """Start or stop recording depending on current state."""
        if not self.ensure_connection():
            return
        self.ws.call(requests.ToggleRecord())
        print("🔀 Recording Toggled")

    def list_inputs(self):
        """Return a list of available input names."""
        if not self.ensure_connection():
            return []
        resp = self.ws.call(requests.GetInputList())
        inputs = resp.datain.get("inputs", [])
        return [i.get("inputName") for i in inputs]

    def list_filters(self, source_name):
        """Return filter names for the given source."""
        if not self.ensure_connection():
            return []
        resp = self.ws.call(requests.GetSourceFilterList(sourceName=source_name))
        filters = resp.datain.get("filters", [])
        return [f.get("filterName") for f in filters]
