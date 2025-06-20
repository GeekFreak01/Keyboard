import tkinter as tk
from tkinter import ttk, messagebox
from obs_client import OBSClient
import os
import keyboard
import subprocess

class KeyButton(tk.Canvas):
    def __init__(self, master, label):
        width, height = 80, 60
        super().__init__(master, width=width, height=height, highlightthickness=0, bd=0, bg="#121212")
        self.label = label
        self.action_name = None
        self.action = None

        self.radius = 12
        self.bg_color = "#1e1e1e"
        self.hover_color = "#333333"
        self.text_color = "white"

        self.rect = self._rounded_rect(2, 2, width-2, height-2, self.radius, fill=self.bg_color, outline=self.bg_color)
        self.text_item = self.create_text(width/2, height/2, text=label, fill=self.text_color)

        self.bind("<ButtonRelease-1>", lambda e: self.trigger())
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=self.hover_color))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=self.bg_color))

    def _rounded_rect(self, x1, y1, x2, y2, r=25, **kwargs):
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def assign(self, action_name, action_func):
        self.action_name = action_name
        self.action = action_func
        self.itemconfig(self.text_item, text=f"{self.label}\n{action_name}")

    def trigger(self):
        if callable(self.action):
            self.action()
        elif isinstance(self.action, str) and self.action:
            try:
                subprocess.Popen(self.action, shell=True)
            except Exception as e:
                print(f"Failed to run command '{self.action}': {e}")
        else:
            print(f"No action assigned to {self.label}")

class KeyboardGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QMK Keyboard Controller")
        self.geometry("600x400")
        self.resizable(False, False)
        self.configure(bg="#121212")

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
        program_frame = tk.Frame(self, bg="#121212")
        program_frame.pack(pady=10)
        tk.Label(program_frame, text="Program:", fg="white", bg="#121212").pack(side=tk.LEFT)
        self.program_var = tk.StringVar(value="OBS")
        ttk.OptionMenu(program_frame, self.program_var, "OBS", "OBS").pack(side=tk.LEFT)

        content = tk.Frame(self, bg="#121212")
        content.pack(fill=tk.BOTH, expand=True)

        # Keyboard layout
        self.keyboard_frame = tk.Frame(content, bg="#121212")
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
        sidebar = tk.Frame(content, bg="#121212")
        sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        tk.Label(sidebar, text="Action", fg="white", bg="#121212").pack(pady=5)

        actions = {
            "Start Stream": self.obs.start_streaming,
            "Stop Stream": self.obs.stop_streaming,
            "Start Recording": self.obs.start_recording,
            "Stop Recording": self.obs.stop_recording,
            "Toggle Mic": self.obs.toggle_mic,
            "Scene 1": lambda: self.obs.set_scene("Scene 1"),
            "Scene 2": lambda: self.obs.set_scene("Scene 2"),
            "Run Program": None,
        }
        self.actions = actions

        self.action_var = tk.StringVar()
        self.action_box = ttk.Combobox(sidebar, textvariable=self.action_var, values=list(actions.keys()), state="readonly")
        self.action_box.pack(pady=5)

        tk.Label(sidebar, text="Command", fg="white", bg="#121212").pack(pady=(10,0))
        self.command_var = tk.StringVar()
        self.command_entry = tk.Entry(sidebar, textvariable=self.command_var, bg="#1e1e1e", fg="white", insertbackground="white")
        self.command_entry.pack(pady=5, fill=tk.X)

        assign_btn = tk.Button(sidebar, text="Assign", command=self.assign_action, bg="#1e1e1e", fg="white", relief=tk.FLAT, activebackground="#333333")
        assign_btn.pack(pady=5)

        self.selected_key = None

        # Register global hotkeys for each button
        self.setup_hotkeys()

    def select_key(self, key_btn):
        self.selected_key = key_btn
        print(f"Selected {key_btn.label}")

    def assign_action(self):
        if not self.selected_key:
            return
        action_name = self.action_var.get()
        if not action_name:
            return
        if action_name == "Run Program":
            cmd = self.command_var.get().strip()
            if cmd:
                self.selected_key.assign(action_name, cmd)
            else:
                messagebox.showwarning("No Command", "Please enter a command to run.")
        else:
            self.selected_key.assign(action_name, self.actions[action_name])

    def setup_hotkeys(self):
        """Bind F13–F24 to the main 12 keys."""
        for idx, key_btn in enumerate(self.keys[3:], start=13):
            hotkey = f"f{idx}"
            keyboard.add_hotkey(hotkey, key_btn.trigger)
        print("⌨️ Hotkeys registered: F13–F24")

    def run(self):
        self.mainloop()

if __name__ == "__main__":
    gui = KeyboardGUI()
    gui.run()
