#!/usr/bin/env python3
"""
Note Coordinator - Universal Note Matching System

This coordinator analyzes XML, MIDI, and SVG files to create comprehensive
note matching and metadata. It establishes relationships between all three
formats before any pipeline processing begins.

Key Features:
- XML as source of truth for musical structure
- MIDI timing and performance data
- SVG visual positioning and coordinates
- Universal note IDs for pipeline tracking
- Comprehensive metadata generation
"""

import xml.etree.ElementTree as ET
import mido
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import uuid
from datetime import datetime

@dataclass
class XMLNote:
    """Note data from MusicXML"""
    part_id: str
    measure: int
    step: str
    octave: int
    duration: str
    xml_x: float
    xml_y: float
    absolute_x: float
    note_name: str
    staff_index: int
    is_grace_note: bool = False
    grace_slash: bool = False  # True for acciaccatura, False for appoggiatura

@dataclass
class MIDINote:
    """Note data from MIDI"""
    track_index: int
    track_name: str
    pitch_midi: int
    pitch_name: str
    velocity: int
    start_time_seconds: float
    end_time_seconds: float
    duration_seconds: float
    start_time_ticks: int
    end_time_ticks: int
    duration_ticks: int
    channel: int

@dataclass
class SVGNote:
    """Note data calculated for SVG positioning"""
    svg_x: int
    svg_y: int
    staff_index: int
    notehead_code: int
    unicode_char: str

@dataclass
class UniversalNote:
    """Unified note with all format data and relationships"""
    universal_id: str
    xml_data: XMLNote
    midi_data: Optional[MIDINote]
    svg_data: SVGNote
    match_confidence: float
    match_method: str
    timing_priority: str  # 'xml' or 'midi'

