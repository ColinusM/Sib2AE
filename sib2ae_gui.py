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

class Sib2AeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sib2Ae Pipeline GUI")

        # Set working directory to project root
        self.project_root = Path(__file__).parent
        os.chdir(self.project_root)

        # Settings file for window preferences
        self.settings_file = self.project_root / "gui_settings.json"

        # Load saved window settings or use defaults
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

        self.setup_ui()

    def setup_ui(self):
        # Create main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

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

    def setup_symbolic_tab(self):
        """Setup the Symbolic Pipeline tab"""
        # File selection frame
        file_frame = ttk.LabelFrame(self.symbolic_frame, text="Input Files")
        file_frame.pack(fill='x', padx=5, pady=5)

        # MusicXML file
        ttk.Label(file_frame, text="MusicXML File:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.musicxml_var = tk.StringVar(value=self.default_musicxml)
        ttk.Entry(file_frame, textvariable=self.musicxml_var, width=60).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.musicxml_var, "MusicXML files", "*.musicxml")).grid(row=0, column=2, padx=5, pady=2)

        # SVG file
        ttk.Label(file_frame, text="SVG File:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.svg_var = tk.StringVar(value=self.default_svg)
        ttk.Entry(file_frame, textvariable=self.svg_var, width=60).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.svg_var, "SVG files", "*.svg")).grid(row=1, column=2, padx=5, pady=2)

        # Output directory
        ttk.Label(file_frame, text="Output Directory:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.symbolic_output_var = tk.StringVar(value="symbolic_output")
        ttk.Entry(file_frame, textvariable=self.symbolic_output_var, width=60).grid(row=2, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_directory(self.symbolic_output_var)).grid(row=2, column=2, padx=5, pady=2)

        # Scripts frame
        scripts_frame = ttk.LabelFrame(self.symbolic_frame, text="Symbolic Processing Scripts")
        scripts_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create buttons for each symbolic script
        symbolic_scripts = [
            ("Extract Noteheads", "truly_universal_noteheads_extractor.py", "Extract noteheads from MusicXML with pixel-perfect coordinates"),
            ("Subtract Noteheads", "truly_universal_noteheads_subtractor.py", "Remove noteheads from full SVG while preserving other elements"),
            ("Separate Instruments", "xml_based_instrument_separator.py", "Create individual SVG files per instrument"),
            ("Create Individual Noteheads", "individual_noteheads_creator.py", "Create one SVG file per notehead for After Effects"),
            ("Extract Staff & Barlines", "staff_barlines_extractor.py", "Extract only staff lines and barlines (optional)")
        ]

        for i, (name, script, description) in enumerate(symbolic_scripts):
            frame = ttk.Frame(scripts_frame)
            frame.pack(fill='x', padx=5, pady=2)

            btn = ttk.Button(frame, text=f"Run {name}", width=25,
                           command=lambda s=script: self.run_symbolic_script(s))
            btn.pack(side='left', padx=5)

            ttk.Label(frame, text=description, foreground='gray').pack(side='left', padx=10)

    def setup_audio_tab(self):
        """Setup the Audio Pipeline tab"""
        # File selection frame
        file_frame = ttk.LabelFrame(self.audio_frame, text="Input Files")
        file_frame.pack(fill='x', padx=5, pady=5)

        # MIDI file
        ttk.Label(file_frame, text="MIDI File:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.midi_var = tk.StringVar(value=self.default_midi)
        ttk.Entry(file_frame, textvariable=self.midi_var, width=60).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_file(self.midi_var, "MIDI files", "*.mid")).grid(row=0, column=2, padx=5, pady=2)

        # MIDI notes directory
        ttk.Label(file_frame, text="MIDI Notes Dir:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.midi_notes_var = tk.StringVar(value=self.default_midi_notes)
        ttk.Entry(file_frame, textvariable=self.midi_notes_var, width=60).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_directory(self.midi_notes_var)).grid(row=1, column=2, padx=5, pady=2)

        # Audio directory
        ttk.Label(file_frame, text="Audio Directory:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.audio_dir_var = tk.StringVar(value=self.default_audio_dir)
        ttk.Entry(file_frame, textvariable=self.audio_dir_var, width=60).grid(row=2, column=1, padx=5, pady=2)
        ttk.Button(file_frame, text="Browse", command=lambda: self.browse_directory(self.audio_dir_var)).grid(row=2, column=2, padx=5, pady=2)

        # Scripts frame
        scripts_frame = ttk.LabelFrame(self.audio_frame, text="Audio Processing Scripts")
        scripts_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create buttons for each audio script
        audio_scripts = [
            ("Separate MIDI Notes", "midi_note_separator.py", "Split MIDI into individual note files (foundation)"),
            ("Render Audio (Fast)", "midi_to_audio_renderer_fast.py", "Convert MIDI to audio with parallel processing (RECOMMENDED)"),
            ("Render Audio (Standard)", "midi_to_audio_renderer.py", "Convert MIDI to audio with higher quality"),
            ("Generate Keyframes (Fast)", "audio_to_keyframes_fast.py", "Create After Effects keyframes with reduced density (RECOMMENDED)"),
            ("Generate Keyframes (Standard)", "audio_to_keyframes.py", "Create comprehensive After Effects keyframes")
        ]

        for i, (name, script, description) in enumerate(audio_scripts):
            frame = ttk.Frame(scripts_frame)
            frame.pack(fill='x', padx=5, pady=2)

            btn = ttk.Button(frame, text=f"Run {name}", width=25,
                           command=lambda s=script: self.run_audio_script(s))
            btn.pack(side='left', padx=5)

            ttk.Label(frame, text=description, foreground='gray').pack(side='left', padx=10)

    def setup_master_tab(self):
        """Setup the Master Pipeline tab"""
        # Settings frame
        settings_frame = ttk.LabelFrame(self.master_frame, text="Master Pipeline Settings")
        settings_frame.pack(fill='x', padx=5, pady=5)

        # Base name
        ttk.Label(settings_frame, text="Base Name:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.base_name_var = tk.StringVar(value="SS 9")
        ttk.Entry(settings_frame, textvariable=self.base_name_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(settings_frame, text="(e.g., 'SS 9' for 'SS 9.musicxml')", foreground='gray').grid(row=0, column=2, sticky='w', padx=5, pady=5)

        # Output directory
        ttk.Label(settings_frame, text="Output Directory:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.master_output_var = tk.StringVar(value="master_output")
        ttk.Entry(settings_frame, textvariable=self.master_output_var, width=30).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(settings_frame, text="Browse", command=lambda: self.browse_directory(self.master_output_var)).grid(row=1, column=2, padx=5, pady=5)

        # Master pipeline button
        master_frame = ttk.LabelFrame(self.master_frame, text="Complete Workflow")
        master_frame.pack(fill='x', padx=5, pady=10)

        ttk.Button(master_frame, text="Run Master Pipeline",
                  command=self.run_master_pipeline,
                  style='Accent.TButton').pack(pady=10)

        ttk.Label(master_frame,
                 text="Runs the complete 4-tool symbolic pipeline and creates instrument-focused folder structure",
                 foreground='blue').pack(pady=5)

        # Quick actions frame
        quick_frame = ttk.LabelFrame(self.master_frame, text="Quick Actions")
        quick_frame.pack(fill='x', padx=5, pady=5)

        quick_actions = [
            ("Open Output Directory", self.open_output_directory),
            ("View Generated Files", self.view_generated_files),
            ("Check Dependencies", self.check_dependencies),
            ("Clean Base Folder", self.clean_base_folder),
            ("Remember Position", self.save_current_window_settings)
        ]

        for name, command in quick_actions:
            ttk.Button(quick_frame, text=name, command=command).pack(side='left', padx=5, pady=5)

        # Always on top toggle
        self.always_on_top_var = tk.BooleanVar(value=True)
        always_on_top_cb = ttk.Checkbutton(quick_frame, text="Always On Top",
                                          variable=self.always_on_top_var,
                                          command=self.toggle_always_on_top)
        always_on_top_cb.pack(side='right', padx=5, pady=5)

    def setup_log_tab(self):
        """Setup the Output Log tab"""
        # Log display
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=20, width=100)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Clear button
        ttk.Button(self.log_frame, text="Clear Log", command=self.clear_log).pack(pady=5)

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
            "geometry": "1000x800+100+100",  # width x height + x_offset + y_offset
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