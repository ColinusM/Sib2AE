#!/usr/bin/env python3
"""
Script Runner - Handles subprocess execution of pipeline scripts
"""

import subprocess
import threading
import sys
import os

class ScriptRunner:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback

    def log(self, message):
        """Send message to log callback if available"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def run_script_async(self, script_path, args=None, description="Running script"):
        """Run a script asynchronously in a background thread"""
        def run_in_thread():
            try:
                self.log(f"🔄 {description}...")

                # Build command
                cmd = [sys.executable, script_path]
                if args:
                    cmd.extend(args)

                self.log(f"📊 Command: {' '.join(cmd)}")

                # Run the script
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    self.log(f"✅ {description} completed successfully!")
                    if result.stdout.strip():
                        # Show key output lines
                        lines = result.stdout.strip().split('\n')
                        for line in lines[-3:]:  # Show last 3 lines
                            if line.strip():
                                self.log(f"   {line}")
                else:
                    self.log(f"❌ {description} failed with return code {result.returncode}")
                    if result.stderr:
                        self.log(f"Error: {result.stderr}")

            except Exception as e:
                self.log(f"❌ Error running {description}: {e}")

        # Run in background thread
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        return thread

    def run_symbolic_script(self, script_name, args=None):
        """Run a symbolic pipeline script"""
        script_path = f"PRPs-agentic-eng/App/Symbolic Separators/{script_name}"
        description = f"Symbolic: {script_name.replace('.py', '').replace('_', ' ').title()}"
        return self.run_script_async(script_path, args, description)

    def run_audio_script(self, script_name, args=None):
        """Run an audio pipeline script"""
        script_path = f"PRPs-agentic-eng/App/Audio Separators/{script_name}"
        description = f"Audio: {script_name.replace('.py', '').replace('_', ' ').title()}"
        return self.run_script_async(script_path, args, description)