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
    
    def connect(self):
        self.ws.connect()
        print("✅ Connected to OBS WebSocket")
    
    def disconnect(self):
        self.ws.disconnect()
        print("❌ Disconnected from OBS WebSocket")
    
    def set_scene(self, scene_name):
        self.ws.call(requests.SetCurrentProgramScene(scene_name))
        print(f"🎬 Switched to scene: {scene_name}")
    
    def toggle_mic(self):
        self.ws.call(requests.ToggleInputMute('Mic/Aux'))
        print("🎙️ Toggled Mic Mute")
    
    def start_recording(self):
        self.ws.call(requests.StartRecord())
        print("⏺️ Recording Started")

    def stop_recording(self):
        self.ws.call(requests.StopRecord())
        print("⏹️ Recording Stopped")

    def start_streaming(self):
        self.ws.call(requests.StartStreaming())
        print("📡 Streaming Started")

    def stop_streaming(self):
        self.ws.call(requests.StopStreaming())
        print("🛑 Streaming Stopped")

    def toggle_filter(self, source_name, filter_name):
        self.ws.call(requests.ToggleSourceFilterEnabled(source_name, filter_name))
        print(f"✨ Toggled filter '{filter_name}' on {source_name}")
