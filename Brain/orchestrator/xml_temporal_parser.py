#!/usr/bin/env python3

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from pathlib import Path

@dataclass
class MusicXMLNote:
    """Complete note representation from MusicXML analysis"""
    pitch: str              # "A4", "C#3", etc.
    duration: int           # In divisions units
    beat_position: float    # Position within measure
    measure_number: int     # Measure location
    part_id: str           # Instrument/part identifier
    voice: Optional[int]    # Voice within part
    tie_type: Optional[str] # "start", "stop", "continue", None
    tied_group_id: Optional[str] # Unique ID for tied note groups
    onset_time: float      # Cumulative time from start of piece
    xml_x: float           # Original XML X coordinate
    xml_y: float           # Original XML Y coordinate
    
    @property
    def pitch_midi(self) -> int:
        """Convert pitch string to MIDI note number."""
        return self._pitch_to_midi(self.pitch)
    
    def _pitch_to_midi(self, pitch: str) -> int:
        """Convert pitch string like 'A4', 'C#3' to MIDI note number."""
        note_to_number = {
            'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
            'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8,
            'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
        }
        
        # Parse the pitch string
        if len(pitch) >= 2:
            if pitch[1] in ['#', 'b']:
                note = pitch[:2]
                octave = int(pitch[2:])
            else:
                note = pitch[0]
                octave = int(pitch[1:])
        else:
            return 60  # Default to C4
        
        # Calculate MIDI number
        midi_number = (octave + 1) * 12 + note_to_number.get(note, 0)
        return midi_number


