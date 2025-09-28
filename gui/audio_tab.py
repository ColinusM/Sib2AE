#!/usr/bin/env python3
"""
Audio Pipeline Tab
"""

import tkinter as tk
from tkinter import ttk, filedialog
from .script_runner import ScriptRunner

class AudioTab:
    def __init__(self, parent_frame, settings, log_callback=None):
        self.frame = parent_frame
        self.settings = settings
        self.log_callback = log_callback
        self.runner = ScriptRunner(log_callback)

        # Variables for file paths
        self.midi_var = tk.StringVar(value=settings.default_midi)
        self.midi_notes_var = tk.StringVar(value=settings.default_midi_notes)
        self.audio_dir_var = tk.StringVar(value=settings.default_audio_dir)

        self.setup_ui()

    def setup_ui(self):
        """Setup the audio pipeline tab UI"""
        # File selection frame
        files_frame = ttk.LabelFrame(self.frame, text="Input Files & Directories")
        files_frame.pack(fill='x', padx=5, pady=5)

        # MIDI file
        ttk.Label(files_frame, text="MIDI:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(files_frame, textvariable=self.midi_var, width=50).grid(row=0, column=1, padx=5, pady=2, sticky='ew')
        ttk.Button(files_frame, text="Browse", command=self.browse_midi).grid(row=0, column=2, padx=2, pady=2)

        # MIDI notes directory
        ttk.Label(files_frame, text="MIDI Notes:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(files_frame, textvariable=self.midi_notes_var, width=50).grid(row=1, column=1, padx=5, pady=2, sticky='ew')
        ttk.Button(files_frame, text="Browse", command=self.browse_midi_notes).grid(row=1, column=2, padx=2, pady=2)

        # Audio directory
        ttk.Label(files_frame, text="Audio Dir:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(files_frame, textvariable=self.audio_dir_var, width=50).grid(row=2, column=1, padx=5, pady=2, sticky='ew')
        ttk.Button(files_frame, text="Browse", command=self.browse_audio_dir).grid(row=2, column=2, padx=2, pady=2)

        files_frame.columnconfigure(1, weight=1)

        # Scripts frame
        scripts_frame = ttk.LabelFrame(self.frame, text="Audio Pipeline Scripts")
        scripts_frame.pack(fill='x', padx=5, pady=5)

        # Script buttons
        scripts = [
            ("Split MIDI Notes", "midi_note_separator.py", self.run_midi_separator),
            ("Render Audio (Fast)", "midi_to_audio_renderer_fast.py", self.run_audio_fast),
            ("Render Audio (Quality)", "midi_to_audio_renderer_fast.py", self.run_audio_quality),
            ("Generate Keyframes (Fast)", "audio_to_keyframes_fast.py", self.run_keyframes_fast),
            ("Generate Keyframes (Amplitude)", "audio_to_keyframes_fast.py", self.run_keyframes_full),
        ]

        for i, (name, script, command) in enumerate(scripts):
            row = i // 2
            col = i % 2
            ttk.Button(scripts_frame, text=name, command=command, width=25).grid(
                row=row, column=col, padx=5, pady=2, sticky='ew')

        # Configure grid
        scripts_frame.columnconfigure(0, weight=1)
        scripts_frame.columnconfigure(1, weight=1)

    def browse_midi(self):
        filename = filedialog.askopenfilename(title="Select MIDI", filetypes=[("MIDI", "*.mid")])
        if filename:
            self.midi_var.set(filename)

    def browse_midi_notes(self):
        dirname = filedialog.askdirectory(title="Select MIDI Notes Directory")
        if dirname:
            self.midi_notes_var.set(dirname)

    def browse_audio_dir(self):
        dirname = filedialog.askdirectory(title="Select Audio Directory")
        if dirname:
            self.audio_dir_var.set(dirname)

    def run_midi_separator(self):
        args = [self.midi_var.get()]
        self.runner.run_audio_script("midi_note_separator.py", args)

    def run_audio_fast(self):
        args = [self.midi_notes_var.get()]
        self.runner.run_audio_script("midi_to_audio_renderer_fast.py", args)

    def run_audio_quality(self):
        args = [self.midi_notes_var.get()]
        self.runner.run_audio_script("midi_to_audio_renderer_fast.py", args)

    def run_keyframes_fast(self):
        args = [self.audio_dir_var.get()]
        self.runner.run_audio_script("audio_to_keyframes_fast.py", args)

    def run_keyframes_full(self):
        args = [self.audio_dir_var.get()]
        self.runner.run_audio_script("audio_to_keyframes_fast.py", args)