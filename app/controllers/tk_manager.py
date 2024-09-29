# tk_manager.py

import tkinter as tk

class TkinterAppManager:
    def __init__(self):
        self.root = None

    def run_tkinter_app(self, app_func, *args, **kwargs):
        """Run the Tkinter app with a single root window"""
        if self.root is None:
            self.root = tk.Tk()
            self.root.withdraw()  # Start hidden
        app_func(self.root, *args, **kwargs)

    def create_window(self, title="New Window"):
        """Create a new Toplevel window"""
        if self.root is None:
            self.root = tk.Tk()
            self.root.withdraw()

        window = tk.Toplevel(self.root)
        window.title(title)
        return window

# Create a global instance
tk_manager = TkinterAppManager()
