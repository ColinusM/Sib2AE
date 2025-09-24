#!/usr/bin/env python3
"""
MIDI-XML-SVG Matching Analyzer
Analyzes coordinate matching between XML notes, MIDI timing, and SVG positions
Generates annotated SVG for visual verification
"""

import xml.etree.ElementTree as ET
import mido
import json
import sys
import os
import re
from pathlib import Path
import uuid
from typing import List, Dict, Tuple, Optional

class MatchingAnalyzer:
    def __init__(self, xml_file: str, midi_file: str, svg_file: str):
        self.xml_file = xml_file
        self.midi_file = midi_file
        self.svg_file = svg_file

        # Coordinate transformation constants (from Note Coordinator)
        self.X_SCALE = 3.206518
        self.X_OFFSET = 564.93

        # Staff positions
        self.STAFF_POSITIONS = {
            0: {'base_y': 1037, 'range': (950, 1100)},   # Upper staff
            1: {'base_y': 1417, 'range': (1250, 1500)},  # Lower staff
            2: {'base_y': 1797, 'range': (1650, 1800)},  # Third staff
            3: {'base_y': 2177, 'range': (2050, 2200)}   # Fourth staff
        }

        # Results
        self.xml_notes = []
        self.midi_notes = []
        self.svg_elements = []
        self.matches = []
        self.errors = []

    def analyze(self) -> Dict:
        """Run complete analysis and return results"""
        print(f"🎼 Analyzing MIDI-XML-SVG Matching", file=sys.stderr)
        print(f"XML: {os.path.basename(self.xml_file)}", file=sys.stderr)
        print(f"MIDI: {os.path.basename(self.midi_file)}", file=sys.stderr)
        print(f"SVG: {os.path.basename(self.svg_file)}", file=sys.stderr)
        print("", file=sys.stderr)

        # Extract data from each source
        self.extract_xml_notes()
        self.extract_midi_notes()
        self.extract_svg_elements()

        # Perform matching
        self.match_notes()

        # Generate annotated SVG
        self.create_annotated_svg()

        # Return results
        return self.generate_results()

    def midi_note_to_name(self, note_number: int) -> str:
        """Convert MIDI note number to note name"""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_number // 12) - 1
        note = notes[note_number % 12]
        return f"{note}{octave}"

    def extract_xml_notes(self):
        """Extract notes from MusicXML with coordinate transformation"""
        print("📄 Extracting XML notes...", file=sys.stderr)

        tree = ET.parse(self.xml_file)
        root = tree.getroot()

        for part in root.findall('part'):
            part_id = part.get('id')
            staff_index = 0 if part_id == 'P1' else 1  # Simple mapping
            cumulative_x = 0

            for measure in part.findall('measure'):
                measure_num = int(measure.get('number'))
                measure_width = float(measure.get('width', 0))

                for note in measure.findall('note'):
                    if note.find('rest') is not None:
                        continue

                    pitch = note.find('pitch')
                    if pitch is None:
                        continue

                    # Extract pitch info
                    step = pitch.find('step').text
                    octave = int(pitch.find('octave').text)
                    note_name = f"{step}{octave}"

                    # Get coordinates
                    default_x = float(note.find('default-x').text if note.find('default-x') is not None else 0)
                    default_y = float(note.find('default-y').text if note.find('default-y') is not None else 0)

                    # Calculate absolute position
                    absolute_x = cumulative_x + default_x

                    # Transform to SVG coordinates
                    svg_x = self.X_SCALE * absolute_x + self.X_OFFSET
                    svg_y = self.calculate_svg_y(default_y, staff_index)

                    xml_note = {
                        'part_id': part_id,
                        'measure': measure_num,
                        'note_name': note_name,
                        'step': step,
                        'octave': octave,
                        'xml_x': default_x,
                        'xml_y': default_y,
                        'absolute_x': absolute_x,
                        'svg_x': svg_x,
                        'svg_y': svg_y,
                        'staff_index': staff_index
                    }
                    self.xml_notes.append(xml_note)

                cumulative_x += measure_width

        print(f"   Found {len(self.xml_notes)} XML notes", file=sys.stderr)

    def calculate_svg_y(self, xml_y: float, staff_index: int) -> float:
        """Calculate SVG Y coordinate from XML Y"""
        base_y = self.STAFF_POSITIONS[staff_index]['base_y']

        # Pitch-specific adjustments (simplified)
        if xml_y == 5:    # G4
            return base_y + 12
        elif xml_y == 10: # A4
            return base_y
        elif xml_y == -15: # C4
            return base_y
        elif xml_y == -20: # B3
            return base_y + 12
        elif xml_y == -25: # A3
            return base_y + 24
        else:
            # Default positioning
            return base_y - (xml_y * 3)  # Approximate scaling

    def extract_midi_notes(self):
        """Extract notes from MIDI with timing"""
        print("🎹 Extracting MIDI notes...", file=sys.stderr)

        mid = mido.MidiFile(self.midi_file)

        # Convert to absolute time
        current_time = 0
        ticks_per_beat = mid.ticks_per_beat
        tempo = 500000  # Default tempo (120 BPM)

        for track_idx, track in enumerate(mid.tracks):
            for msg in track:
                current_time += msg.time

                if msg.type == 'set_tempo':
                    tempo = msg.tempo
                elif msg.type == 'note_on' and msg.velocity > 0:
                    # Convert ticks to seconds
                    time_seconds = mido.tick2second(current_time, ticks_per_beat, tempo)

                    # Get pitch name
                    pitch_name = self.midi_note_to_name(msg.note)

                    midi_note = {
                        'track_index': track_idx,
                        'pitch_midi': msg.note,
                        'pitch_name': pitch_name,
                        'velocity': msg.velocity,
                        'start_time': time_seconds,
                        'channel': msg.channel
                    }
                    self.midi_notes.append(midi_note)

        print(f"   Found {len(self.midi_notes)} MIDI notes", file=sys.stderr)

    def extract_svg_elements(self):
        """Extract text elements (noteheads) from SVG"""
        print("🎨 Extracting SVG elements...", file=sys.stderr)

        tree = ET.parse(self.svg_file)
        root = tree.getroot()

        # Find all text elements (noteheads are typically text elements)
        for elem in root.iter():
            if elem.tag.endswith('text'):
                x = float(elem.get('x', 0))
                y = float(elem.get('y', 0))
                font_family = elem.get('font-family', '')
                text_content = elem.text or ''

                # Filter for noteheads (Helsinki font, specific coordinates)
                if 'Helsinki' in font_family and 900 < y < 2300:
                    svg_elem = {
                        'x': x,
                        'y': y,
                        'font_family': font_family,
                        'text': text_content,
                        'matched': False
                    }
                    self.svg_elements.append(svg_elem)

        print(f"   Found {len(self.svg_elements)} SVG noteheads", file=sys.stderr)

    def match_notes(self):
        """Match XML notes to MIDI notes and SVG elements"""
        print("🎯 Matching notes...", file=sys.stderr)

        # Simple matching by pitch name and approximate timing
        for xml_note in self.xml_notes:
            best_midi = self.find_best_midi_match(xml_note)
            best_svg = self.find_best_svg_match(xml_note)

            if best_midi and best_svg:
                # Successful match
                match = {
                    'xml_note': xml_note,
                    'midi_note': best_midi,
                    'svg_element': best_svg,
                    'note': xml_note['note_name'],
                    'svg_x': best_svg['x'],
                    'svg_y': best_svg['y'],
                    'midi_time': best_midi['start_time'],
                    'velocity': best_midi['velocity'],
                    'coordinate_error': self.calculate_coordinate_error(xml_note, best_svg)
                }
                self.matches.append(match)
                best_svg['matched'] = True

            else:
                # Failed match
                error = {
                    'xml_note': xml_note,
                    'note': xml_note['note_name'],
                    'reason': self.determine_error_reason(xml_note, best_midi, best_svg)
                }
                self.errors.append(error)

        print(f"   {len(self.matches)} successful matches", file=sys.stderr)
        print(f"   {len(self.errors)} matching errors", file=sys.stderr)

    def find_best_midi_match(self, xml_note: Dict) -> Optional[Dict]:
        """Find best MIDI note match"""
        xml_pitch = xml_note['note_name']

        # Convert XML pitch to MIDI number for accurate matching
        xml_midi_num = self.note_name_to_midi(xml_pitch)

        # Find MIDI notes with same MIDI number
        candidates = [m for m in self.midi_notes if m['pitch_midi'] == xml_midi_num]

        if candidates:
            # Return first candidate (could be improved with timing logic)
            return candidates[0]
        return None

    def note_name_to_midi(self, note_name: str) -> int:
        """Convert note name (like 'A4') to MIDI number"""
        # Parse note name
        if len(note_name) < 2:
            return 60  # Default to C4

        note = note_name[:-1]  # Everything except last character
        octave = int(note_name[-1])  # Last character is octave

        # Note to semitone mapping
        note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

        # Handle sharps and flats
        if '#' in note:
            base_note = note.replace('#', '')
            semitones = note_map.get(base_note, 0) + 1
        elif 'b' in note:
            base_note = note.replace('b', '')
            semitones = note_map.get(base_note, 0) - 1
        else:
            semitones = note_map.get(note, 0)

        # Calculate MIDI number
        midi_num = (octave + 1) * 12 + semitones
        return midi_num

    def find_best_svg_match(self, xml_note: Dict) -> Optional[Dict]:
        """Find best SVG element match"""
        expected_x = xml_note['svg_x']
        expected_y = xml_note['svg_y']

        tolerance = 50  # pixels

        # Find SVG elements within tolerance
        candidates = []
        for svg_elem in self.svg_elements:
            if svg_elem['matched']:
                continue

            dx = abs(svg_elem['x'] - expected_x)
            dy = abs(svg_elem['y'] - expected_y)

            if dx <= tolerance and dy <= tolerance:
                distance = (dx**2 + dy**2)**0.5
                candidates.append((svg_elem, distance))

        if candidates:
            # Return closest match
            candidates.sort(key=lambda x: x[1])
            return candidates[0][0]
        return None

    def calculate_coordinate_error(self, xml_note: Dict, svg_elem: Dict) -> float:
        """Calculate coordinate error in pixels"""
        dx = xml_note['svg_x'] - svg_elem['x']
        dy = xml_note['svg_y'] - svg_elem['y']
        return (dx**2 + dy**2)**0.5

    def determine_error_reason(self, xml_note: Dict, midi_note: Optional[Dict], svg_elem: Optional[Dict]) -> str:
        """Determine why matching failed"""
        if not midi_note and not svg_elem:
            return "No MIDI or SVG match found"
        elif not midi_note:
            return "No MIDI note found for this pitch"
        elif not svg_elem:
            return f"No SVG element found near ({xml_note['svg_x']:.0f}, {xml_note['svg_y']:.0f})"
        else:
            return "Unknown matching error"

    def create_annotated_svg(self):
        """Create an annotated SVG showing matches and errors"""
        print("🎨 Creating annotated SVG...", file=sys.stderr)

        # Copy original SVG
        tree = ET.parse(self.svg_file)
        root = tree.getroot()

        # Add annotation layer
        annotation_group = ET.SubElement(root, 'g')
        annotation_group.set('id', 'matching_annotations')
        annotation_group.set('opacity', '0.8')

        # Add successful matches (green circles)
        for match in self.matches:
            circle = ET.SubElement(annotation_group, 'circle')
            circle.set('cx', str(match['svg_x']))
            circle.set('cy', str(match['svg_y']))
            circle.set('r', '15')
            circle.set('fill', 'none')
            circle.set('stroke', 'green')
            circle.set('stroke-width', '3')

            # Add timing label
            text = ET.SubElement(annotation_group, 'text')
            text.set('x', str(match['svg_x'] + 20))
            text.set('y', str(match['svg_y'] - 10))
            text.set('font-family', 'Arial')
            text.set('font-size', '12')
            text.set('fill', 'green')
            text.text = f"{match['midi_time']:.1f}s"

        # Add errors (red X marks)
        for error in self.errors:
            xml_note = error['xml_note']
            x, y = xml_note['svg_x'], xml_note['svg_y']

            # Red X
            line1 = ET.SubElement(annotation_group, 'line')
            line1.set('x1', str(x - 10))
            line1.set('y1', str(y - 10))
            line1.set('x2', str(x + 10))
            line1.set('y2', str(y + 10))
            line1.set('stroke', 'red')
            line1.set('stroke-width', '3')

            line2 = ET.SubElement(annotation_group, 'line')
            line2.set('x1', str(x - 10))
            line2.set('y1', str(y + 10))
            line2.set('x2', str(x + 10))
            line2.set('y2', str(y - 10))
            line2.set('stroke', 'red')
            line2.set('stroke-width', '3')

            # Error label
            text = ET.SubElement(annotation_group, 'text')
            text.set('x', str(x + 15))
            text.set('y', str(y + 15))
            text.set('font-family', 'Arial')
            text.set('font-size', '10')
            text.set('fill', 'red')
            text.text = error['note']

        # Add legend
        legend_group = ET.SubElement(annotation_group, 'g')
        legend_group.set('transform', 'translate(50, 50)')

        # Legend background
        legend_bg = ET.SubElement(legend_group, 'rect')
        legend_bg.set('x', '0')
        legend_bg.set('y', '0')
        legend_bg.set('width', '200')
        legend_bg.set('height', '80')
        legend_bg.set('fill', 'white')
        legend_bg.set('stroke', 'black')
        legend_bg.set('opacity', '0.9')

        # Legend items
        # Green circle example
        circle = ET.SubElement(legend_group, 'circle')
        circle.set('cx', '15')
        circle.set('cy', '20')
        circle.set('r', '8')
        circle.set('fill', 'none')
        circle.set('stroke', 'green')
        circle.set('stroke-width', '2')

        text = ET.SubElement(legend_group, 'text')
        text.set('x', '30')
        text.set('y', '25')
        text.set('font-family', 'Arial')
        text.set('font-size', '12')
        text.text = 'Successful match'

        # Red X example
        line1 = ET.SubElement(legend_group, 'line')
        line1.set('x1', '8')
        line1.set('y1', '40')
        line1.set('x2', '22')
        line1.set('y2', '54')
        line1.set('stroke', 'red')
        line1.set('stroke-width', '2')

        line2 = ET.SubElement(legend_group, 'line')
        line2.set('x1', '8')
        line2.set('y1', '54')
        line2.set('x2', '22')
        line2.set('y2', '40')
        line2.set('stroke', 'red')
        line2.set('stroke-width', '2')

        text = ET.SubElement(legend_group, 'text')
        text.set('x', '30')
        text.set('y', '50')
        text.set('font-family', 'Arial')
        text.set('font-size', '12')
        text.text = 'Matching error'

        # Stats
        text = ET.SubElement(legend_group, 'text')
        text.set('x', '10')
        text.set('y', '70')
        text.set('font-family', 'Arial')
        text.set('font-size', '10')
        text.text = f"Matches: {len(self.matches)}, Errors: {len(self.errors)}"

        # Save annotated SVG
        output_file = "output/annotated_matching.svg"
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        print(f"   Saved: {output_file}", file=sys.stderr)

    def generate_results(self) -> Dict:
        """Generate final results dictionary"""
        total_notes = len(self.xml_notes)
        successful_matches = len(self.matches)
        accuracy = successful_matches / total_notes if total_notes > 0 else 0

        avg_error = 0
        if self.matches:
            avg_error = sum(m['coordinate_error'] for m in self.matches) / len(self.matches)

        return {
            'summary': {
                'xml_notes': len(self.xml_notes),
                'midi_notes': len(self.midi_notes),
                'svg_elements': len(self.svg_elements),
                'matches': successful_matches,
                'errors': len(self.errors),
                'accuracy': accuracy,
                'avg_error': avg_error
            },
            'matches': self.matches,
            'errors': self.errors,
            'files': {
                'xml': self.xml_file,
                'midi': self.midi_file,
                'svg': self.svg_file,
                'annotated_svg': 'output/annotated_matching.svg'
            }
        }

def main():
    if len(sys.argv) != 4:
        print("Usage: matching_analyzer.py <xml_file> <midi_file> <svg_file>")
        sys.exit(1)

    xml_file = sys.argv[1]
    midi_file = sys.argv[2]
    svg_file = sys.argv[3]

    # Validate files exist
    for file_path in [xml_file, midi_file, svg_file]:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

    # Run analysis
    analyzer = MatchingAnalyzer(xml_file, midi_file, svg_file)
    results = analyzer.analyze()

    # Output results as JSON
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()