class XMLTemporalParser:
    """
    XML temporal parser that extracts timing information and handles tied notes
    from MusicXML files. Follows patterns from truly_universal_noteheads_extractor.py
    """
    
    def __init__(self, musicxml_path: Path):
        """Initialize parser with MusicXML file."""
        self.musicxml_path = Path(musicxml_path)
        self.tree = ET.parse(musicxml_path)
        self.root = self.tree.getroot()
        self.divisions_per_quarter = self._extract_divisions()
        self.tempo_map = self._extract_tempo_map()
        
    def _extract_divisions(self) -> int:
        """Extract divisions value for timing resolution (MIDI ticks per quarter note)."""
        # Find divisions in attributes - this determines timing resolution
        divisions_elem = self.root.find('.//attributes/divisions')
        if divisions_elem is not None:
            return int(divisions_elem.text)
        return 480  # Default MIDI resolution
    
    def _extract_tempo_map(self) -> List[Tuple[float, float]]:
        """Extract tempo markings from MusicXML."""
        tempo_map = []
        default_tempo = 120.0  # Default BPM
        
        # Look for metronome markings in direction elements
        for direction in self.root.findall('.//direction'):
            metronome = direction.find('.//metronome')
            if metronome is not None:
                beat_unit = metronome.find('beat-unit')
                per_minute = metronome.find('per-minute')
                
                if beat_unit is not None and per_minute is not None:
                    # Convert to quarter note BPM
                    unit = beat_unit.text
                    bpm = float(per_minute.text)
                    
                    # Convert different note values to quarter note equivalent
                    if unit == 'eighth':
                        bpm = bpm / 2
                    elif unit == 'half':
                        bpm = bpm * 2
                    elif unit == 'whole':
                        bpm = bpm * 4
                    
                    tempo_map.append((0.0, bpm))  # For now, assume tempo at start
        
        if not tempo_map:
            tempo_map.append((0.0, default_tempo))
            
        return tempo_map
    
    def extract_tied_notes(self) -> Dict[str, List[MusicXMLNote]]:
        """
        Extract tied note groups using both <tie> and <tied> elements.
        
        CRITICAL: MusicXML tied note detection requires both elements:
        - <tie> affects MIDI timing 
        - <tied> affects visual notation
        
        Returns:
            Dictionary mapping tied_group_id to list of tied notes
        """
        tied_groups = {}
        tied_group_counter = 0
        active_tied_groups = {}  # Track ongoing tied note sequences
        
        for part in self.root.findall('part'):
            part_id = part.get('id')
            
            for measure in part.findall('measure'):
                measure_num = int(measure.get('number'))
                
                for note in measure.findall('note'):
                    if note.find('rest') is not None:
                        continue
                        
                    # Extract basic note information
                    pitch_elem = note.find('pitch')
                    if pitch_elem is None:
                        continue
                        
                    step = pitch_elem.find('step').text
                    octave = int(pitch_elem.find('octave').text)
                    
                    # Handle accidentals
                    alter_elem = pitch_elem.find('alter')
                    alter = int(alter_elem.text) if alter_elem is not None else 0
                    
                    # Create pitch string with accidentals
                    if alter == 1:
                        pitch_str = f"{step}#{octave}"
                    elif alter == -1:
                        pitch_str = f"{step}b{octave}"
                    else:
                        pitch_str = f"{step}{octave}"
                    
                    # Get voice information
                    voice_elem = note.find('voice')
                    voice = int(voice_elem.text) if voice_elem is not None else 1
                    
                    # Create unique key for this note position
                    note_key = f"{part_id}_voice{voice}_{pitch_str}"
                    
                    # Check for tie elements - CRITICAL: Process both <tie> and <tied>
                    tie_elem = note.find('tie')
                    tied_elem = note.find('notations/tied')
                    
                    tie_type = None
                    if tie_elem is not None:
                        tie_type = tie_elem.get('type')
                    elif tied_elem is not None:
                        tie_type = tied_elem.get('type')
                    
                    # Extract timing information
                    duration_elem = note.find('duration')
                    duration = int(duration_elem.text) if duration_elem is not None else self.divisions_per_quarter
                    
                    # Calculate beat position within measure
                    beat_position = self.calculate_beat_position(note, measure)
                    
                    # Calculate cumulative onset time from start of piece
                    onset_time = self._calculate_onset_time(measure_num, beat_position)
                    
                    # Get XML coordinates
                    xml_x = float(note.get('default-x', 0))
                    xml_y = float(note.get('default-y', 0))
                    
                    # Create MusicXMLNote object
                    xml_note = MusicXMLNote(
                        pitch=pitch_str,
                        duration=duration,
                        beat_position=beat_position,
                        measure_number=measure_num,
                        part_id=part_id,
                        voice=voice,
                        tie_type=tie_type,
                        tied_group_id=None,  # Will be set below
                        onset_time=onset_time,
                        xml_x=xml_x,
                        xml_y=xml_y
                    )
                    
                    # Handle tied note grouping
                    if tie_type == 'start':
                        # Start a new tied group
                        tied_group_counter += 1
                        group_id = f"tied_group_{tied_group_counter}"
                        xml_note.tied_group_id = group_id
                        
                        tied_groups[group_id] = [xml_note]
                        active_tied_groups[note_key] = group_id
                        
                    elif tie_type == 'continue':
                        # Continue existing tied group
                        if note_key in active_tied_groups:
                            group_id = active_tied_groups[note_key]
                            xml_note.tied_group_id = group_id
                            tied_groups[group_id].append(xml_note)
                        
                    elif tie_type == 'stop':
                        # End tied group
                        if note_key in active_tied_groups:
                            group_id = active_tied_groups[note_key]
                            xml_note.tied_group_id = group_id
                            tied_groups[group_id].append(xml_note)
                            # Remove from active tracking
                            del active_tied_groups[note_key]
        
        return tied_groups
    
    def calculate_beat_position(self, note_elem, measure_elem) -> float:
        """
        Calculate beat position of note within measure.
        
        CRITICAL: Extract <divisions> for timing resolution and calculate 
        cumulative position based on note ordering within measure.
        """
        # Get divisions for this measure
        divisions_elem = measure_elem.find('attributes/divisions')
        if divisions_elem is not None:
            divisions = int(divisions_elem.text)
        else:
            divisions = self.divisions_per_quarter
        
        # Calculate cumulative duration before this note
        cumulative_duration = 0
        
        # Find all note elements in order and sum durations until we reach our note
        for prev_note in measure_elem.findall('note'):
            if prev_note == note_elem:
                break
                
            # Skip if this is a chord note (has <chord> element)
            if prev_note.find('chord') is not None:
                continue
                
            duration_elem = prev_note.find('duration')
            if duration_elem is not None:
                cumulative_duration += int(duration_elem.text)
        
        # Convert to beat position (1-based, where beat 1 is start of measure)
        beat_position = (cumulative_duration / divisions) + 1.0
        return beat_position
    
    def _calculate_onset_time(self, measure_number: int, beat_position: float) -> float:
        """
        Calculate cumulative onset time from start of piece in SECONDS.
        
        Converts from quarter note beats to seconds using tempo map.
        """
        # Simple calculation assuming 4/4 time - can be enhanced
        beats_per_measure = 4
        beats_before_measure = (measure_number - 1) * beats_per_measure
        total_beats = beats_before_measure + (beat_position - 1)
        
        # Convert beats to seconds using tempo
        # Get tempo from tempo map (for now use first tempo)
        if self.tempo_map:
            tempo_bpm = self.tempo_map[0][1]  # First tempo value
        else:
            tempo_bpm = 120.0  # Default tempo
        
        # Convert quarter note beats to seconds
        seconds_per_beat = 60.0 / tempo_bpm
        total_seconds = total_beats * seconds_per_beat
        
        return total_seconds
    
    def extract_all_notes(self) -> List[MusicXMLNote]:
        """
        Extract all notes from MusicXML with timing information.
        
        Mirrors pattern from truly_universal_noteheads_extractor.py
        but adds temporal/timing analysis.
        """
        notes = []
        
        for part in self.root.findall('part'):
            part_id = part.get('id')
            
            for measure in part.findall('measure'):
                measure_num = int(measure.get('number'))
                
                for note in measure.findall('note'):
                    if note.find('rest') is not None:
                        continue
                        
                    pitch_elem = note.find('pitch')
                    if pitch_elem is None:
                        continue
                        
                    step = pitch_elem.find('step').text
                    octave = int(pitch_elem.find('octave').text)
                    
                    # Handle accidentals
                    alter_elem = pitch_elem.find('alter')
                    alter = int(alter_elem.text) if alter_elem is not None else 0
                    
                    # Create pitch string with accidentals
                    if alter == 1:
                        pitch_str = f"{step}#{octave}"
                    elif alter == -1:
                        pitch_str = f"{step}b{octave}"
                    else:
                        pitch_str = f"{step}{octave}"
                    
                    # Get voice information
                    voice_elem = note.find('voice')
                    voice = int(voice_elem.text) if voice_elem is not None else 1
                    
                    # Check for tie elements
                    tie_elem = note.find('tie')
                    tied_elem = note.find('notations/tied')
                    
                    tie_type = None
                    if tie_elem is not None:
                        tie_type = tie_elem.get('type')
                    elif tied_elem is not None:
                        tie_type = tied_elem.get('type')
                    
                    # Extract timing information
                    duration_elem = note.find('duration')
                    duration = int(duration_elem.text) if duration_elem is not None else self.divisions_per_quarter
                    
                    # Calculate beat position within measure
                    beat_position = self.calculate_beat_position(note, measure)
                    
                    # Calculate cumulative onset time from start of piece
                    onset_time = self._calculate_onset_time(measure_num, beat_position)
                    
                    # Get XML coordinates (following existing pattern)
                    xml_x = float(note.get('default-x', 0))
                    xml_y = float(note.get('default-y', 0))
                    
                    # Create MusicXMLNote object
                    xml_note = MusicXMLNote(
                        pitch=pitch_str,
                        duration=duration,
                        beat_position=beat_position,
                        measure_number=measure_num,
                        part_id=part_id,
                        voice=voice,
                        tie_type=tie_type,
                        tied_group_id=None,  # Set separately in tied note processing
                        onset_time=onset_time,
                        xml_x=xml_x,
                        xml_y=xml_y
                    )
                    
                    notes.append(xml_note)
        
        return notes
    
    def get_timing_summary(self) -> Dict:
        """Get summary of timing information for debugging and validation."""
        notes = self.extract_all_notes()
        tied_groups = self.extract_tied_notes()
        
        return {
            'total_notes': len(notes),
            'divisions_per_quarter': self.divisions_per_quarter,
            'tempo_map': self.tempo_map,
            'tied_groups_count': len(tied_groups),
            'tied_notes_total': sum(len(group) for group in tied_groups.values()),
            'parts': list(set(note.part_id for note in notes)),
            'measure_range': (
                min(note.measure_number for note in notes) if notes else 0,
                max(note.measure_number for note in notes) if notes else 0
            )
        }


