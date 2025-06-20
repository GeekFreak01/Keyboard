import tkinter as tk
from tkinter import ttk, messagebox
from obs_client import OBSClient
import os

class KeyButton(tk.Button):
    def __init__(self, master, label):
        super().__init__(master, text=label, width=10, height=3)
        self.label = label
        self.action_name = None
        self.action = None
        self.config(command=self.trigger)

    def assign(self, action_name, action_func):
        self.action_name = action_name
        self.action = action_func
        self.config(text=f"{self.label}\n{action_name}")

    def trigger(self):
        if callable(self.action):
            self.action()
        else:
            print(f"No action assigned to {self.label}")

class KeyboardGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QMK Keyboard Controller")
        self.geometry("600x400")

        # Connect to OBS
        self.obs = OBSClient(
            host=os.getenv("OBS_HOST", "localhost"),
            port=int(os.getenv("OBS_PORT", 4455)),
            password=os.getenv("OBS_PASSWORD", "your_password")
        )
        try:
            self.obs.connect()
        except Exception as e:
            print(f"OBS connection error: {e}")
            msg = (
                "Failed to connect to OBS.\n"
                "1. Ensure OBS is running and the WebSocket server is enabled.\n"
                "2. Verify the host and port settings.\n"
                "3. Check the WebSocket password."
            )
            retry = messagebox.askretrycancel("OBS Connection Error", msg)
            if retry:
                try:
                    self.obs.connect()
                except Exception:
                    messagebox.showerror(
                        "Connection Failed",
                        "Still unable to connect. Please review your settings."
                    )

        # Program selector (for future expansion)
        program_frame = tk.Frame(self)
        program_frame.pack(pady=10)
        tk.Label(program_frame, text="Program:").pack(side=tk.LEFT)
        self.program_var = tk.StringVar(value="OBS")
        ttk.OptionMenu(program_frame, self.program_var, "OBS", "OBS").pack(side=tk.LEFT)

        content = tk.Frame(self)
        content.pack(fill=tk.BOTH, expand=True)

        # Keyboard layout
        self.keyboard_frame = tk.Frame(content)
        self.keyboard_frame.pack(side=tk.LEFT, padx=10)

        self.keys = []
        # Encoders on top row
        for i in range(3):
            btn = KeyButton(self.keyboard_frame, f"Enc {i+1}")
            btn.grid(row=0, column=i, padx=5, pady=5)
            btn.bind('<Button-1>', lambda e, b=btn: self.select_key(b))
            self.keys.append(btn)

        # 12 keys (3x4 grid)
        index = 1
        for r in range(1,5):
            for c in range(3):
                btn = KeyButton(self.keyboard_frame, f"Key {index}")
                btn.grid(row=r, column=c, padx=5, pady=5)
                btn.bind('<Button-1>', lambda e, b=btn: self.select_key(b))
                self.keys.append(btn)
                index += 1

        # Sidebar for actions
        sidebar = tk.Frame(content)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        tk.Label(sidebar, text="Action").pack(pady=5)

        actions = {
            "Start Stream": self.obs.start_streaming,
            "Stop Stream": self.obs.stop_streaming,
            "Start Recording": self.obs.start_recording,
            "Stop Recording": self.obs.stop_recording,
            "Toggle Mic": self.obs.toggle_mic,
            "Scene 1": lambda: self.obs.set_scene("Scene 1"),
            "Scene 2": lambda: self.obs.set_scene("Scene 2"),
        }
        self.actions = actions

        self.action_var = tk.StringVar()
        self.action_box = ttk.Combobox(sidebar, textvariable=self.action_var, values=list(actions.keys()), state="readonly")
        self.action_box.pack(pady=5)

        assign_btn = tk.Button(sidebar, text="Assign", command=self.assign_action)
        assign_btn.pack(pady=5)

        self.selected_key = None

    def select_key(self, key_btn):
        self.selected_key = key_btn
        print(f"Selected {key_btn.label}")

    def assign_action(self):
        if not self.selected_key:
            return
        action_name = self.action_var.get()
        if action_name:
            self.selected_key.assign(action_name, self.actions[action_name])

    def run(self):
        self.mainloop()

if __name__ == "__main__":
    gui = KeyboardGUI()
    gui.run()
