# key_handler.py
import keyboard
import time

def setup_keybindings(obs_client):
    # Примеры назначения кнопок
    keyboard.add_hotkey('f1', lambda: obs_client.set_scene('Scene 1'))
    keyboard.add_hotkey('f2', lambda: obs_client.set_scene('Scene 2'))
    keyboard.add_hotkey('f3', lambda: obs_client.toggle_mic())
    keyboard.add_hotkey('f4', lambda: obs_client.toggle_recording())

    print("⌨️ Hotkeys are active (press ESC to stop)...")
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("🛑 Stopping hotkey handler...")
            break