class NoteCoordinator:
    """Main coordinator for note matching across formats"""
    
    def __init__(self):
        self.xml_notes = []
        self.midi_notes = []
        self.svg_notes = []
        self.universal_notes = []
        self.metadata = {}
        
    def load_xml_notes(self, musicxml_file: str):
        """Load and parse notes from MusicXML"""
        print(f"📄 Loading XML notes from: {musicxml_file}")
        
        tree = ET.parse(musicxml_file)
        root = tree.getroot()
        
        # Extract scaling for coordinate conversion
        scaling = root.find('defaults/scaling')
        if scaling is not None:
            tenths = float(scaling.find('tenths').text)
            mm = float(scaling.find('millimeters').text)
            scaling_factor = mm / tenths
        else:
            scaling_factor = 0.15
        
        notes = []
        parts = []
        
        # Get part list for staff assignment
        part_list = root.find('part-list')
        if part_list is not None:
            for score_part in part_list.findall('score-part'):
                parts.append(score_part.get('id'))
        
        for part in root.findall('part'):
            part_id = part.get('id')
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

                    # Check if this is a grace note
                    grace_elem = note.find('grace')
                    is_grace = grace_elem is not None
                    grace_slash = grace_elem.get('slash') == 'yes' if is_grace else False

                    step = pitch.find('step').text
                    octave = int(pitch.find('octave').text)

                    # Handle accidentals for grace notes
                    alter_elem = pitch.find('alter')
                    alter = int(alter_elem.text) if alter_elem is not None else 0
                    accidental = ''
                    if alter == 1:
                        accidental = '#'
                    elif alter == -1:
                        accidental = 'b'

                    note_type = note.find('type')
                    duration = note_type.text if note_type is not None else 'quarter'

                    xml_x = float(note.get('default-x', 0))
                    xml_y = float(note.get('default-y', 0))
                    absolute_x = cumulative_x + xml_x

                    xml_note = XMLNote(
                        part_id=part_id,
                        measure=measure_num,
                        step=step,
                        octave=octave,
                        duration=duration,
                        xml_x=xml_x,
                        xml_y=xml_y,
                        absolute_x=absolute_x,
                        note_name=f"{step}{accidental}{octave}",
                        staff_index=parts.index(part_id) if part_id in parts else 0,
                        is_grace_note=is_grace,
                        grace_slash=grace_slash
                    )

                    notes.append(xml_note)
                
                cumulative_x += measure_width
        
        self.xml_notes = notes
        print(f"   ✅ Loaded {len(notes)} XML notes from {len(set(n.part_id for n in notes))} parts")
        
    def load_midi_notes(self, midi_file: str):
        """Load and parse notes from MIDI"""
        print(f"🎵 Loading MIDI notes from: {midi_file}")
        
        mid = mido.MidiFile(midi_file)
        notes = []
        note_id = 0
        
        for track_idx, track in enumerate(mid.tracks):
            track_name = track.name or f'Track_{track_idx}'
            active_notes = {}
            current_time = 0
            
            for msg in track:
                current_time += msg.time
                
                if msg.type == 'note_on' and hasattr(msg, 'note') and msg.velocity > 0:
                    active_notes[msg.note] = (current_time, msg.velocity)
                    
                elif (msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0)) and hasattr(msg, 'note'):
                    if msg.note in active_notes:
                        start_time, velocity = active_notes[msg.note]
                        duration = current_time - start_time
                        
                        # Convert ticks to seconds using tempo map
                        # Extract tempo from MIDI or default to 120 BPM
                        tempo_bpm = 120.0  # Default
                        for temp_msg in track:
                            if temp_msg.type == 'set_tempo':
                                tempo_bpm = 60000000 / temp_msg.tempo
                                break
                        
                        seconds_per_beat = 60.0 / tempo_bpm
                        start_seconds = start_time / mid.ticks_per_beat * seconds_per_beat
                        end_seconds = current_time / mid.ticks_per_beat * seconds_per_beat
                        duration_seconds = duration / mid.ticks_per_beat * seconds_per_beat
                        
                        midi_note = MIDINote(
                            track_index=track_idx,
                            track_name=track_name,
                            pitch_midi=msg.note,
                            pitch_name=self.midi_to_note_name(msg.note),
                            velocity=velocity,
                            start_time_seconds=start_seconds,
                            end_time_seconds=end_seconds,
                            duration_seconds=duration_seconds,
                            start_time_ticks=start_time,
                            end_time_ticks=current_time,
                            duration_ticks=duration,
                            channel=msg.channel
                        )
                        
                        notes.append(midi_note)
                        del active_notes[msg.note]
        
        self.midi_notes = notes
        print(f"   ✅ Loaded {len(notes)} MIDI notes from {len(set(n.track_name for n in notes))} tracks")
        
    def midi_to_note_name(self, note_number: int) -> str:
        """Convert MIDI note number to note name"""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = note_number // 12 - 1
        note = notes[note_number % 12]
        return f"{note}{octave}"
        
    def calculate_svg_coordinates(self):
        """Calculate SVG coordinates for XML notes using universal transformation"""
        print(f"🖼️  Calculating SVG coordinates")
        
        # Universal transformation constants
        X_SCALE = 3.206518
        X_OFFSET = 564.93
        
        # Universal staff positioning - dynamic based on number of staves
        STAFF_BASE_Y_START = 1037  # First staff base Y
        STAFF_SEPARATION = 380     # Separation between staves
        
        svg_notes = []
        
        for xml_note in self.xml_notes:
            # X coordinate transformation (universal)
            svg_x = int(xml_note.absolute_x * X_SCALE + X_OFFSET)
            
            # Y coordinate transformation - universal staff positioning
            base_y = STAFF_BASE_Y_START + (xml_note.staff_index * STAFF_SEPARATION)
            
            # Universal Y offset calculation based on XML Y value
            # This maps any XML Y coordinate to appropriate staff position
            y_offset = xml_note.xml_y * 1.2  # Universal scaling factor for Y positioning
            svg_y = int(base_y + y_offset)
            
            # Notehead type (universal for all durations)
            notehead_code = 70 if xml_note.duration in ['whole', 'half'] else 102
            unicode_char = '&#70;' if xml_note.duration in ['whole', 'half'] else '&#102;'
            
            svg_note = SVGNote(
                svg_x=svg_x,
                svg_y=svg_y,
                staff_index=xml_note.staff_index,
                notehead_code=notehead_code,
                unicode_char=unicode_char
            )
            
            svg_notes.append(svg_note)
        
        self.svg_notes = svg_notes
        print(f"   ✅ Calculated {len(svg_notes)} SVG coordinates")
        
    def match_xml_to_midi(self) -> List[Tuple[XMLNote, Optional[MIDINote], float, str]]:
        """Match XML notes to MIDI notes using pitch and timing (includes grace notes)"""
        print(f"🔗 Matching XML to MIDI notes")

        matches = []
        used_midi_indices = set()

        for xml_idx, xml_note in enumerate(self.xml_notes):
            best_match = None
            best_confidence = 0.0
            best_method = "no_match"
            best_midi_idx = -1

            # Use the complete note_name which includes accidentals (F#4, Bb3, etc.)
            xml_pitch = xml_note.note_name

            # SPECIAL HANDLING FOR GRACE NOTES
            # Grace notes appear RIGHT BEFORE the next regular note in MIDI
            if xml_note.is_grace_note:
                # Find the next regular (non-grace) note in same part
                next_regular_note = None
                for future_xml in self.xml_notes[xml_idx + 1:]:
                    if not future_xml.is_grace_note and future_xml.part_id == xml_note.part_id:
                        next_regular_note = future_xml
                        break

                # Match grace note to MIDI note that comes just before the next regular note
                for i, midi_note in enumerate(self.midi_notes):
                    if i in used_midi_indices:
                        continue

                    # Check pitch match (exact or enharmonic)
                    pitch_matches = midi_note.pitch_name == xml_pitch
                    if not pitch_matches:
                        enharmonic_pitches = self.get_enharmonic_equivalents(xml_pitch)
                        pitch_matches = midi_note.pitch_name in enharmonic_pitches

                    if pitch_matches:
                        confidence = 0.85  # High confidence for grace notes
                        method = "grace_note_pitch"

                        # Boost confidence if MIDI track matches XML part
                        if midi_note.track_index == xml_note.staff_index + 1:
                            confidence += 0.1

                        if confidence > best_confidence:
                            best_match = midi_note
                            best_confidence = confidence
                            best_method = method
                            best_midi_idx = i

            # REGULAR NOTE MATCHING
            else:
                # Try exact pitch match first
                for i, midi_note in enumerate(self.midi_notes):
                    if i in used_midi_indices:
                        continue

                    if midi_note.pitch_name == xml_pitch:
                        confidence = 0.9
                        method = "exact_pitch"

                        # Boost confidence using universal track-to-part matching
                        # Match MIDI track index to XML part staff index
                        if midi_note.track_index == xml_note.staff_index + 1:  # +1 because track 0 is usually tempo/meta
                            confidence += 0.1

                        if confidence > best_confidence:
                            best_match = midi_note
                            best_confidence = confidence
                            best_method = method
                            best_midi_idx = i

                # If no exact match, try enharmonic equivalents
                if best_confidence < 0.5:
                    enharmonic_pitches = self.get_enharmonic_equivalents(xml_pitch)
                    for i, midi_note in enumerate(self.midi_notes):
                        if i in used_midi_indices:
                            continue

                        if midi_note.pitch_name in enharmonic_pitches:
                            confidence = 0.7
                            method = "enharmonic"

                            if confidence > best_confidence:
                                best_match = midi_note
                                best_confidence = confidence
                                best_method = method
                                best_midi_idx = i

            if best_midi_idx >= 0:
                used_midi_indices.add(best_midi_idx)

            matches.append((xml_note, best_match, best_confidence, best_method))

        matched_count = sum(1 for _, midi, _, _ in matches if midi is not None)
        grace_count = sum(1 for xml, _, _, _ in matches if xml.is_grace_note)
        print(f"   ✅ Matched {matched_count}/{len(self.xml_notes)} XML notes to MIDI ({grace_count} grace notes)")

        return matches
        
    def get_enharmonic_equivalents(self, note_name: str) -> List[str]:
        """Get enharmonic equivalent note names"""
        enharmonic_map = {
            'C#': ['Db'], 'Db': ['C#'],
            'D#': ['Eb'], 'Eb': ['D#'],
            'F#': ['Gb'], 'Gb': ['F#'],
            'G#': ['Ab'], 'Ab': ['G#'],
            'A#': ['Bb'], 'Bb': ['A#']
        }
        
        equivalents = [note_name]
        for original, alts in enharmonic_map.items():
            if original in note_name:
                for alt in alts:
                    equivalents.append(note_name.replace(original, alt))
        
        return equivalents
        
    def create_universal_notes(self):
        """Create universal notes with all format data"""
        print(f"🌍 Creating universal note registry")
        
        xml_midi_matches = self.match_xml_to_midi()
        universal_notes = []
        
        for i, (xml_note, midi_note, confidence, method) in enumerate(xml_midi_matches):
            # Generate universal ID
            universal_id = str(uuid.uuid4())
            
            # Get corresponding SVG data
            svg_note = self.svg_notes[i] if i < len(self.svg_notes) else None
            
            # Determine timing priority
            timing_priority = 'midi' if midi_note and confidence > 0.8 else 'xml'
            
            universal_note = UniversalNote(
                universal_id=universal_id,
                xml_data=xml_note,
                midi_data=midi_note,
                svg_data=svg_note,
                match_confidence=confidence,
                match_method=method,
                timing_priority=timing_priority
            )
            
            universal_notes.append(universal_note)
        
        self.universal_notes = universal_notes
        print(f"   ✅ Created {len(universal_notes)} universal notes")
        
    def generate_pipeline_manifests(self):
        """Generate manifests for pipeline execution"""
        manifests = {}
        
        # MIDI pipeline manifest
        midi_manifest = []
        for i, note in enumerate(self.universal_notes):
            if note.midi_data:
                midi_manifest.append({
                    'universal_id': note.universal_id,
                    'midi_sequence_id': i,
                    'original_filename': f"note_{i:03d}_{note.midi_data.track_name}_{note.xml_data.note_name}_vel{note.midi_data.velocity}.mid",
                    'audio_filename': f"note_{i:03d}_{note.midi_data.track_name}_{note.xml_data.note_name}_vel{note.midi_data.velocity}.wav",
                    'keyframes_filename': f"note_{i:03d}_{note.midi_data.track_name}_{note.xml_data.note_name}_vel{note.midi_data.velocity}_keyframes.json",
                    'track_name': note.midi_data.track_name,
                    'pitch': note.xml_data.note_name,
                    'timing_data': {
                        'start_seconds': note.midi_data.start_time_seconds,
                        'duration_seconds': note.midi_data.duration_seconds,
                        'velocity': note.midi_data.velocity
                    }
                })
        
        manifests['midi_pipeline'] = midi_manifest
        
        # SVG pipeline manifest
        svg_manifest = []
        for note in self.universal_notes:
            svg_manifest.append({
                'universal_id': note.universal_id,
                'svg_filename': f"notehead_{note.universal_id[:8]}_{note.xml_data.part_id}_{note.xml_data.note_name}_M{note.xml_data.measure}.svg",
                'coordinates': {
                    'svg_x': note.svg_data.svg_x,
                    'svg_y': note.svg_data.svg_y,
                    'staff_index': note.svg_data.staff_index
                },
                'visual_data': {
                    'notehead_code': note.svg_data.notehead_code,
                    'unicode_char': note.svg_data.unicode_char,
                    'duration': note.xml_data.duration
                },
                'instrument_info': {
                    'part_id': note.xml_data.part_id,
                    'measure': note.xml_data.measure
                }
            })
        
        manifests['svg_pipeline'] = svg_manifest
        
        return manifests
        
    def generate_comprehensive_metadata(self, musicxml_file: str, midi_file: str):
        """Generate comprehensive metadata about the coordination"""
        return {
            'coordination_info': {
                'timestamp': datetime.now().isoformat(),
                'musicxml_file': musicxml_file,
                'midi_file': midi_file,
                'total_notes': len(self.universal_notes),
                'coordinator_version': '1.0.0'
            },
            'file_analysis': {
                'xml_notes_found': len(self.xml_notes),
                'midi_notes_found': len(self.midi_notes),
                'svg_coordinates_calculated': len(self.svg_notes)
            },
            'matching_statistics': {
                'exact_pitch_matches': len([n for n in self.universal_notes if n.match_method == 'exact_pitch']),
                'enharmonic_matches': len([n for n in self.universal_notes if n.match_method == 'enharmonic']),
                'unmatched_notes': len([n for n in self.universal_notes if n.match_method == 'no_match']),
                'high_confidence_matches': len([n for n in self.universal_notes if n.match_confidence >= 0.8]),
                'average_confidence': sum(n.match_confidence for n in self.universal_notes) / len(self.universal_notes) if self.universal_notes else 0
            },
            'instrument_breakdown': self.get_instrument_breakdown(),
            'timing_analysis': self.get_timing_analysis(),
            'coordinate_ranges': self.get_coordinate_ranges()
        }
        
    def get_instrument_breakdown(self):
        """Get breakdown by instrument/part"""
        breakdown = {}
        for note in self.universal_notes:
            part_id = note.xml_data.part_id
            if part_id not in breakdown:
                breakdown[part_id] = {
                    'total_notes': 0,
                    'matched_to_midi': 0,
                    'pitch_range': [],
                    'measures': set()
                }
            
            breakdown[part_id]['total_notes'] += 1
            if note.midi_data:
                breakdown[part_id]['matched_to_midi'] += 1
            breakdown[part_id]['pitch_range'].append(note.xml_data.note_name)
            breakdown[part_id]['measures'].add(note.xml_data.measure)
        
        # Convert sets to lists for JSON serialization
        for part_data in breakdown.values():
            part_data['measures'] = sorted(list(part_data['measures']))
            part_data['unique_pitches'] = sorted(list(set(part_data['pitch_range'])))
            del part_data['pitch_range']
        
        return breakdown
        
    def get_timing_analysis(self):
        """Get timing analysis from MIDI data"""
        midi_notes = [n for n in self.universal_notes if n.midi_data]
        if not midi_notes:
            return {}
            
        start_times = [n.midi_data.start_time_seconds for n in midi_notes]
        durations = [n.midi_data.duration_seconds for n in midi_notes]
        
        return {
            'total_duration': max(n.midi_data.end_time_seconds for n in midi_notes) if midi_notes else 0,
            'earliest_note': min(start_times) if start_times else 0,
            'average_duration': sum(durations) / len(durations) if durations else 0,
            'shortest_note': min(durations) if durations else 0,
            'longest_note': max(durations) if durations else 0
        }
        
    def get_coordinate_ranges(self):
        """Get SVG coordinate ranges"""
        if not self.svg_notes:
            return {}
            
        x_coords = [n.svg_x for n in self.svg_notes]
        y_coords = [n.svg_y for n in self.svg_notes]
        
        return {
            'x_range': {'min': min(x_coords), 'max': max(x_coords)},
            'y_range': {'min': min(y_coords), 'max': max(y_coords)},
            'staff_distribution': {
                str(i): len([n for n in self.svg_notes if n.staff_index == i])
                for i in set(n.staff_index for n in self.svg_notes)
            }
        }
        
    def save_coordination_data(self, output_dir: str, musicxml_file: str, midi_file: str):
        """Save all coordination data to output directory"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Universal notes registry
        universal_data = {
            'notes': [asdict(note) for note in self.universal_notes]
        }
        
        with open(os.path.join(output_dir, 'universal_notes_registry.json'), 'w') as f:
            json.dump(universal_data, f, indent=2, default=str)
        
        # Pipeline manifests
        manifests = self.generate_pipeline_manifests()
        
        with open(os.path.join(output_dir, 'midi_pipeline_manifest.json'), 'w') as f:
            json.dump(manifests['midi_pipeline'], f, indent=2)
            
        with open(os.path.join(output_dir, 'svg_pipeline_manifest.json'), 'w') as f:
            json.dump(manifests['svg_pipeline'], f, indent=2)
        
        # Comprehensive metadata
        metadata = self.generate_comprehensive_metadata(musicxml_file, midi_file)
        
        with open(os.path.join(output_dir, 'coordination_metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        print(f"💾 Saved coordination data to: {output_dir}")
        print(f"   📋 universal_notes_registry.json - Complete note registry")
        print(f"   🎵 midi_pipeline_manifest.json - MIDI pipeline tracking")
        print(f"   🖼️  svg_pipeline_manifest.json - SVG pipeline tracking") 
        print(f"   📊 coordination_metadata.json - Comprehensive metadata")

def main():
    if len(sys.argv) < 3:
        print("NOTE COORDINATOR - Universal Note Matching System")
        print("=" * 60)
        print("Usage: python note_coordinator.py <musicxml_file> <midi_file> [output_dir]")
        print("Example: python note_coordinator.py 'Base/SS 9.musicxml' 'Base/Saint-Saens Trio No 2.mid' 'output'")
        print()
        print("This coordinator creates comprehensive note matching across XML, MIDI, and SVG formats.")
        print("It generates universal note IDs and manifests for pipeline tracking.")
        sys.exit(1)
    
    musicxml_file = sys.argv[1]
    midi_file = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "outputs/json/coordination"
    
    print("NOTE COORDINATOR - Universal Note Matching System")
    print("=" * 60)
    print(f"📄 MusicXML: {musicxml_file}")
    print(f"🎵 MIDI: {midi_file}")
    print(f"📁 Output: {output_dir}")
    print()
    
    # Check input files
    if not os.path.exists(musicxml_file):
        print(f"❌ ERROR: MusicXML file not found: {musicxml_file}")
        sys.exit(1)
        
    if not os.path.exists(midi_file):
        print(f"❌ ERROR: MIDI file not found: {midi_file}")
        sys.exit(1)
    
    try:
        # Initialize coordinator
        coordinator = NoteCoordinator()
        
        # Load all format data
        coordinator.load_xml_notes(musicxml_file)
        coordinator.load_midi_notes(midi_file)
        coordinator.calculate_svg_coordinates()
        
        # Create universal note registry
        coordinator.create_universal_notes()
        
        # Save all coordination data
        coordinator.save_coordination_data(output_dir, musicxml_file, midi_file)
        
        # Final summary
        metadata = coordinator.generate_comprehensive_metadata(musicxml_file, midi_file)
        
        print()
        print("🎯 COORDINATION COMPLETE!")
        print("=" * 60)
        print(f"✅ Total Notes: {metadata['coordination_info']['total_notes']}")
        print(f"🔗 High Confidence Matches: {metadata['matching_statistics']['high_confidence_matches']}")
        print(f"📊 Average Match Confidence: {metadata['matching_statistics']['average_confidence']:.2f}")
        print(f"⏱️  Total Duration: {metadata['timing_analysis'].get('total_duration', 0):.2f}s")
        print()
        print("📋 Instrument Breakdown:")
        for part_id, data in metadata['instrument_breakdown'].items():
            print(f"   {part_id}: {data['total_notes']} notes, {data['matched_to_midi']} matched to MIDI")
        print()
        print("🚀 Ready for pipeline execution with universal note tracking!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()