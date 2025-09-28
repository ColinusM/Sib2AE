#!/usr/bin/env python3
"""
GUI Settings Management
Handles window settings, file paths, and configuration
"""

import json
import os
from pathlib import Path

class GUISettings:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.settings_file = Path(__file__).parent / "gui_settings.json"

        # Default file paths - updated for new Brain/ structure and outputs/ organization
        base_dir = self.project_root / "Brain" / "Base"
        self.default_musicxml = str(base_dir / "SS 9.musicxml")
        self.default_svg = str(base_dir / "SS 9 full.svg")
        self.default_midi = str(base_dir / "Saint-Saens Trio No 2.mid")
        self.default_midi_notes = str(self.project_root / "outputs" / "midi")
        self.default_audio_dir = str(self.project_root / "outputs" / "audio")

        # Window settings
        self.window_width = 800
        self.window_height = 600
        self.window_x = 100
        self.window_y = 100

        self.load_settings()

    def load_settings(self):
        """Load window and app settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.window_width = settings.get('width', 800)
                    self.window_height = settings.get('height', 600)
                    self.window_x = settings.get('x', 100)
                    self.window_y = settings.get('y', 100)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self, root):
        """Save current window settings"""
        try:
            settings = {
                'width': root.winfo_width(),
                'height': root.winfo_height(),
                'x': root.winfo_x(),
                'y': root.winfo_y()
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def check_files_exist(self):
        """Check if default files exist and return status"""
        files = [
            ("MusicXML", self.default_musicxml),
            ("SVG", self.default_svg),
            ("MIDI", self.default_midi),
            ("Audio Dir", self.default_audio_dir)
        ]

        status = []
        for name, path in files:
            exists = os.path.exists(path)
            status.append((name, path, exists))

        return status