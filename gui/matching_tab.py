#!/usr/bin/env python3
"""
MIDI-XML-SVG Matching Tab
Interactive matching with visual verification
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os
import json
import sys
import xml.etree.ElementTree as ET

class MatchingTab:
    def __init__(self, parent_frame, settings, log_callback=None):
        self.frame = parent_frame
        self.settings = settings
        self.log_callback = log_callback

        # Variables for file paths
        self.xml_var = tk.StringVar(value=settings.default_musicxml)
        self.midi_var = tk.StringVar(value=settings.default_midi)
        self.svg_var = tk.StringVar(value=settings.default_svg)

        # Results
        self.match_results = None

        self.setup_ui()

    def log(self, message):
        """Send message to log callback"""
        if self.log_callback:
            self.log_callback(message)

    def setup_ui(self):
        """Setup the matching tab UI"""
        # Input files frame
        files_frame = ttk.LabelFrame(self.frame, text="Input Files for Matching")
        files_frame.pack(fill='x', padx=5, pady=5)

        # XML file
        ttk.Label(files_frame, text="MusicXML:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(files_frame, textvariable=self.xml_var, width=50).grid(row=0, column=1, padx=5, pady=2, sticky='ew')
        ttk.Button(files_frame, text="Browse", command=self.browse_xml).grid(row=0, column=2, padx=2, pady=2)

        # MIDI file
        ttk.Label(files_frame, text="MIDI:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(files_frame, textvariable=self.midi_var, width=50).grid(row=1, column=1, padx=5, pady=2, sticky='ew')
        ttk.Button(files_frame, text="Browse", command=self.browse_midi).grid(row=1, column=2, padx=2, pady=2)

        # SVG file
        ttk.Label(files_frame, text="SVG:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(files_frame, textvariable=self.svg_var, width=50).grid(row=2, column=1, padx=5, pady=2, sticky='ew')
        ttk.Button(files_frame, text="Browse", command=self.browse_svg).grid(row=2, column=2, padx=2, pady=2)

        files_frame.columnconfigure(1, weight=1)

        # Matching controls frame
        controls_frame = ttk.LabelFrame(self.frame, text="Matching Analysis")
        controls_frame.pack(fill='x', padx=5, pady=5)

        # Analysis buttons
        ttk.Button(controls_frame, text="🎯 Run Note Coordinator",
                  command=self.run_note_coordinator,
                  style='Accent.TButton').grid(row=0, column=0, padx=5, pady=5, sticky='ew')

        ttk.Button(controls_frame, text="🔍 View Annotated SVG",
                  command=self.view_annotated_svg).grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        ttk.Button(controls_frame, text="💬 Chat About Results",
                  command=self.chat_about_results).grid(row=0, column=2, padx=5, pady=5, sticky='ew')

        # Configure grid
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(2, weight=1)

        # Results frame
        self.results_frame = ttk.LabelFrame(self.frame, text="Matching Results")
        self.results_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Results text
        self.results_text = tk.Text(self.results_frame, height=15, font=('Consolas', 9))
        scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)

        self.results_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)

        # Initial message
        self.results_text.insert('1.0', "🎼 MIDI-XML-SVG Matching Analysis\n\n")
        self.results_text.insert('end', "Select your input files and click 'Analyze Matching' to begin.\n\n")
        self.results_text.insert('end', "This will:\n")
        self.results_text.insert('end', "• Extract note data from MusicXML\n")
        self.results_text.insert('end', "• Parse MIDI timing information\n")
        self.results_text.insert('end', "• Match coordinates in SVG\n")
        self.results_text.insert('end', "• Show matching accuracy and errors\n")
        self.results_text.insert('end', "• Generate annotated visualization\n\n")
        self.results_text.insert('end', "You can then review the annotated SVG and chat about the results!")

    def browse_xml(self):
        filename = filedialog.askopenfilename(title="Select MusicXML", filetypes=[("MusicXML", "*.musicxml")])
        if filename:
            self.xml_var.set(filename)

    def browse_midi(self):
        filename = filedialog.askopenfilename(title="Select MIDI", filetypes=[("MIDI", "*.mid")])
        if filename:
            self.midi_var.set(filename)

    def browse_svg(self):
        filename = filedialog.askopenfilename(title="Select SVG", filetypes=[("SVG", "*.svg")])
        if filename:
            self.svg_var.set(filename)

    def run_note_coordinator(self):
        """Run the Note Coordinator and create annotated SVG"""
        # Validate inputs
        xml_file = self.xml_var.get()
        midi_file = self.midi_var.get()
        svg_file = self.svg_var.get()

        if not all(os.path.exists(f) for f in [xml_file, midi_file, svg_file]):
            messagebox.showerror("Error", "Please select valid XML, MIDI, and SVG files")
            return

        self.log("🎯 Running Note Coordinator...")
        self.results_text.delete('1.0', 'end')
        self.results_text.insert('1.0', "🔄 Running Note Coordinator matching...\n\n")

        def run_analysis():
            try:
                # Run Note Coordinator
                output_dir = "outputs/json/coordination"
                cmd = [
                    sys.executable,
                    "PRPs-agentic-eng/note_coordinator.py",
                    xml_file,
                    midi_file,
                    output_dir
                ]

                self.log(f"📊 Command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    self.log("✅ Note Coordinator completed!")

                    # Load the registry and create annotated SVG
                    registry_path = os.path.join(output_dir, "universal_notes_registry.json")
                    if os.path.exists(registry_path):
                        with open(registry_path, 'r') as f:
                            registry_data = json.load(f)

                        # Create annotated SVG
                        self.create_annotated_svg_from_registry(svg_file, registry_data)

                        # Display results
                        self.display_coordinator_results(registry_data)
                        self.match_results = self.convert_to_standard_format(registry_data)

                    else:
                        self.log("❌ Registry file not found")
                else:
                    self.results_text.delete('1.0', 'end')
                    self.results_text.insert('1.0', f"❌ Note Coordinator failed:\n{result.stderr}")
                    self.log("❌ Note Coordinator failed")

            except Exception as e:
                self.results_text.delete('1.0', 'end')
                self.results_text.insert('1.0', f"❌ Error: {e}")
                self.log(f"❌ Coordinator error: {e}")

        # Run in background thread
        thread = threading.Thread(target=run_analysis, daemon=True)
        thread.start()

    def create_annotated_svg_from_registry(self, svg_file, registry_data):
        """Create annotated SVG with MIDI timing labels from Note Coordinator registry"""
        import xml.etree.ElementTree as ET

        try:
            # Parse the original SVG
            tree = ET.parse(svg_file)
            root = tree.getroot()

            # Add annotation layer
            annotation_group = ET.SubElement(root, 'g')
            annotation_group.set('id', 'midi_annotations')
            annotation_group.set('opacity', '0.9')

            matched_count = 0
            unmatched_count = 0

            # Process each note in the registry
            for note in registry_data.get('notes', []):
                svg_data = note.get('svg_data', {})
                midi_data = note.get('midi_data')

                if 'svg_x' in svg_data and 'svg_y' in svg_data:
                    x = float(svg_data['svg_x'])
                    y = float(svg_data['svg_y'])

                    if midi_data and midi_data.get('start_time_seconds') is not None:
                        # Matched note - green circle and timing label
                        circle = ET.SubElement(annotation_group, 'circle')
                        circle.set('cx', str(x))
                        circle.set('cy', str(y))
                        circle.set('r', '12')
                        circle.set('fill', 'none')
                        circle.set('stroke', 'green')
                        circle.set('stroke-width', '2')

                        # Timing text
                        timing_text = ET.SubElement(annotation_group, 'text')
                        timing_text.set('x', str(x + 15))
                        timing_text.set('y', str(y - 5))
                        timing_text.set('font-family', 'Arial, sans-serif')
                        timing_text.set('font-size', '14')
                        timing_text.set('font-weight', 'bold')
                        timing_text.set('fill', 'green')
                        timing_text.text = f"{midi_data['start_time_seconds']:.1f}s"

                        # Note name below
                        note_text = ET.SubElement(annotation_group, 'text')
                        note_text.set('x', str(x + 15))
                        note_text.set('y', str(y + 10))
                        note_text.set('font-family', 'Arial, sans-serif')
                        note_text.set('font-size', '12')
                        note_text.set('fill', 'green')
                        note_text.text = note.get('xml_data', {}).get('note_name', '')

                        matched_count += 1

                    else:
                        # Unmatched note - red X
                        # Red X lines
                        line1 = ET.SubElement(annotation_group, 'line')
                        line1.set('x1', str(x - 8))
                        line1.set('y1', str(y - 8))
                        line1.set('x2', str(x + 8))
                        line1.set('y2', str(y + 8))
                        line1.set('stroke', 'red')
                        line1.set('stroke-width', '3')

                        line2 = ET.SubElement(annotation_group, 'line')
                        line2.set('x1', str(x - 8))
                        line2.set('y1', str(y + 8))
                        line2.set('x2', str(x + 8))
                        line2.set('y2', str(y - 8))
                        line2.set('stroke', 'red')
                        line2.set('stroke-width', '3')

                        # Note name
                        note_text = ET.SubElement(annotation_group, 'text')
                        note_text.set('x', str(x + 15))
                        note_text.set('y', str(y + 5))
                        note_text.set('font-family', 'Arial, sans-serif')
                        note_text.set('font-size', '12')
                        note_text.set('fill', 'red')
                        note_text.text = note.get('xml_data', {}).get('note_name', 'Unknown')

                        unmatched_count += 1

            # Add legend
            self.add_legend_to_svg(annotation_group, matched_count, unmatched_count)

            # Save annotated SVG
            output_file = "outputs/svg/annotated/annotated_coordinator.svg"
            os.makedirs("outputs/svg/annotated", exist_ok=True)
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            self.log(f"🎨 Annotated SVG saved: {output_file}")

        except Exception as e:
            self.log(f"❌ Error creating annotated SVG: {e}")

    def add_legend_to_svg(self, parent_group, matched_count, unmatched_count):
        """Add legend to the annotated SVG"""
        legend_group = ET.SubElement(parent_group, 'g')
        legend_group.set('transform', 'translate(50, 50)')

        # Legend background
        legend_bg = ET.SubElement(legend_group, 'rect')
        legend_bg.set('x', '0')
        legend_bg.set('y', '0')
        legend_bg.set('width', '250')
        legend_bg.set('height', '100')
        legend_bg.set('fill', 'white')
        legend_bg.set('stroke', 'black')
        legend_bg.set('stroke-width', '1')
        legend_bg.set('opacity', '0.95')

        # Title
        title_text = ET.SubElement(legend_group, 'text')
        title_text.set('x', '10')
        title_text.set('y', '20')
        title_text.set('font-family', 'Arial, sans-serif')
        title_text.set('font-size', '16')
        title_text.set('font-weight', 'bold')
        title_text.text = 'MIDI-XML Matching Results'

        # Green circle example
        circle = ET.SubElement(legend_group, 'circle')
        circle.set('cx', '20')
        circle.set('cy', '40')
        circle.set('r', '8')
        circle.set('fill', 'none')
        circle.set('stroke', 'green')
        circle.set('stroke-width', '2')

        text = ET.SubElement(legend_group, 'text')
        text.set('x', '35')
        text.set('y', '45')
        text.set('font-family', 'Arial, sans-serif')
        text.set('font-size', '12')
        text.text = f'Matched ({matched_count}) - Shows timing'

        # Red X example
        line1 = ET.SubElement(legend_group, 'line')
        line1.set('x1', '15')
        line1.set('y1', '55')
        line1.set('x2', '25')
        line1.set('y2', '65')
        line1.set('stroke', 'red')
        line1.set('stroke-width', '2')

        line2 = ET.SubElement(legend_group, 'line')
        line2.set('x1', '15')
        line2.set('y1', '65')
        line2.set('x2', '25')
        line2.set('y2', '55')
        line2.set('stroke', 'red')
        line2.set('stroke-width', '2')

        text = ET.SubElement(legend_group, 'text')
        text.set('x', '35')
        text.set('y', '65')
        text.set('font-family', 'Arial, sans-serif')
        text.set('font-size', '12')
        text.text = f'Unmatched ({unmatched_count}) - No MIDI found'

        # Stats
        stats_text = ET.SubElement(legend_group, 'text')
        stats_text.set('x', '10')
        stats_text.set('y', '85')
        stats_text.set('font-family', 'Arial, sans-serif')
        stats_text.set('font-size', '11')
        total_notes = matched_count + unmatched_count
        accuracy = (matched_count / total_notes * 100) if total_notes > 0 else 0
        stats_text.text = f'Accuracy: {accuracy:.1f}% ({matched_count}/{total_notes} notes)'

    def display_coordinator_results(self, registry_data):
        """Display Note Coordinator results"""
        self.results_text.delete('1.0', 'end')

        # Summary
        notes = registry_data.get('notes', [])
        matched_notes = [n for n in notes if n.get('midi_data') is not None]
        unmatched_notes = [n for n in notes if n.get('midi_data') is None]

        self.results_text.insert('end', f"🎼 NOTE COORDINATOR RESULTS\n")
        self.results_text.insert('end', f"{'='*50}\n\n")

        self.results_text.insert('end', f"📊 SUMMARY:\n")
        self.results_text.insert('end', f"• Total notes: {len(notes)}\n")
        self.results_text.insert('end', f"• Matched to MIDI: {len(matched_notes)}\n")
        self.results_text.insert('end', f"• Unmatched: {len(unmatched_notes)}\n")
        accuracy = (len(matched_notes) / len(notes) * 100) if notes else 0
        self.results_text.insert('end', f"• Accuracy: {accuracy:.1f}%\n\n")

        # Show matched notes
        if matched_notes:
            self.results_text.insert('end', f"✅ MATCHED NOTES ({len(matched_notes)}):\n")
            for i, note in enumerate(matched_notes[:10]):  # Show first 10
                xml_data = note.get('xml_data', {})
                midi_data = note.get('midi_data', {})
                svg_data = note.get('svg_data', {})

                note_name = xml_data.get('note_name', 'Unknown')
                timing = midi_data.get('start_time_seconds', 0)
                velocity = midi_data.get('velocity', 0)
                x = svg_data.get('svg_x', 0)
                y = svg_data.get('svg_y', 0)

                self.results_text.insert('end',
                    f"{i+1:2d}. {note_name} @ ({x:.0f},{y:.0f}) "
                    f"MIDI: {timing:.1f}s vel:{velocity}\n")

            if len(matched_notes) > 10:
                self.results_text.insert('end', f"    ... and {len(matched_notes)-10} more\n")
            self.results_text.insert('end', "\n")

        # Show unmatched notes
        if unmatched_notes:
            self.results_text.insert('end', f"❌ UNMATCHED NOTES ({len(unmatched_notes)}):\n")
            for i, note in enumerate(unmatched_notes[:5]):  # Show first 5
                xml_data = note.get('xml_data', {})
                note_name = xml_data.get('note_name', 'Unknown')
                self.results_text.insert('end', f"{i+1}. {note_name} - No MIDI match found\n")

            if len(unmatched_notes) > 5:
                self.results_text.insert('end', f"    ... and {len(unmatched_notes)-5} more\n")

        self.results_text.insert('end', f"\n💡 Click 'View Annotated SVG' to see visual verification!\n")

    def convert_to_standard_format(self, registry_data):
        """Convert registry data to standard format for compatibility"""
        notes = registry_data.get('notes', [])
        matched_notes = [n for n in notes if n.get('midi_data') is not None]
        unmatched_notes = [n for n in notes if n.get('midi_data') is None]

        return {
            'summary': {
                'xml_notes': len(notes),
                'midi_notes': len(matched_notes),
                'matches': len(matched_notes),
                'errors': len(unmatched_notes),
                'accuracy': len(matched_notes) / len(notes) if notes else 0
            },
            'matches': matched_notes,
            'errors': unmatched_notes
        }

    def display_results(self):
        """Display matching results in a formatted way"""
        if not self.match_results:
            return

        self.results_text.delete('1.0', 'end')

        # Summary
        summary = self.match_results.get('summary', {})
        self.results_text.insert('end', f"🎼 MATCHING ANALYSIS RESULTS\n")
        self.results_text.insert('end', f"{'='*50}\n\n")

        self.results_text.insert('end', f"📊 SUMMARY:\n")
        self.results_text.insert('end', f"• Total XML notes: {summary.get('xml_notes', 0)}\n")
        self.results_text.insert('end', f"• Total MIDI notes: {summary.get('midi_notes', 0)}\n")
        self.results_text.insert('end', f"• Successful matches: {summary.get('matches', 0)}\n")
        self.results_text.insert('end', f"• Match accuracy: {summary.get('accuracy', 0):.1%}\n")
        self.results_text.insert('end', f"• Avg coordinate error: {summary.get('avg_error', 0):.1f} pixels\n\n")

        # Matches
        matches = self.match_results.get('matches', [])
        if matches:
            self.results_text.insert('end', f"✅ SUCCESSFUL MATCHES ({len(matches)}):\n")
            for i, match in enumerate(matches[:10]):  # Show first 10
                self.results_text.insert('end',
                    f"{i+1:2d}. {match.get('note', '?')} @ ({match.get('svg_x', 0):.0f},{match.get('svg_y', 0):.0f}) "
                    f"MIDI: {match.get('midi_time', 0):.2f}s vel:{match.get('velocity', 0)}\n")

            if len(matches) > 10:
                self.results_text.insert('end', f"    ... and {len(matches)-10} more\n")
            self.results_text.insert('end', "\n")

        # Errors
        errors = self.match_results.get('errors', [])
        if errors:
            self.results_text.insert('end', f"❌ MATCHING ERRORS ({len(errors)}):\n")
            for i, error in enumerate(errors[:5]):  # Show first 5
                self.results_text.insert('end', f"{i+1}. {error.get('note', '?')}: {error.get('reason', 'Unknown error')}\n")

            if len(errors) > 5:
                self.results_text.insert('end', f"    ... and {len(errors)-5} more errors\n")
            self.results_text.insert('end', "\n")

        self.results_text.insert('end', f"💡 TIP: Click 'View Annotated SVG' to see visual verification!\n")

    def view_annotated_svg(self):
        """Open the annotated SVG for visual verification"""
        # Check for coordinator output first, then fallback to matching analyzer
        annotated_svg = "outputs/svg/annotated/annotated_coordinator.svg"
        if not os.path.exists(annotated_svg):
            annotated_svg = "outputs/svg/annotated/annotated_matching.svg"

        if not os.path.exists(annotated_svg):
            messagebox.showwarning("Warning", "No annotated SVG found. Run Note Coordinator first.")
            return

        try:
            # Open with default application
            import platform
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", annotated_svg])
            elif platform.system() == "Windows":
                subprocess.run(["start", annotated_svg], shell=True)
            else:  # Linux
                subprocess.run(["xdg-open", annotated_svg])

            self.log(f"🔍 Opened annotated SVG: {annotated_svg}")

        except Exception as e:
            self.log(f"❌ Error opening SVG: {e}")

    def chat_about_results(self):
        """Open a chat interface to discuss the results"""
        if not self.match_results:
            messagebox.showinfo("Info", "Run analysis first to generate results to chat about")
            return

        # Create chat window
        self.create_chat_window()

    def create_chat_window(self):
        """Create a chat window for discussing results"""
        chat_window = tk.Toplevel(self.frame)
        chat_window.title("Chat About Matching Results")
        chat_window.geometry("600x400")

        # Chat history
        chat_frame = ttk.Frame(chat_window)
        chat_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.chat_text = tk.Text(chat_frame, height=20, font=('Consolas', 9))
        chat_scroll = ttk.Scrollbar(chat_frame, orient="vertical", command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=chat_scroll.set)

        self.chat_text.pack(side='left', fill='both', expand=True)
        chat_scroll.pack(side='right', fill='y')

        # Input frame
        input_frame = ttk.Frame(chat_window)
        input_frame.pack(fill='x', padx=10, pady=(0, 10))

        self.chat_input = ttk.Entry(input_frame, font=('Consolas', 9))
        self.chat_input.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.chat_input.bind('<Return>', self.send_chat_message)

        ttk.Button(input_frame, text="Send", command=self.send_chat_message).pack(side='right')

        # Initial message
        self.chat_text.insert('1.0', "🤖 AI Assistant: Hi! I can help you analyze the matching results.\n\n")
        self.chat_text.insert('end', f"I can see you have {self.match_results.get('summary', {}).get('matches', 0)} matches ")
        self.chat_text.insert('end', f"with {self.match_results.get('summary', {}).get('accuracy', 0):.1%} accuracy.\n\n")
        self.chat_text.insert('end', "Ask me anything about:\n")
        self.chat_text.insert('end', "• Why certain notes didn't match\n")
        self.chat_text.insert('end', "• Coordinate transformation issues\n")
        self.chat_text.insert('end', "• How to improve matching accuracy\n")
        self.chat_text.insert('end', "• Interpretation of the results\n\n")
        self.chat_text.insert('end', "Type your question below!\n\n")

    def send_chat_message(self, event=None):
        """Send a chat message and get AI response"""
        message = self.chat_input.get().strip()
        if not message:
            return

        # Display user message
        self.chat_text.insert('end', f"👤 You: {message}\n\n")

        # Clear input
        self.chat_input.delete(0, 'end')

        # Generate AI response (simulated for now)
        response = self.generate_ai_response(message)
        self.chat_text.insert('end', f"🤖 AI: {response}\n\n")

        # Scroll to bottom
        self.chat_text.see('end')

    def generate_ai_response(self, message):
        """Generate AI response based on the message and results"""
        message_lower = message.lower()

        if not self.match_results:
            return "I don't have any analysis results to discuss. Please run the matching analysis first."

        summary = self.match_results.get('summary', {})
        matches = len(self.match_results.get('matches', []))
        errors = len(self.match_results.get('errors', []))
        accuracy = summary.get('accuracy', 0)

        # Simple response logic based on keywords
        if 'accuracy' in message_lower or 'how good' in message_lower:
            if accuracy > 0.8:
                return f"Your matching accuracy of {accuracy:.1%} is quite good! This means {matches} out of {matches + errors} notes were successfully matched."
            elif accuracy > 0.5:
                return f"Your accuracy of {accuracy:.1%} is moderate. There might be coordinate transformation issues or timing misalignments causing some notes to not match."
            else:
                return f"Your accuracy of {accuracy:.1%} is low. This could indicate significant coordinate system differences between your XML and SVG, or MIDI timing issues."

        elif 'error' in message_lower or 'wrong' in message_lower or 'fail' in message_lower:
            if errors > 0:
                return f"You have {errors} matching errors. Common causes include: coordinate system misalignment, missing notes in MIDI, or noteheads not found in SVG. Check the annotated SVG to see which notes failed."
            else:
                return "Great! You don't have any matching errors. All notes were successfully matched."

        elif 'improve' in message_lower or 'better' in message_lower or 'fix' in message_lower:
            suggestions = []
            if accuracy < 0.7:
                suggestions.append("Check if your SVG coordinates match the MusicXML transformation")
            if errors > matches * 0.3:
                suggestions.append("Verify that all MIDI notes have corresponding visual noteheads in the SVG")
            suggestions.append("Try adjusting the coordinate tolerance in the matching algorithm")
            return "To improve matching: " + ". ".join(suggestions) + "."

        elif 'coordinate' in message_lower or 'position' in message_lower:
            avg_error = summary.get('avg_error', 0)
            return f"The average coordinate error is {avg_error:.1f} pixels. If this is high (>50), there may be scaling or offset issues between your XML and SVG coordinate systems."

        else:
            # Default helpful response
            return f"Based on your results: {matches} successful matches, {accuracy:.1%} accuracy. The annotated SVG will show you exactly which notes matched (green) and which didn't (red). What specific aspect would you like to understand better?"