def main():
    """Test the XML temporal parser with a MusicXML file."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python xml_temporal_parser.py <musicxml_file>")
        print("Example: python xml_temporal_parser.py 'Base/SS 9.musicxml'")
        sys.exit(1)
    
    musicxml_file = sys.argv[1]
    
    print("XML TEMPORAL PARSER")
    print("=" * 50)
    print(f"Input: {musicxml_file}")
    print()
    
    try:
        # Initialize parser
        parser = XMLTemporalParser(Path(musicxml_file))
        
        # Extract timing summary
        summary = parser.get_timing_summary()
        print(f"✅ Timing Analysis Complete")
        print(f"   Total notes: {summary['total_notes']}")
        print(f"   Parts: {summary['parts']}")
        print(f"   Measures: {summary['measure_range'][0]}-{summary['measure_range'][1]}")
        print(f"   Divisions per quarter: {summary['divisions_per_quarter']}")
        print(f"   Tied groups: {summary['tied_groups_count']}")
        print(f"   Tied notes total: {summary['tied_notes_total']}")
        print()
        
        # Extract all notes
        all_notes = parser.extract_all_notes()
        print(f"✅ Extracted {len(all_notes)} notes with timing")
        
        # Show first few notes as example
        print("\nFirst 5 notes with timing:")
        for i, note in enumerate(all_notes[:5]):
            print(f"  {i+1}. {note.pitch} M{note.measure_number} Beat{note.beat_position:.2f} "
                  f"Onset:{note.onset_time:.2f} {note.part_id}")
            if note.tie_type:
                print(f"      Tie: {note.tie_type}")
        
        # Extract tied notes
        tied_groups = parser.extract_tied_notes()
        if tied_groups:
            print(f"\n✅ Found {len(tied_groups)} tied note groups:")
            for group_id, notes_in_group in tied_groups.items():
                print(f"  {group_id}: {len(notes_in_group)} notes")
                for note in notes_in_group:
                    print(f"    {note.pitch} M{note.measure_number} tie:{note.tie_type}")
        else:
            print(f"\n✅ No tied notes found in this piece")
        
        print(f"\n🎯 SUCCESS! Temporal analysis complete for {musicxml_file}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()