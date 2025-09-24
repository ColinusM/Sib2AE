#!/usr/bin/env python3
"""
Sib2Ae Simple GUI - Modular, clean interface for music notation pipeline
Simplified version with only Symbolic and Audio tabs, no master pipeline
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import os
import sys
from pathlib import Path

# Import modules from same directory
from .settings import GUISettings
from .symbolic_tab import SymbolicTab
from .audio_tab import AudioTab
from .matching_tab import MatchingTab

# SVG viewer functionality removed for simplicity
SVGViewerClass = None

class Sib2AeSimpleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sib2Ae Pipeline - Simple")

        # Initialize settings
        self.settings = GUISettings()

        # Set working directory
        os.chdir(self.settings.project_root)

        # Configure window
        self.root.geometry(f"{self.settings.window_width}x{self.settings.window_height}+{self.settings.window_x}+{self.settings.window_y}")
        self.root.attributes('-topmost', True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # SVG viewer reference
        self.svg_viewer = None

        self.setup_ui()
        self.check_files()


    def setup_ui(self):
        """Setup the main UI"""
        # Toolbar
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.pack(fill='x', padx=5, pady=2)

        ttk.Button(toolbar_frame, text="📁 Open Output", command=self.open_output).pack(side='left', padx=2)
        ttk.Button(toolbar_frame, text="📋 Check Files", command=self.check_files).pack(side='left', padx=2)

        # Main notebook
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=5, pady=2)

        # Symbolic Pipeline Tab
        symbolic_frame = ttk.Frame(notebook)
        notebook.add(symbolic_frame, text="Symbolic Pipeline")
        self.symbolic_tab = SymbolicTab(symbolic_frame, self.settings, self.log)

        # Audio Pipeline Tab
        audio_frame = ttk.Frame(notebook)
        notebook.add(audio_frame, text="Audio Pipeline")
        self.audio_tab = AudioTab(audio_frame, self.settings, self.log)

        # Matching Tab
        matching_frame = ttk.Frame(notebook)
        notebook.add(matching_frame, text="MIDI-XML-SVG Matching")
        self.matching_tab = MatchingTab(matching_frame, self.settings, self.log)

        # Log Tab
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Output Log")
        self.setup_log_tab(log_frame)

    def setup_log_tab(self, parent):
        """Setup the log tab"""
        self.log_text = scrolledtext.ScrolledText(parent, height=20, font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Clear button
        ttk.Button(parent, text="Clear Log", command=self.clear_log).pack(pady=2)

        # Initial messages
        self.log("🚀 Sib2Ae Simple GUI initialized")
        self.log(f"📁 Working directory: {os.getcwd()}")

    def log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)

    def check_files(self):
        """Check if default files exist and log status"""
        self.log("\n📁 Checking default file paths:")
        file_status = self.settings.check_files_exist()

        for name, path, exists in file_status:
            status = "✅" if exists else "❌"
            self.log(f"{status} {name}: {path}")

    def open_output(self):
        """Open output directories"""
        import subprocess
        import platform

        output_dirs = [
            "PRPs-agentic-eng/Audio",
            "PRPs-agentic-eng/instruments_output",
            "universal_output"
        ]

        for output_dir in output_dirs:
            if os.path.exists(output_dir):
                try:
                    if platform.system() == "Darwin":  # macOS
                        subprocess.run(["open", output_dir])
                    elif platform.system() == "Windows":
                        subprocess.run(["explorer", output_dir])
                    else:  # Linux
                        subprocess.run(["xdg-open", output_dir])
                    self.log(f"📂 Opened: {output_dir}")
                except Exception as e:
                    self.log(f"❌ Error opening {output_dir}: {e}")


    def on_closing(self):
        """Handle window close"""
        self.settings.save_settings(self.root)
        self.root.destroy()

def main():
    root = tk.Tk()
    app = Sib2AeSimpleGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()