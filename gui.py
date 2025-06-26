import tkinter as tk
from tkinter import ttk, messagebox
from obs_client import OBSClient
import os
import keyboard
import subprocess
import pystray
from PIL import Image, ImageDraw
import json

class KeyButton(tk.Canvas):
    def __init__(self, master, label):
        width, height = 80, 60
        super().__init__(master, width=width, height=height, highlightthickness=0, bd=0, bg="#121212")
        self.label = label
        self.action_name = None
        self.action = None
        self.meta = None

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

    def assign(self, action_name, action_func, meta=None):
        self.action_name = action_name
        self.action = action_func
        self.meta = meta
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
        self.geometry("700x400")
        self.resizable(False, False)
        self.configure(bg="#121212")

        self.overrideredirect(True)
        self._is_maximized = False
        self._normal_geometry = None

        self.title_bar = tk.Frame(self, bg="#1e1e1e")
        self.title_bar.pack(fill=tk.X, side=tk.TOP)

        btn_cfg = {
            "bg": "#1e1e1e",
            "fg": "white",
            "relief": tk.FLAT,
            "activebackground": "#333333",
            "width": 3,
        }
        self.min_button = tk.Button(
            self.title_bar, text="_", command=self.iconify, **btn_cfg
        )
        self.max_button = tk.Button(
            self.title_bar, text="□", command=self.toggle_maximize, **btn_cfg
        )
        self.close_button = tk.Button(
            self.title_bar, text="×", command=self.on_exit, **btn_cfg
        )
        # Pack close first so buttons appear as [minimize, maximize, close]
        for btn in (self.close_button, self.max_button, self.min_button):
            btn.pack(side=tk.RIGHT, padx=2, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#333333"))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#1e1e1e"))

        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)

        self.config_file = "keyboard_config.json"
        self.programs = {
            "Firefox": "firefox",
            "Calculator": "calc" if os.name == "nt" else "gnome-calculator",
            "Notepad": "notepad" if os.name == "nt" else "gedit",
        }

        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.bind("<Unmap>", self.on_minimize)

        self.tray_icon = self.create_tray_icon()

        # Initialize OBS client but don't require connection on startup
        self.obs = OBSClient(
            host=os.getenv("OBS_HOST", "localhost"),
            port=int(os.getenv("OBS_PORT", 4455)),
            password=os.getenv("OBS_PASSWORD", "your_password")
        )
        try:
            self.obs.connect()
        except Exception as e:
            print(f"OBS connection error: {e}. Will retry when actions are used.")

        content = tk.Frame(self, bg="#121212")
        content.pack(fill=tk.BOTH, expand=True)

        # Keyboard layout
        self.keyboard_frame = tk.Frame(content, bg="#121212")
        self.keyboard_frame.pack(side=tk.LEFT, padx=10)

        self.keys = []
        self.encoders = []
        # Encoders on a dedicated top row
        for i in range(3):
            btn = KeyButton(self.keyboard_frame, f"Enc {i+1}")
            btn.grid(row=0, column=i+1, padx=5, pady=5)
            btn.bind('<Button-1>', lambda e, b=btn: self.select_key(b))
            self.encoders.append(btn)
            self.keys.append(btn)

        # 15 keys in three rows below the encoders
        index = 1
        for r in range(1, 4):
            for c in range(5):
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
            "Toggle Stream": self.obs.toggle_streaming,
            "Toggle Recording": self.obs.toggle_recording,
            "Toggle Mic": self.obs.toggle_mic,
            "Scene 1": lambda: self.obs.set_scene("Scene 1"),
            "Scene 2": lambda: self.obs.set_scene("Scene 2"),
            "Toggle Filter": None,
            "Run Program": None,
        }
        self.actions = actions

        self.action_var = tk.StringVar()
        self.action_box = ttk.Combobox(
            sidebar, textvariable=self.action_var,
            values=list(actions.keys()), state="readonly"
        )
        self.action_box.pack(pady=5)
        self.action_var.trace_add("write", self.update_action_ui)
        self.program_label = tk.Label(sidebar, text="Program", fg="white", bg="#121212")
        self.program_var = tk.StringVar()
        self.program_box = ttk.Combobox(
            sidebar, textvariable=self.program_var,
            values=list(self.programs.keys()), state="readonly"
        )

        self.command_label = tk.Label(sidebar, text="Command", fg="white", bg="#121212")
        self.command_var = tk.StringVar()
        self.command_entry = tk.Entry(
            sidebar, textvariable=self.command_var,
            bg="#1e1e1e", fg="white", insertbackground="white"
        )

        self.source_label = tk.Label(sidebar, text="Source", fg="white", bg="#121212")
        self.source_var = tk.StringVar()
        self.source_box = ttk.Combobox(sidebar, textvariable=self.source_var, state="readonly")
        self.source_var.trace_add("write", self.update_filter_options)

        self.filter_label = tk.Label(sidebar, text="Filter", fg="white", bg="#121212")
        self.filter_var = tk.StringVar()
        self.filter_box = ttk.Combobox(sidebar, textvariable=self.filter_var, state="readonly")

        # Initially hide program and command widgets until an action is chosen
        self.program_label.pack_forget()
        self.program_box.pack_forget()
        self.command_label.pack_forget()
        self.command_entry.pack_forget()
        self.source_label.pack_forget()
        self.source_box.pack_forget()
        self.filter_label.pack_forget()
        self.filter_box.pack_forget()

        assign_btn = tk.Button(sidebar, text="Assign", command=self.assign_action, bg="#1e1e1e", fg="white", relief=tk.FLAT, activebackground="#333333")
        assign_btn.pack(pady=5)

        self.selected_key = None

        self.load_config()

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
            cmd_text = self.command_var.get().strip()
            if cmd_text:
                self.selected_key.assign(action_name, cmd_text)
            else:
                program_label = self.program_var.get().strip()
                cmd = self.programs.get(program_label)
                if cmd:
                    self.selected_key.assign(action_name, cmd)
                else:
                    messagebox.showwarning(
                        "No Program",
                        "Please choose a program or enter a command to run."
                    )
        elif action_name == "Toggle Filter":
            source = self.source_var.get().strip()
            flt = self.filter_var.get().strip()
            if source and flt:
                func = lambda s=source, f=flt: self.obs.toggle_filter(s, f)
                self.selected_key.assign(action_name, func, {"source": source, "filter": flt})
            else:
                messagebox.showwarning(
                    "Missing Info",
                    "Please select both a source and filter."
                )
                return
        else:
            self.selected_key.assign(action_name, self.actions[action_name])

        self.save_config()

    def update_action_ui(self, *args):
        """Adjust input widgets based on selected action."""
        action = self.action_var.get()
        if action == "Run Program":
            self.program_label.pack(pady=(10, 0))
            self.program_box.pack(pady=5, fill=tk.X)
            self.command_label.pack(pady=(10, 0))
            self.command_entry.pack(pady=5, fill=tk.X)
            self.source_label.pack_forget()
            self.source_box.pack_forget()
            self.filter_label.pack_forget()
            self.filter_box.pack_forget()
        elif action == "Toggle Filter":
            self.program_label.pack_forget()
            self.program_box.pack_forget()
            self.command_label.pack_forget()
            self.command_entry.pack_forget()
            self.populate_sources()
            self.source_label.pack(pady=(10, 0))
            self.source_box.pack(pady=5, fill=tk.X)
            self.filter_label.pack(pady=(10, 0))
            self.filter_box.pack(pady=5, fill=tk.X)
        else:
            self.program_label.pack_forget()
            self.program_box.pack_forget()
            self.command_label.pack_forget()
            self.command_entry.pack_forget()
            self.source_label.pack_forget()
            self.source_box.pack_forget()
            self.filter_label.pack_forget()
            self.filter_box.pack_forget()

    def populate_sources(self):
        """Load available OBS sources into the combobox."""
        try:
            sources = self.obs.list_inputs()
        except Exception as e:
            print(f"Failed to get sources: {e}")
            sources = []
        self.source_box["values"] = sources
        self.source_var.set("")
        self.filter_box["values"] = []
        self.filter_var.set("")

    def update_filter_options(self, *args):
        source = self.source_var.get()
        if not source:
            self.filter_box["values"] = []
            self.filter_var.set("")
            return
        try:
            filters = self.obs.list_filters(source)
        except Exception as e:
            print(f"Failed to get filters for {source}: {e}")
            filters = []
        self.filter_box["values"] = filters
        if filters:
            self.filter_var.set(filters[0])

    def save_config(self):
        data = []
        for btn in self.keys:
            entry = {"action": btn.action_name}
            if btn.action_name == "Run Program":
                entry["command"] = btn.action
            elif btn.action_name == "Toggle Filter" and btn.meta:
                entry["source"] = btn.meta.get("source")
                entry["filter"] = btn.meta.get("filter")
            data.append(entry)
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def load_config(self):
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return
        except Exception as e:
            print(f"Failed to load config: {e}")
            return

        for btn, info in zip(self.keys, data):
            action = info.get("action")
            if not action:
                continue
            if action == "Run Program":
                cmd = info.get("command")
                btn.assign(action, cmd)
            elif action == "Toggle Filter":
                source = info.get("source")
                flt = info.get("filter")
                func = lambda s=source, f=flt: self.obs.toggle_filter(s, f)
                btn.assign(action, func, {"source": source, "filter": flt})
            else:
                btn.assign(action, self.actions.get(action))

    def setup_hotkeys(self):
        """Bind F13–F24 to the first 12 numbered keys."""
        for idx, key_btn in enumerate(self.keys[3:15], start=13):
            hotkey = f"f{idx}"
            keyboard.add_hotkey(hotkey, key_btn.trigger)
        print("⌨️ Hotkeys registered: F13–F24")

    def create_tray_icon(self):
        """Create the system tray icon."""
        size = 64
        image = Image.new("RGB", (size, size), "#1e1e1e")
        draw = ImageDraw.Draw(image)
        draw.text((size // 3, size // 4), "K", fill="white")
        menu = pystray.Menu(
            pystray.MenuItem("Open", self.show_window),
            pystray.MenuItem("Quit", self.on_exit)
        )
        return pystray.Icon("keyboard", image, "Keyboard", menu)

    def hide_to_tray(self, *args):
        """Hide the window and show the tray icon."""
        self.withdraw()
        if not self.tray_icon.visible:
            self.tray_icon.run_detached()

    def start_move(self, event):
        self._drag_offset_x = event.x
        self._drag_offset_y = event.y

    def do_move(self, event):
        x = event.x_root - self._drag_offset_x
        y = event.y_root - self._drag_offset_y
        self.geometry(f"+{x}+{y}")

    def toggle_maximize(self):
        if not self._is_maximized:
            self._normal_geometry = self.geometry()
            w = self.winfo_screenwidth()
            h = self.winfo_screenheight()
            self.geometry(f"{w}x{h}+0+0")
            self._is_maximized = True
        else:
            if self._normal_geometry:
                self.geometry(self._normal_geometry)
            self._is_maximized = False

    def on_minimize(self, event):
        if self.state() == "iconic":
            self.hide_to_tray()

    def show_window(self, icon=None, item=None):
        self.deiconify()
        if self.tray_icon.visible:
            self.tray_icon.stop()

    def on_exit(self, icon=None, item=None):
        """Disconnect from OBS if connected and close the application."""
        if getattr(self, "obs", None):
            try:
                self.obs.disconnect()
            except Exception as e:
                print(f"OBS disconnect error: {e}")
        if self.tray_icon.visible:
            self.tray_icon.stop()
        self.destroy()

    # Backwards compatibility for older tray icons that may still reference
    # on_quit
    def on_quit(self, icon=None, item=None):
        self.on_exit(icon, item)

    def run(self):
        self.mainloop()

if __name__ == "__main__":
    gui = KeyboardGUI()
    gui.run()
