# main.py
from obs_client import OBSClient
from key_handler import setup_keybindings

def main():
    obs = OBSClient(host='localhost', port=4455, password='твой_пароль_от_OBS')
    
    try:
        obs.connect()
        setup_keybindings(obs)
    except Exception as e:
        print(f"⚠️ Error: {e}")
    finally:
        obs.disconnect()

if __name__ == "__main__":
    main()
