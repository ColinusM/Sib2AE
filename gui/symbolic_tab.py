#!/usr/bin/env python3
"""
Symbolic Pipeline Tab
"""

import tkinter as tk
from tkinter import ttk, filedialog
from .script_runner import ScriptRunner

class SymbolicTab:
    def __init__(self, parent_frame, settings, log_callback=None):
        self.frame = parent_frame
        self.settings = settings
        self.log_callback = log_callback
        self.runner = ScriptRunner(log_callback)

        # Variables for file paths
        self.musicxml_var = tk.StringVar(value=settings.default_musicxml)
        self.svg_var = tk.StringVar(value=settings.default_svg)
        self.output_var = tk.StringVar(value="outputs/svg/instruments")

        self.setup_ui()

    def setup_ui(self):
        """Setup the symbolic pipeline tab UI"""
        # File selection frame
        files_frame = ttk.LabelFrame(self.frame, text="Input Files")
        files_frame.pack(fill='x', padx=5, pady=5)

        # MusicXML file
        ttk.Label(files_frame, text="MusicXML:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(files_frame, textvariable=self.musicxml_var, width=50).grid(row=0, column=1, padx=5, pady=2, sticky='ew')
        ttk.Button(files_frame, text="Browse", command=self.browse_musicxml).grid(row=0, column=2, padx=2, pady=2)

        # SVG file
        ttk.Label(files_frame, text="SVG:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(files_frame, textvariable=self.svg_var, width=50).grid(row=1, column=1, padx=5, pady=2, sticky='ew')
        ttk.Button(files_frame, text="Browse", command=self.browse_svg).grid(row=1, column=2, padx=2, pady=2)

        # Output directory
        ttk.Label(files_frame, text="Output:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(files_frame, textvariable=self.output_var, width=50).grid(row=2, column=1, padx=5, pady=2, sticky='ew')
        ttk.Button(files_frame, text="Browse", command=self.browse_output).grid(row=2, column=2, padx=2, pady=2)

        files_frame.columnconfigure(1, weight=1)

        # Scripts frame
        scripts_frame = ttk.LabelFrame(self.frame, text="Symbolic Pipeline Scripts")
        scripts_frame.pack(fill='x', padx=5, pady=5)

        # Script buttons
        scripts = [
            ("Extract Noteheads", "truly_universal_noteheads_extractor.py", self.run_noteheads_extractor),
            ("Remove Noteheads", "truly_universal_noteheads_subtractor.py", self.run_noteheads_subtractor),
            ("Separate Instruments", "xml_based_instrument_separator.py", self.run_instrument_separator),
            ("Individual Noteheads", "individual_noteheads_creator.py", self.run_individual_noteheads),
        ]

        for i, (name, script, command) in enumerate(scripts):
            ttk.Button(scripts_frame, text=name, command=command, width=20).grid(
                row=i//2, column=i%2, padx=5, pady=2, sticky='ew')

        # Configure grid
        scripts_frame.columnconfigure(0, weight=1)
        scripts_frame.columnconfigure(1, weight=1)

    def browse_musicxml(self):
        filename = filedialog.askopenfilename(title="Select MusicXML", filetypes=[("MusicXML", "*.musicxml")])
        if filename:
            self.musicxml_var.set(filename)

    def browse_svg(self):
        filename = filedialog.askopenfilename(title="Select SVG", filetypes=[("SVG", "*.svg")])
        if filename:
            self.svg_var.set(filename)

    def browse_output(self):
        dirname = filedialog.askdirectory(title="Select Output Directory")
        if dirname:
            self.output_var.set(dirname)

    def run_noteheads_extractor(self):
        args = [self.musicxml_var.get()]
        self.runner.run_symbolic_script("truly_universal_noteheads_extractor.py", args)

    def run_noteheads_subtractor(self):
        args = [self.musicxml_var.get(), self.svg_var.get()]
        self.runner.run_symbolic_script("truly_universal_noteheads_subtractor.py", args)

    def run_instrument_separator(self):
        args = [self.musicxml_var.get(), self.svg_var.get(), self.output_var.get()]
        self.runner.run_symbolic_script("xml_based_instrument_separator.py", args)

    def run_individual_noteheads(self):
        args = [self.musicxml_var.get()]
        self.runner.run_symbolic_script("individual_noteheads_creator.py", args)