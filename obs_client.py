# obs_client.py
from obswebsocket import obsws, requests

class OBSClient:
    def __init__(self, host='localhost', port=4455, password=''):
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
