#!/usr/bin/env python3
"""
Sib2Ae GUI - Graphical interface for running music notation to After Effects pipeline scripts

This GUI provides an easy-to-use interface for executing all Sib2Ae pipeline scripts
with the correct file paths and parameters.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import json
from pathlib import Path

# Import SVG viewer windows
try:
    from svg_viewer_webview import SVGViewerWebView
    SVGViewerClass = SVGViewerWebView
except ImportError:
    try:
        from svg_viewer_window import SVGViewerWindow
        SVGViewerClass = SVGViewerWindow
    except ImportError:
        SVGViewerClass = None

class Sib2AeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sib2Ae Pipeline GUI")

        # Set working directory to project root
        self.project_root = Path(__file__).parent
        os.chdir(self.project_root)

        # Settings file for window preferences
        self.settings_file = self.project_root / "gui_settings.json"

        # Load saved window settings or use defaults (much more compact)
        self.load_window_settings()

        # Make window always on top (especially useful on macOS)
        self.root.attributes('-topmost', True)

        # Optional: Allow user to toggle always on top
        self.always_on_top = True

        # Bind window close event to save settings
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Default file paths from the codebase (use absolute paths)
        base_dir = self.project_root / "PRPs-agentic-eng" / "Base"
        self.default_musicxml = str(base_dir / "SS 9.musicxml")
        self.default_svg = str(base_dir / "SS 9 full.svg")
        self.default_midi = str(base_dir / "Saint-Saens Trio No 2.mid")
        self.default_midi_notes = str(base_dir / "Saint-Saens Trio No 2_individual_notes")
        self.default_audio_dir = str(self.project_root / "PRPs-agentic-eng" / "Audio")

        # SVG viewer window reference
        self.svg_viewer = None

        # Context gatherer data
        self.context_analysis = None
        self.midi_mappings = {}

        self.setup_ui()

        # Auto-launch SVG viewer window
        self.auto_launch_svg_viewer()

        # Auto-run context gatherer on launch for faster testing
        self.auto_run_context_gatherer()

    def setup_ui(self):
        # Create top toolbar frame (compact)
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.pack(fill='x', padx=5, pady=2)

        # Add persistent buttons to toolbar
        self.setup_toolbar(toolbar_frame)

        # Create main notebook for tabs (compact)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=5, pady=2)

        # Tab 1: Symbolic Pipeline
        self.symbolic_frame = ttk.Frame(notebook)
        notebook.add(self.symbolic_frame, text="Symbolic Pipeline")
        self.setup_symbolic_tab()

        # Tab 2: Audio Pipeline
        self.audio_frame = ttk.Frame(notebook)
        notebook.add(self.audio_frame, text="Audio Pipeline")
        self.setup_audio_tab()

        # Tab 3: Master Pipeline
        self.master_frame = ttk.Frame(notebook)
        notebook.add(self.master_frame, text="Master Pipeline")
        self.setup_master_tab()

        # Tab 4: Output Log
        self.log_frame = ttk.Frame(notebook)
        notebook.add(self.log_frame, text="Output Log")
        self.setup_log_tab()

    def setup_toolbar(self, parent):
        """Setup the persistent toolbar with commonly used buttons"""
        # Compact title and toolbar buttons
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill='x')

        # Compact project title
        title_label = ttk.Label(title_frame, text="🎵 Sib2Ae", font=('Arial', 10, 'bold'))
        title_label.pack(side='left', pady=1)

        # Compact toolbar buttons frame (right side)
        buttons_frame = ttk.Frame(title_frame)
        buttons_frame.pack(side='right', pady=1)

        # Always on top toggle in toolbar (compact)
        self.always_on_top_var = tk.BooleanVar(value=True)
        always_on_top_cb = ttk.Checkbutton(buttons_frame, text="🔝",
                                          variable=self.always_on_top_var,
                                          command=self.toggle_always_on_top)
        always_on_top_cb.pack(side='right', padx=2)

        # Context Gatherer button (compact)
        context_btn = ttk.Button(buttons_frame, text="🎹", width=3,
                                command=self.run_context_gatherer)
        context_btn.pack(side='right', padx=1)

        # SVG Viewer button (compact)
        svg_viewer_btn = ttk.Button(buttons_frame, text="🔍", width=3,
                                   command=self.launch_svg_viewer)
        svg_viewer_btn.pack(side='right', padx=1)

        # Remember Position button (compact)
        position_btn = ttk.Button(buttons_frame, text="📍", width=3,
                                 command=self.save_current_window_settings)
        position_btn.pack(side='right', padx=1)

        # Clean Base Folder button with trash bin icon (compact)
        clean_btn = ttk.Button(buttons_frame, text="🗑️",
                              command=self.clean_base_folder, width=3)
        clean_btn.pack(side='right', padx=1)

        # Thin separator line
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill='x', pady=1)

    def setup_symbolic_tab(self):
        """Setup the Symbolic Pipeline tab"""
        # Compact file selection frame
        file_frame = ttk.LabelFrame(self.symbolic_frame, text="Files")
        file_frame.pack(fill='x', padx=2, pady=2)

        # MusicXML file (compact)
        ttk.Label(file_frame, text="XML:").grid(row=0, column=0, sticky='w', padx=2, pady=1)
        self.musicxml_var = tk.StringVar(value=self.default_musicxml)
        ttk.Entry(file_frame, textvariable=self.musicxml_var, width=50).grid(row=0, column=1, padx=2, pady=1, sticky='ew')
        ttk.Button(file_frame, text="...", width=3, command=lambda: self.browse_file(self.musicxml_var, "MusicXML files", "*.musicxml")).grid(row=0, column=2, padx=1, pady=1)

        # SVG file (compact)
        ttk.Label(file_frame, text="SVG:").grid(row=1, column=0, sticky='w', padx=2, pady=1)
        self.svg_var = tk.StringVar(value=self.default_svg)
        ttk.Entry(file_frame, textvariable=self.svg_var, width=50).grid(row=1, column=1, padx=2, pady=1, sticky='ew')
        ttk.Button(file_frame, text="...", width=3, command=lambda: self.browse_file(self.svg_var, "SVG files", "*.svg")).grid(row=1, column=2, padx=1, pady=1)

        # Output directory (compact)
        ttk.Label(file_frame, text="Out:").grid(row=2, column=0, sticky='w', padx=2, pady=1)
        self.symbolic_output_var = tk.StringVar(value="symbolic_output")
        ttk.Entry(file_frame, textvariable=self.symbolic_output_var, width=50).grid(row=2, column=1, padx=2, pady=1, sticky='ew')
        ttk.Button(file_frame, text="...", width=3, command=lambda: self.browse_directory(self.symbolic_output_var)).grid(row=2, column=2, padx=1, pady=1)

        # Configure column weights for responsive layout
        file_frame.columnconfigure(1, weight=1)

        # Compact scripts frame
        scripts_frame = ttk.LabelFrame(self.symbolic_frame, text="Scripts")
        scripts_frame.pack(fill='both', expand=True, padx=2, pady=2)

        # Create compact buttons for each symbolic script
        symbolic_scripts = [
            ("Extract Noteheads", "truly_universal_noteheads_extractor.py"),
            ("Subtract Noteheads", "truly_universal_noteheads_subtractor.py"),
            ("Separate Instruments", "xml_based_instrument_separator.py"),
            ("Individual Noteheads", "individual_noteheads_creator.py"),
            ("Staff & Barlines", "staff_barlines_extractor.py")
        ]

        # Create a grid of compact buttons (2 columns)
        for i, (name, script) in enumerate(symbolic_scripts):
            row = i // 2
            col = i % 2
            btn = ttk.Button(scripts_frame, text=name, width=20,
                           command=lambda s=script: self.run_symbolic_script(s))
            btn.grid(row=row, column=col, padx=2, pady=1, sticky='ew')

        # Configure column weights
        scripts_frame.columnconfigure(0, weight=1)
        scripts_frame.columnconfigure(1, weight=1)

    def setup_audio_tab(self):
        """Setup the Audio Pipeline tab"""
        # Compact file selection frame
        file_frame = ttk.LabelFrame(self.audio_frame, text="Files")
        file_frame.pack(fill='x', padx=2, pady=2)

        # MIDI file (compact)
        ttk.Label(file_frame, text="MIDI:").grid(row=0, column=0, sticky='w', padx=2, pady=1)
        self.midi_var = tk.StringVar(value=self.default_midi)
        ttk.Entry(file_frame, textvariable=self.midi_var, width=50).grid(row=0, column=1, padx=2, pady=1, sticky='ew')
        ttk.Button(file_frame, text="...", width=3, command=lambda: self.browse_file(self.midi_var, "MIDI files", "*.mid")).grid(row=0, column=2, padx=1, pady=1)

        # MIDI notes directory (compact)
        ttk.Label(file_frame, text="Notes:").grid(row=1, column=0, sticky='w', padx=2, pady=1)
        self.midi_notes_var = tk.StringVar(value=self.default_midi_notes)
        ttk.Entry(file_frame, textvariable=self.midi_notes_var, width=50).grid(row=1, column=1, padx=2, pady=1, sticky='ew')
        ttk.Button(file_frame, text="...", width=3, command=lambda: self.browse_directory(self.midi_notes_var)).grid(row=1, column=2, padx=1, pady=1)

        # Audio directory (compact)
        ttk.Label(file_frame, text="Audio:").grid(row=2, column=0, sticky='w', padx=2, pady=1)
        self.audio_dir_var = tk.StringVar(value=self.default_audio_dir)
        ttk.Entry(file_frame, textvariable=self.audio_dir_var, width=50).grid(row=2, column=1, padx=2, pady=1, sticky='ew')
        ttk.Button(file_frame, text="...", width=3, command=lambda: self.browse_directory(self.audio_dir_var)).grid(row=2, column=2, padx=1, pady=1)

        # Configure column weights
        file_frame.columnconfigure(1, weight=1)

        # Compact scripts frame
        scripts_frame = ttk.LabelFrame(self.audio_frame, text="Scripts")
        scripts_frame.pack(fill='both', expand=True, padx=2, pady=2)

        # Create compact buttons for each audio script
        audio_scripts = [
            ("Separate MIDI", "midi_note_separator.py"),
            ("Render Audio (Fast)", "midi_to_audio_renderer_fast.py"),
            ("Render Audio", "midi_to_audio_renderer.py"),
            ("Keyframes (Fast)", "audio_to_keyframes_fast.py"),
            ("Keyframes", "audio_to_keyframes.py")
        ]

        # Create a grid of compact buttons (2 columns)
        for i, (name, script) in enumerate(audio_scripts):
            row = i // 2
            col = i % 2
            btn = ttk.Button(scripts_frame, text=name, width=20,
                           command=lambda s=script: self.run_audio_script(s))
            btn.grid(row=row, column=col, padx=2, pady=1, sticky='ew')

        # Configure column weights
        scripts_frame.columnconfigure(0, weight=1)
        scripts_frame.columnconfigure(1, weight=1)

    def setup_master_tab(self):
        """Setup the Master Pipeline tab"""
        # Compact settings frame
        settings_frame = ttk.LabelFrame(self.master_frame, text="Settings")
        settings_frame.pack(fill='x', padx=2, pady=2)

        # Base name (compact)
        ttk.Label(settings_frame, text="Base:").grid(row=0, column=0, sticky='w', padx=2, pady=1)
        self.base_name_var = tk.StringVar(value="SS 9")
        ttk.Entry(settings_frame, textvariable=self.base_name_var, width=15).grid(row=0, column=1, padx=2, pady=1)

        # Output directory (compact)
        ttk.Label(settings_frame, text="Output:").grid(row=1, column=0, sticky='w', padx=2, pady=1)
        self.master_output_var = tk.StringVar(value="master_output")
        ttk.Entry(settings_frame, textvariable=self.master_output_var, width=25).grid(row=1, column=1, padx=2, pady=1, sticky='ew')
        ttk.Button(settings_frame, text="...", width=3, command=lambda: self.browse_directory(self.master_output_var)).grid(row=1, column=2, padx=1, pady=1)

        settings_frame.columnconfigure(1, weight=1)

        # Compact master pipeline button
        master_frame = ttk.LabelFrame(self.master_frame, text="Workflow")
        master_frame.pack(fill='x', padx=2, pady=2)

        ttk.Button(master_frame, text="🚀 Run Master Pipeline",
                  command=self.run_master_pipeline,
                  style='Accent.TButton').pack(pady=5)

        # Synchronization buttons frame
        sync_frame = ttk.LabelFrame(self.master_frame, text="MIDI-XML-SVG Synchronization")
        sync_frame.pack(fill='x', padx=2, pady=2)

        # Create buttons in a row
        button_frame = ttk.Frame(sync_frame)
        button_frame.pack(fill='x', padx=2, pady=2)

        ttk.Button(button_frame, text="🎹 Simple Sync (Note Coordinator)",
                  command=self.run_note_coordinator,
                  width=30).grid(row=0, column=0, padx=2, pady=2)

        ttk.Button(button_frame, text="🎯 Advanced Sync (Context Gatherer)",
                  command=self.run_context_gatherer,
                  width=30).grid(row=0, column=1, padx=2, pady=2)

        # Configure columns for equal width
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        # Compact quick actions frame
        quick_frame = ttk.LabelFrame(self.master_frame, text="Actions")
        quick_frame.pack(fill='x', padx=2, pady=2)

        quick_actions = [
            ("📁 Output", self.open_output_directory),
            ("📋 Files", self.view_generated_files),
            ("🔍 Deps", self.check_dependencies)
        ]

        # Arrange in a row for compactness
        for i, (name, command) in enumerate(quick_actions):
            ttk.Button(quick_frame, text=name, command=command, width=12).grid(row=0, column=i, padx=2, pady=2)

        # Configure columns
        for i in range(len(quick_actions)):
            quick_frame.columnconfigure(i, weight=1)

    def setup_log_tab(self):
        """Setup the Output Log tab"""
        # Compact log display
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=15, width=80, font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True, padx=2, pady=2)

        # Compact clear button
        ttk.Button(self.log_frame, text="Clear", command=self.clear_log, width=10).pack(pady=2)

        # Initial log message
        self.log("Sib2Ae Pipeline GUI initialized")
        self.log(f"Working directory: {os.getcwd()}")

        # Check if default files exist
        self.check_default_files()

    def browse_file(self, var, title, filetypes):
        """Browse for a file"""
        filename = filedialog.askopenfilename(title=f"Select {title}", filetypes=[(title, filetypes)])
        if filename:
            var.set(filename)

    def browse_directory(self, var):
        """Browse for a directory"""
        directory = filedialog.askdirectory(title="Select Directory")
        if directory:
            var.set(directory)

    def log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)

    def check_default_files(self):
        """Check if default files exist and log status"""
        files_to_check = [
            ("MusicXML", self.default_musicxml),
            ("SVG", self.default_svg),
            ("MIDI", self.default_midi),
            ("MIDI Notes Dir", self.default_midi_notes),
            ("Audio Dir", self.default_audio_dir)
        ]

        self.log("\n📁 Checking default file paths:")
        for name, path in files_to_check:
            if os.path.exists(path):
                self.log(f"✅ {name}: {path}")
            else:
                self.log(f"❌ {name}: NOT FOUND - {path}")

        self.log("")

    def run_command(self, command, description):
        """Run a command in a separate thread"""
        def run():
            try:
                self.log(f"\n🔄 {description}")
                self.log(f"Command: {' '.join(command)}")
                self.log("-" * 50)

                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

                for line in iter(process.stdout.readline, ''):
                    if line:
                        self.log(line.strip())

                process.wait()

                if process.returncode == 0:
                    self.log(f"✅ {description} completed successfully")
                else:
                    self.log(f"❌ {description} failed with return code {process.returncode}")

            except Exception as e:
                self.log(f"❌ Error running {description}: {str(e)}")

            self.log("-" * 50)

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def run_symbolic_script(self, script_name):
        """Run a symbolic processing script"""
        script_path = f"PRPs-agentic-eng/App/Symbolic Separators/{script_name}"

        if script_name == "truly_universal_noteheads_extractor.py":
            command = ["python", script_path, self.musicxml_var.get()]
        elif script_name == "truly_universal_noteheads_subtractor.py":
            command = ["python", script_path, self.musicxml_var.get(), self.svg_var.get()]
        elif script_name == "xml_based_instrument_separator.py":
            command = ["python", script_path, self.musicxml_var.get(), self.svg_var.get(), self.symbolic_output_var.get()]
        elif script_name == "individual_noteheads_creator.py":
            command = ["python", script_path, self.musicxml_var.get()]
        elif script_name == "staff_barlines_extractor.py":
            command = ["python", script_path, self.musicxml_var.get(), self.svg_var.get()]
        else:
            self.log(f"❌ Unknown script: {script_name}")
            return

        self.run_command(command, f"Symbolic Script: {script_name}")

    def run_audio_script(self, script_name):
        """Run an audio processing script"""
        script_path = f"PRPs-agentic-eng/App/Audio Separators/{script_name}"

        if script_name == "midi_note_separator.py":
            command = ["python", script_path, self.midi_var.get()]
        elif "midi_to_audio_renderer" in script_name:
            command = ["python", script_path, self.midi_notes_var.get()]
        elif "audio_to_keyframes" in script_name:
            command = ["python", script_path, self.audio_dir_var.get()]
        else:
            self.log(f"❌ Unknown script: {script_name}")
            return

        self.run_command(command, f"Audio Script: {script_name}")

    def run_master_pipeline(self):
        """Run the master pipeline"""
        script_path = "PRPs-agentic-eng/App/Symbolic Separators/sib2ae_master_pipeline.py"
        command = ["python", script_path, self.base_name_var.get(), self.master_output_var.get()]
        self.run_command(command, "Master Pipeline")

    def open_output_directory(self):
        """Open the output directory in file manager"""
        output_dir = self.master_output_var.get()
        if os.path.exists(output_dir):
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", output_dir])
            elif sys.platform == "win32":  # Windows
                subprocess.run(["explorer", output_dir])
            else:  # Linux
                subprocess.run(["xdg-open", output_dir])
        else:
            messagebox.showwarning("Directory Not Found", f"Output directory does not exist: {output_dir}")

    def view_generated_files(self):
        """Show information about generated files"""
        info = []

        # Check for various output files
        directories_to_check = [
            ("Audio files", self.audio_dir_var.get()),
            ("Instrument SVGs", "PRPs-agentic-eng/instruments_output"),
            ("Master output", self.master_output_var.get()),
            ("Universal output", "PRPs-agentic-eng/universal_output")
        ]

        for name, directory in directories_to_check:
            if os.path.exists(directory):
                files = os.listdir(directory)
                info.append(f"{name}: {len(files)} items in {directory}")
            else:
                info.append(f"{name}: Directory not found ({directory})")

        messagebox.showinfo("Generated Files", "\n".join(info))

    def check_dependencies(self):
        """Check if required dependencies are available"""
        dependencies = [
            ("Python", "python", "--version"),
            ("FluidSynth", "fluidsynth", "--version")
        ]

        results = []
        for name, command, flag in dependencies:
            try:
                result = subprocess.run([command, flag], capture_output=True, text=True)
                if result.returncode == 0:
                    version = result.stdout.strip() or result.stderr.strip()
                    results.append(f"✅ {name}: {version}")
                else:
                    results.append(f"❌ {name}: Not available")
            except FileNotFoundError:
                results.append(f"❌ {name}: Not found")

        messagebox.showinfo("Dependencies Check", "\n".join(results))

    def clean_base_folder(self):
        """Clean generated files from Base folder while keeping main source files"""
        base_dir = self.project_root / "PRPs-agentic-eng" / "Base"

        # Main source files to KEEP (never delete these)
        source_files = {
            "SS 9.musicxml",  # Source MusicXML
            "SS 9 full.svg",  # Source SVG
            "Saint-Saens Trio No 2.mid"  # Source MIDI
        }

        # Generated files/patterns to CLEAN (safe to delete)
        clean_patterns = [
            "*_noteheads_universal.svg",
            "*_staff_barlines.svg",
            "*noteheads-onlyTRUTH.svg",
            "*_master_timing.json",
            "*_individual_notes",  # directory
            "*_without_noteheads.svg",
            ".DS_Store"
        ]

        if not base_dir.exists():
            messagebox.showwarning("Directory Not Found", f"Base directory not found: {base_dir}")
            return

        # Ask for confirmation
        result = messagebox.askyesno(
            "Clean Base Folder",
            f"This will remove generated files from:\n{base_dir}\n\n"
            f"Source files will be KEPT:\n• {chr(10).join(source_files)}\n\n"
            "Generated files will be REMOVED.\n\nContinue?"
        )

        if not result:
            return

        self.log("\n🧹 Cleaning Base folder...")
        self.log(f"Directory: {base_dir}")

        import glob
        import shutil

        cleaned_count = 0
        kept_count = 0

        try:
            # Get all items in base directory
            for item in base_dir.iterdir():
                item_name = item.name

                # Always keep source files
                if item_name in source_files:
                    self.log(f"✅ KEPT: {item_name}")
                    kept_count += 1
                    continue

                # Check if item matches clean patterns
                should_clean = False
                for pattern in clean_patterns:
                    if item.match(pattern):
                        should_clean = True
                        break

                if should_clean:
                    try:
                        if item.is_file():
                            item.unlink()
                            self.log(f"🗑️  REMOVED FILE: {item_name}")
                        elif item.is_dir():
                            shutil.rmtree(item)
                            self.log(f"🗑️  REMOVED DIR: {item_name}/")
                        cleaned_count += 1
                    except Exception as e:
                        self.log(f"❌ Failed to remove {item_name}: {e}")
                else:
                    self.log(f"⚠️  UNKNOWN FILE (kept): {item_name}")
                    kept_count += 1

            self.log(f"\n✅ Base folder cleaning complete!")
            self.log(f"📊 Files kept: {kept_count}")
            self.log(f"🗑️  Files removed: {cleaned_count}")

            # Show success message
            messagebox.showinfo(
                "Cleaning Complete",
                f"Base folder cleaned successfully!\n\n"
                f"Files kept: {kept_count}\n"
                f"Files removed: {cleaned_count}"
            )

        except Exception as e:
            error_msg = f"Error cleaning base folder: {e}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("Cleaning Error", error_msg)

    def toggle_always_on_top(self):
        """Toggle the always on top setting"""
        self.always_on_top = self.always_on_top_var.get()
        self.root.attributes('-topmost', self.always_on_top)

        # Log the change
        status = "enabled" if self.always_on_top else "disabled"
        self.log(f"🔝 Always on top {status}")

    def load_window_settings(self):
        """Load window settings from file or use defaults"""
        default_settings = {
            "geometry": "700x500+100+100",  # Much more compact: width x height + x_offset + y_offset
            "always_on_top": True
        }

        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)

                # Validate settings and use defaults if invalid
                geometry = settings.get("geometry", default_settings["geometry"])
                always_on_top = settings.get("always_on_top", default_settings["always_on_top"])

                self.root.geometry(geometry)
                self.always_on_top = always_on_top

                print(f"✅ Loaded window settings: {geometry}")
            else:
                # Use defaults for first run
                self.root.geometry(default_settings["geometry"])
                self.always_on_top = default_settings["always_on_top"]
                print(f"📋 Using default window settings: {default_settings['geometry']}")

        except Exception as e:
            # Fall back to defaults if there's any error
            self.root.geometry(default_settings["geometry"])
            self.always_on_top = default_settings["always_on_top"]
            print(f"⚠️ Error loading settings, using defaults: {e}")

    def save_current_window_settings(self):
        """Save current window position and size as new defaults"""
        try:
            # Get current window geometry
            current_geometry = self.root.geometry()
            current_always_on_top = self.always_on_top_var.get()

            settings = {
                "geometry": current_geometry,
                "always_on_top": current_always_on_top
            }

            # Save to settings file
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            self.log(f"💾 Window position saved: {current_geometry}")
            self.log(f"   Always on top: {'enabled' if current_always_on_top else 'disabled'}")

            messagebox.showinfo(
                "Position Saved",
                f"Current window position and size saved!\n\n"
                f"Position: {current_geometry}\n"
                f"Always on top: {'Enabled' if current_always_on_top else 'Disabled'}\n\n"
                f"This will be the default position when the GUI opens next time."
            )

        except Exception as e:
            error_msg = f"Error saving window settings: {e}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("Save Error", error_msg)

    def auto_launch_svg_viewer(self):
        """Automatically launch the SVG viewer window on startup"""
        if SVGViewerClass is None:
            self.log("⚠️ SVG Viewer not available")
            return

        try:
            # Look for the best SVG file to display (processed versions first)
            svg_file = self.find_best_svg_file()

            # Launch SVG viewer window and keep reference
            self.svg_viewer = SVGViewerClass(parent_callback=self.log)

            # Show the SVG file in a separate process for webview
            if svg_file:
                self.svg_viewer.show_in_subprocess(svg_file)
                self.log(f"🔍 SVG Viewer auto-launched with {os.path.basename(svg_file)}")
            else:
                self.svg_viewer.show_in_subprocess()
                self.log(f"🔍 SVG Viewer auto-launched (no SVG file)")

        except Exception as e:
            self.log(f"❌ Error auto-launching SVG viewer: {str(e)}")

    def find_best_svg_file(self):
        """Find the best SVG file to display (processed versions preferred)"""
        # Priority order: noteheads subtracted > staff+barlines only > original full
        base_name = "SS 9"

        # Look for processed versions first
        candidates = [
            # Noteheads subtracted (best for viewing structure)
            f"PRPs-agentic-eng/Base/{base_name} full_without_noteheads.svg",
            f"PRPs-agentic-eng/{base_name}_without_noteheads.svg",
            f"symbolic_output/{base_name}_without_noteheads.svg",

            # Staff and barlines only (good for structure)
            f"PRPs-agentic-eng/Base/{base_name} full_staff_barlines_only.svg",
            f"PRPs-agentic-eng/{base_name}_staff_barlines_only.svg",
            f"symbolic_output/{base_name}_staff_barlines_only.svg",

            # Original full SVG (fallback)
            self.default_svg
        ]

        for candidate in candidates:
            full_path = str(self.project_root / candidate)
            if os.path.exists(full_path):
                if "without_noteheads" in candidate:
                    self.log(f"📋 Using noteheads-subtracted SVG for better analysis")
                elif "staff_barlines" in candidate:
                    self.log(f"📐 Using staff+barlines-only SVG for structure view")
                else:
                    self.log(f"📄 Using original full SVG")
                return full_path

        return None

    def launch_svg_viewer(self):
        """Launch the SVG viewer window (manual trigger)"""
        if SVGViewerClass is None:
            messagebox.showerror("Error", "SVG Viewer not available.")
            return

        # If SVG viewer already exists and is a webview, focus the window (if possible)
        if self.svg_viewer and hasattr(self.svg_viewer, 'window'):
            try:
                # For webview, we can't easily bring to front, so create new instance
                self.log("🔍 Creating new SVG Viewer instance")
            except:
                pass

        try:
            # Get current SVG file from the symbolic tab
            svg_file = self.svg_var.get()

            # If no SVG selected or doesn't exist, use default
            if not svg_file or not os.path.exists(svg_file):
                svg_file = self.default_svg

            # Launch new SVG viewer window
            self.svg_viewer = SVGViewerClass(parent_callback=self.log)

            # Pass MIDI mappings if available
            if self.midi_mappings:
                self.svg_viewer.midi_mappings = self.midi_mappings
                self.log(f"🎹 Loaded {len(self.midi_mappings)} MIDI mappings into SVG viewer")

            # Show the SVG file in a separate process for webview
            if os.path.exists(svg_file):
                # For webview with MIDI mappings, we need to use the enhanced show method
                if self.midi_mappings:
                    # Can't pass MIDI data to subprocess - need direct show
                    self.svg_viewer.show(svg_file, self.default_musicxml, self.default_midi)
                else:
                    self.svg_viewer.show_in_subprocess(svg_file)
                self.log(f"🔍 SVG Viewer launched with {os.path.basename(svg_file)}")
            else:
                self.svg_viewer.show_in_subprocess()
                self.log(f"🔍 SVG Viewer launched (no SVG file)")

        except Exception as e:
            error_msg = f"Error launching SVG viewer: {str(e)}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("SVG Viewer Error", error_msg)

    def save_settings_on_close(self):
        """Automatically save settings when window is closed"""
        try:
            current_geometry = self.root.geometry()
            current_always_on_top = self.always_on_top_var.get()

            settings = {
                "geometry": current_geometry,
                "always_on_top": current_always_on_top
            }

            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            print(f"💾 Auto-saved window settings on close: {current_geometry}")

        except Exception as e:
            print(f"⚠️ Error auto-saving settings: {e}")

    def run_note_coordinator(self):
        """Run the simple note coordinator synchronization system"""
        try:
            self.log("🎹 Running Note Coordinator...")

            # Use default file paths
            musicxml_path = self.default_musicxml
            midi_path = self.default_midi
            output_dir = "universal_output"

            # Validate files exist
            if not os.path.exists(musicxml_path):
                self.log(f"❌ MusicXML file not found: {musicxml_path}")
                return
            if not os.path.exists(midi_path):
                self.log(f"❌ MIDI file not found: {midi_path}")
                return

            # Run in background thread
            def run_coordination():
                try:
                    # Build command
                    cmd = [
                        sys.executable,
                        "PRPs-agentic-eng/note_coordinator.py",
                        musicxml_path,
                        midi_path,
                        output_dir
                    ]

                    self.log(f"📊 Running: {' '.join(cmd)}")

                    # Run the command
                    result = subprocess.run(cmd, capture_output=True, text=True)

                    if result.returncode == 0:
                        self.log(f"✅ Note Coordinator completed successfully!")
                        self.log(f"📁 Output directory: {output_dir}")

                        # Load the universal registry for SVG viewer
                        registry_path = os.path.join(output_dir, "universal_notes_registry.json")
                        if os.path.exists(registry_path):
                            with open(registry_path, 'r') as f:
                                registry_data = json.load(f)

                            # Convert to MIDI mappings format for SVG viewer
                            self.midi_mappings = {}
                            for note in registry_data.get('notes', []):
                                # Note Coordinator uses nested structure
                                svg_data = note.get('svg_data', {})
                                midi_data = note.get('midi_data')

                                # Skip notes with null MIDI data
                                if midi_data is None:
                                    continue

                                if 'svg_x' in svg_data and 'svg_y' in svg_data and 'start_time_seconds' in midi_data:
                                    coord_key = f"{int(svg_data['svg_x'])}_{int(svg_data['svg_y'])}"
                                    self.log(f"🗝️  Mapping key: {coord_key} -> {midi_data['start_time_seconds']:.2f}s")
                                    self.midi_mappings[coord_key] = {
                                        'start_time': midi_data['start_time_seconds'],
                                        'end_time': midi_data.get('end_time_seconds', midi_data['start_time_seconds'] + 1),
                                        'velocity': midi_data.get('velocity', 64),
                                        'pitch': midi_data.get('pitch_midi', 60),
                                        'confidence': note.get('match_confidence', 1.0),
                                        'timing_source': 'note_coordinator'
                                    }

                            self.log(f"🎹 MIDI mappings loaded: {len(self.midi_mappings)} notes")

                            # Update SVG viewer if it exists
                            if self.svg_viewer and hasattr(self.svg_viewer, 'midi_mappings'):
                                self.svg_viewer.midi_mappings = self.midi_mappings
                                # Update in real-time without restart
                                if hasattr(self.svg_viewer, 'update_midi_mappings'):
                                    try:
                                        mappings_json = json.dumps(self.midi_mappings)
                                        self.svg_viewer.update_midi_mappings(mappings_json)
                                        self.log("🔄 SVG Viewer updated with MIDI mappings (real-time)")
                                    except Exception as e:
                                        self.log(f"⚠️ Real-time update failed: {e}")
                                        self.log("🔄 SVG Viewer updated with MIDI mappings (fallback)")
                                else:
                                    self.log("🔄 SVG Viewer updated with MIDI mappings")

                    else:
                        self.log(f"❌ Note Coordinator failed with return code {result.returncode}")
                        self.log(f"Error output: {result.stderr}")

                except Exception as e:
                    self.log(f"❌ Note Coordinator error: {e}")
                    import traceback
                    traceback.print_exc()

            # Run in background thread
            thread = threading.Thread(target=run_coordination, daemon=True)
            thread.start()

        except Exception as e:
            self.log(f"❌ Failed to start Note Coordinator: {e}")

    def run_context_gatherer(self):
        """Run context gatherer to create XML-MIDI-SVG relationships"""
        try:
            self.log("🎹 Running Context Gatherer...")

            # Use default file paths
            musicxml_path = self.default_musicxml
            midi_path = self.default_midi
            svg_path = self.default_svg

            # Validate files exist
            if not os.path.exists(musicxml_path):
                self.log(f"❌ MusicXML file not found: {musicxml_path}")
                return
            if not os.path.exists(midi_path):
                self.log(f"❌ MIDI file not found: {midi_path}")
                return
            if not os.path.exists(svg_path):
                self.log(f"❌ SVG file not found: {svg_path}")
                return

            # Run in background thread
            def run_analysis():
                try:
                    # Import context gatherer
                    sys.path.append(os.path.join(self.project_root, 'PRPs-agentic-eng', 'App', 'Synchronizer 19-26-28-342'))
                    from context_gatherer import ContextGatherer

                    self.log(f"📊 Analyzing: {os.path.basename(musicxml_path)}")

                    # Create context gatherer
                    gatherer = ContextGatherer(
                        musicxml_path=Path(musicxml_path),
                        midi_path=Path(midi_path),
                        svg_path=Path(svg_path)
                    )

                    # Analyze relationships
                    self.context_analysis = gatherer.analyze_and_create_relationships()

                    # Extract MIDI mappings for SVG viewer
                    self.midi_mappings = {}
                    for sync_note in self.context_analysis.synchronized_notes:
                        if sync_note.midi_note and sync_note.svg_noteheads:
                            midi_data = {
                                'start_time': sync_note.master_start_time_seconds,
                                'end_time': sync_note.master_end_time_seconds,
                                'velocity': sync_note.midi_note.velocity,
                                'pitch': sync_note.midi_note.pitch,
                                'confidence': sync_note.match_confidence,
                                'timing_source': sync_note.timing_source
                            }

                            # Map to coordinates
                            for svg_notehead in sync_note.svg_noteheads:
                                coord_key = f"{int(svg_notehead.coordinates[0])}_{int(svg_notehead.coordinates[1])}"
                                self.midi_mappings[coord_key] = midi_data

                    self.log(f"✅ Context analysis complete!")
                    self.log(f"🎹 MIDI mappings: {len(self.midi_mappings)} notes")
                    self.log(f"🎯 Match rate: {self.context_analysis.timing_accuracy['match_rate']:.1%}")
                    self.log(f"⏱️  Avg timing error: {self.context_analysis.timing_accuracy['average_timing_error_ms']:.1f}ms")

                    # Update SVG viewer if it exists
                    if self.svg_viewer and hasattr(self.svg_viewer, 'midi_mappings'):
                        self.svg_viewer.midi_mappings = self.midi_mappings
                        # Update in real-time without restart
                        if hasattr(self.svg_viewer, 'update_midi_mappings'):
                            try:
                                mappings_json = json.dumps(self.midi_mappings)
                                self.svg_viewer.update_midi_mappings(mappings_json)
                                self.log("🔄 SVG Viewer updated with MIDI mappings (real-time)")
                            except Exception as e:
                                self.log(f"⚠️ Real-time update failed: {e}")
                                self.log("🔄 SVG Viewer updated with MIDI mappings (fallback)")
                        else:
                            self.log("🔄 SVG Viewer updated with MIDI mappings")

                except Exception as e:
                    self.log(f"❌ Context gatherer error: {e}")
                    import traceback
                    traceback.print_exc()

            # Run in background thread
            thread = threading.Thread(target=run_analysis, daemon=True)
            thread.start()

        except Exception as e:
            self.log(f"❌ Failed to start context gatherer: {e}")

    def auto_run_context_gatherer(self):
        """Auto-run context gatherer on GUI launch for faster testing"""
        # Delay a bit to let GUI fully initialize
        self.root.after(2000, self.run_context_gatherer)  # Run after 2 seconds

    def on_closing(self):
        """Handle window close event"""
        # Auto-save current position when closing
        self.save_settings_on_close()

        # Close the application
        self.root.destroy()

def main():
    root = tk.Tk()
    app = Sib2AeGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()