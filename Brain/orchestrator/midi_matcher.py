#!/usr/bin/env python3
"""
MIDI Matching Engine

This module implements tolerance-based MIDI note matching for synchronization
between MusicXML notation and MIDI performance data. It handles unquantized
MIDI variations with configurable timing tolerance and confidence scoring.

Critical Features:
- Tolerance-based matching (default 100ms, configurable)
- Pitch + timing + instrument matching algorithm 
- Confidence scoring for match quality assessment
- Support for unquantized MIDI timing variations
- Multi-factor scoring with pitch exactness, timing proximity, and context
"""

import mido
import sys
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Set
import json
import math


@dataclass
class MIDINote:
    """MIDI note representation with precise timing"""
    pitch: int              # MIDI note number (60 = C4)
    velocity: int           # 0-127
    start_time: float       # Seconds from start of MIDI
    end_time: float         # End time in seconds
    duration: float         # Duration in seconds
    channel: int            # MIDI channel
    instrument: str         # Derived instrument name
    track_index: int        # Track number in MIDI file
    track_name: str         # Track name from MIDI
    note_id: str           # Unique identifier for this note
    
    @property
    def pitch_name(self) -> str:
        """Convert MIDI pitch to note name (e.g., 60 -> C4)"""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = self.pitch // 12 - 1
        note = notes[self.pitch % 12]
        return f"{note}{octave}"


@dataclass
class MusicXMLNote:
    """MusicXML note representation for matching"""
    pitch: str              # "A4", "C#3", etc.
    duration: int           # In divisions units
    beat_position: float    # Position within measure
    measure_number: int     # Measure location
    part_id: str           # Instrument/part identifier
    voice: Optional[int]    # Voice within part
    tie_type: Optional[str] # "start", "stop", "continue", None
    tied_group_id: Optional[str] # Unique ID for tied note groups
    onset_time: float      # Cumulative time from start of piece
    
    @property
    def pitch_midi(self) -> int:
        """Convert note name to MIDI number for comparison"""
        return self._note_name_to_midi(self.pitch)
    
    def _note_name_to_midi(self, note_name: str) -> int:
        """Convert note name like 'A4' to MIDI number like 69"""
        # Parse note name (e.g., "C#4", "Bb3")
        note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
        
        # Handle different note name formats
        note_name = note_name.strip().upper()
        
        if len(note_name) < 2:
            raise ValueError(f"Invalid note name: {note_name}")
        
        # Extract base note
        base_note = note_name[0]
        if base_note not in note_map:
            raise ValueError(f"Invalid note: {base_note}")
        
        # Extract accidental and octave
        accidental = 0
        octave_start = 1
        
        if len(note_name) > 1:
            if note_name[1] == '#':
                accidental = 1
                octave_start = 2
            elif note_name[1] == 'B':
                accidental = -1
                octave_start = 2
        
        # Extract octave number
        try:
            octave = int(note_name[octave_start:])
        except (ValueError, IndexError):
            raise ValueError(f"Invalid octave in note name: {note_name}")
        
        # Calculate MIDI number
        midi_number = (octave + 1) * 12 + note_map[base_note] + accidental
        return midi_number


@dataclass
class NoteMatch:
    """Represents a matched XML-MIDI note pair with confidence scoring"""
    xml_note: MusicXMLNote
    midi_note: MIDINote
    confidence: float       # 0.0 to 1.0 confidence score
    time_difference: float  # Absolute time difference in seconds
    pitch_match: bool       # Whether pitches match exactly
    timing_score: float     # Sub-score for timing accuracy
    context_score: float    # Sub-score for contextual factors
    match_type: str        # "exact", "tolerance", "approximate"


class MIDIMatcher:
    """
    Tolerance-based MIDI matching engine for synchronization.
    
    Matches MIDI notes with XML notes using pitch + timing + confidence scoring.
    Handles unquantized MIDI variations with configurable tolerance.
    """
    
    def __init__(self, tolerance_ms: float = 100.0, strict_pitch: bool = True):
        """
        Initialize MIDI matcher with configurable parameters.
        
        Args:
            tolerance_ms: Maximum timing difference in milliseconds (default 100ms)
            strict_pitch: Whether pitch must match exactly (default True)
        """
        self.tolerance_seconds = tolerance_ms / 1000.0
        self.strict_pitch = strict_pitch
        self.matched_midi_notes: Set[str] = set()  # Track used MIDI notes
        self.matched_xml_notes: Set[str] = set()   # Track used XML notes
        
        print(f"🎯 MIDI MATCHER INITIALIZED")
        print(f"⏱️  Tolerance: {tolerance_ms}ms ({self.tolerance_seconds:.3f}s)")
        print(f"🎵 Strict pitch matching: {strict_pitch}")
        print()
    
    def match_notes_with_tolerance(
        self, 
        xml_notes: List[MusicXMLNote], 
        midi_notes: List[MIDINote],
        min_confidence: float = 0.5
    ) -> List[NoteMatch]:
        """
        Match XML notes with MIDI notes using tolerance-based algorithm.
        
        Args:
            xml_notes: List of MusicXML notes to match
            midi_notes: List of MIDI notes to match against
            min_confidence: Minimum confidence threshold for matches
            
        Returns:
            List of NoteMatch objects with confidence scoring
        """
        print(f"MIDI TOLERANCE MATCHING")
        print("=" * 50)
        print(f"🎼 XML notes to match: {len(xml_notes)}")
        print(f"🎹 MIDI notes available: {len(midi_notes)}")
        print(f"🎯 Minimum confidence: {min_confidence}")
        print()
        
        matches = []
        unmatched_xml = []
        
        # Sort XML notes by onset time for chronological processing
        sorted_xml_notes = sorted(xml_notes, key=lambda x: x.onset_time)
        
        for xml_note in sorted_xml_notes:
            # Find candidate MIDI notes within tolerance
            candidates = self._find_candidate_matches(xml_note, midi_notes)
            
            if candidates:
                # Score all candidates and select the best
                best_match = self._select_best_match(xml_note, candidates)
                
                if best_match and best_match.confidence >= min_confidence:
                    matches.append(best_match)
                    # Mark notes as used to avoid double-matching
                    self.matched_midi_notes.add(best_match.midi_note.note_id)
                    xml_id = f"{xml_note.part_id}_{xml_note.measure_number}_{xml_note.beat_position}_{xml_note.pitch}"
                    self.matched_xml_notes.add(xml_id)
                    
                    print(f"✅ MATCH: {xml_note.pitch} @ {xml_note.onset_time:.3f}s → "
                          f"MIDI {best_match.midi_note.pitch_name} @ {best_match.midi_note.start_time:.3f}s "
                          f"(confidence: {best_match.confidence:.2f})")
                else:
                    unmatched_xml.append(xml_note)
                    print(f"⚠️  LOW CONFIDENCE: {xml_note.pitch} @ {xml_note.onset_time:.3f}s "
                          f"(best: {best_match.confidence:.2f} < {min_confidence})")
            else:
                unmatched_xml.append(xml_note)
                print(f"❌ NO CANDIDATES: {xml_note.pitch} @ {xml_note.onset_time:.3f}s")
        
        # Summary statistics
        print()
        print(f"📊 MATCHING RESULTS:")
        print(f"✅ Successful matches: {len(matches)}")
        print(f"❌ Unmatched XML notes: {len(unmatched_xml)}")
        print(f"🎯 Match rate: {len(matches) / len(xml_notes) * 100:.1f}%")
        
        if matches:
            avg_confidence = sum(m.confidence for m in matches) / len(matches)
            avg_time_error = sum(m.time_difference for m in matches) / len(matches)
            print(f"📈 Average confidence: {avg_confidence:.3f}")
            print(f"⏱️  Average timing error: {avg_time_error * 1000:.1f}ms")
        
        print()
        return matches
    
    def _find_candidate_matches(
        self, 
        xml_note: MusicXMLNote, 
        midi_notes: List[MIDINote]
    ) -> List[MIDINote]:
        """Find MIDI notes that could potentially match the XML note"""
        candidates = []
        
        for midi_note in midi_notes:
            # Skip if already matched
            if midi_note.note_id in self.matched_midi_notes:
                continue
            
            # Check pitch matching
            if self.strict_pitch:
                if xml_note.pitch_midi != midi_note.pitch:
                    continue
            else:
                # Allow some pitch variation (e.g., octave errors)
                pitch_diff = abs(xml_note.pitch_midi - midi_note.pitch)
                if pitch_diff > 12:  # More than one octave difference
                    continue
            
            # Check timing within tolerance
            time_diff = abs(xml_note.onset_time - midi_note.start_time)
            if time_diff <= self.tolerance_seconds:
                candidates.append(midi_note)
        
        return candidates
    
    def _select_best_match(
        self, 
        xml_note: MusicXMLNote, 
        candidates: List[MIDINote]
    ) -> Optional[NoteMatch]:
        """Select the best candidate match using multi-factor scoring"""
        if not candidates:
            return None
        
        scored_candidates = []
        
        for midi_note in candidates:
            # Calculate comprehensive match score
            match = self._calculate_match_score(xml_note, midi_note)
            scored_candidates.append(match)
        
        # Return the highest confidence match
        best_match = max(scored_candidates, key=lambda x: x.confidence)
        return best_match
    
    def _calculate_match_score(
        self, 
        xml_note: MusicXMLNote, 
        midi_note: MIDINote
    ) -> NoteMatch:
        """Calculate comprehensive confidence score for a potential match"""
        # Timing score (0.0 to 1.0, higher is better)
        time_diff = abs(xml_note.onset_time - midi_note.start_time)
        timing_score = max(0.0, 1.0 - (time_diff / self.tolerance_seconds))
        
        # Pitch score (1.0 for exact, partial for octave errors)
        pitch_match = xml_note.pitch_midi == midi_note.pitch
        if pitch_match:
            pitch_score = 1.0
        else:
            # Penalize octave errors but don't eliminate completely
            pitch_diff = abs(xml_note.pitch_midi - midi_note.pitch)
            if pitch_diff % 12 == 0:  # Same note, different octave
                pitch_score = 0.7
            else:
                pitch_score = 0.0
        
        # Context score based on musical factors
        context_score = self._calculate_context_score(xml_note, midi_note)
        
        # Combined confidence score (weighted average)
        confidence = (
            0.4 * timing_score +    # Timing is very important
            0.4 * pitch_score +     # Pitch is very important  
            0.2 * context_score     # Context provides additional validation
        )
        
        # Determine match type
        if pitch_match and time_diff < self.tolerance_seconds * 0.1:  # Within 10% of tolerance
            match_type = "exact"
        elif pitch_match and time_diff < self.tolerance_seconds:
            match_type = "tolerance"
        else:
            match_type = "approximate"
        
        return NoteMatch(
            xml_note=xml_note,
            midi_note=midi_note,
            confidence=confidence,
            time_difference=time_diff,
            pitch_match=pitch_match,
            timing_score=timing_score,
            context_score=context_score,
            match_type=match_type
        )
    
    def _calculate_context_score(
        self, 
        xml_note: MusicXMLNote, 
        midi_note: MIDINote
    ) -> float:
        """Calculate context-based scoring factors"""
        score = 0.5  # Base score
        
        # Instrument context (if available)
        if hasattr(xml_note, 'part_id') and hasattr(midi_note, 'instrument'):
            # Simple instrument name matching
            xml_instrument = xml_note.part_id.lower()
            midi_instrument = midi_note.instrument.lower()
            
            # Basic instrument family matching
            if any(inst in xml_instrument and inst in midi_instrument 
                   for inst in ['flute', 'violin', 'piano', 'cello']):
                score += 0.3
        
        # Velocity context (reasonable range)
        if 40 <= midi_note.velocity <= 100:  # Typical performance range
            score += 0.1
        
        # Duration context (avoid very short glitches)
        if midi_note.duration > 0.05:  # Longer than 50ms
            score += 0.1
        
        return min(1.0, score)
    
    def get_match_statistics(self, matches: List[NoteMatch]) -> Dict:
        """Generate comprehensive statistics about matching quality"""
        if not matches:
            return {
                'total_matches': 0,
                'average_confidence': 0.0,
                'average_timing_error_ms': 0.0,
                'match_types': {},
                'pitch_accuracy': 0.0
            }
        
        # Calculate statistics
        total_matches = len(matches)
        avg_confidence = sum(m.confidence for m in matches) / total_matches
        avg_timing_error = sum(m.time_difference for m in matches) / total_matches
        
        # Match type distribution
        match_types = {}
        for match in matches:
            match_type = match.match_type
            if match_type not in match_types:
                match_types[match_type] = 0
            match_types[match_type] += 1
        
        # Pitch accuracy
        exact_pitch_matches = sum(1 for m in matches if m.pitch_match)
        pitch_accuracy = exact_pitch_matches / total_matches
        
        # Timing distribution
        timing_errors_ms = [m.time_difference * 1000 for m in matches]
        min_error = min(timing_errors_ms)
        max_error = max(timing_errors_ms)
        
        return {
            'total_matches': total_matches,
            'average_confidence': avg_confidence,
            'average_timing_error_ms': avg_timing_error * 1000,
            'min_timing_error_ms': min_error,
            'max_timing_error_ms': max_error,
            'match_types': match_types,
            'pitch_accuracy': pitch_accuracy,
            'exact_pitch_matches': exact_pitch_matches,
            'timing_within_tolerance': total_matches  # All matches are within tolerance by definition
        }
    
    def save_matches_to_json(self, matches: List[NoteMatch], output_path: Path):
        """Save match results to JSON file for analysis and debugging"""
        match_data = {
            'matcher_config': {
                'tolerance_seconds': self.tolerance_seconds,
                'strict_pitch': self.strict_pitch
            },
            'statistics': self.get_match_statistics(matches),
            'matches': []
        }
        
        for match in matches:
            match_dict = {
                'xml_note': {
                    'pitch': match.xml_note.pitch,
                    'onset_time': match.xml_note.onset_time,
                    'measure': match.xml_note.measure_number,
                    'beat_position': match.xml_note.beat_position,
                    'part_id': match.xml_note.part_id
                },
                'midi_note': {
                    'pitch': match.midi_note.pitch,
                    'pitch_name': match.midi_note.pitch_name,
                    'start_time': match.midi_note.start_time,
                    'velocity': match.midi_note.velocity,
                    'instrument': match.midi_note.instrument,
                    'track_name': match.midi_note.track_name
                },
                'scoring': {
                    'confidence': match.confidence,
                    'time_difference': match.time_difference,
                    'timing_score': match.timing_score,
                    'context_score': match.context_score,
                    'match_type': match.match_type,
                    'pitch_match': match.pitch_match
                }
            }
            match_data['matches'].append(match_dict)
        
        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(match_data, f, indent=2)
        
        print(f"💾 Match results saved to: {output_path}")
        return output_path
    
    def reset_matching_state(self):
        """Reset matcher state for fresh matching session"""
        self.matched_midi_notes.clear()
        self.matched_xml_notes.clear()
        print("🔄 Matcher state reset")


def create_midi_notes_from_master_timing(master_timing_data: Dict) -> List[MIDINote]:
    """
    Create MIDINote objects from master timing extraction data.
    
    Args:
        master_timing_data: Data from MasterMIDIExtractor
        
    Returns:
        List of MIDINote objects ready for matching
    """
    midi_notes = []
    
    for event in master_timing_data.get('note_events', []):
        midi_note = MIDINote(
            pitch=event['pitch_midi'],
            velocity=event['velocity'],
            start_time=event['start_time_seconds'],
            end_time=event['end_time_seconds'],
            duration=event['duration_seconds'],
            channel=event['channel'],
            instrument=event['instrument'],
            track_index=event['track_index'],
            track_name=event['track_name'],
            note_id=f"midi_{event['track_index']}_{event['start_time_seconds']:.3f}_{event['pitch_midi']}"
        )
        midi_notes.append(midi_note)
    
    return midi_notes


def main():
    """CLI interface for testing MIDI matching functionality"""
    if len(sys.argv) < 3:
        print("Usage: python midi_matcher.py <master_timing_json> <xml_notes_json> [tolerance_ms]")
        print("Example: python midi_matcher.py timing.json xml_notes.json 100")
        sys.exit(1)
    
    timing_file = sys.argv[1]
    xml_file = sys.argv[2]
    tolerance_ms = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0
    
    if not os.path.exists(timing_file):
        print(f"❌ ERROR: Master timing file not found: {timing_file}")
        sys.exit(1)
    
    if not os.path.exists(xml_file):
        print(f"❌ ERROR: XML notes file not found: {xml_file}")
        sys.exit(1)
    
    try:
        # Load master timing data
        with open(timing_file, 'r') as f:
            master_timing = json.load(f)
        
        # Load XML notes data (placeholder - would need actual XML parser)
        with open(xml_file, 'r') as f:
            xml_data = json.load(f)
        
        # Create MIDI notes from master timing
        midi_notes = create_midi_notes_from_master_timing(master_timing)
        
        # Create XML notes (placeholder implementation)
        # In real implementation, this would come from XMLTemporalParser
        xml_notes = []  # Would be populated from actual XML parsing
        
        print(f"🎵 Loaded {len(midi_notes)} MIDI notes from timing data")
        print(f"🎼 Loaded {len(xml_notes)} XML notes")
        print()
        
        # Initialize matcher and perform matching
        matcher = MIDIMatcher(tolerance_ms=tolerance_ms)
        matches = matcher.match_notes_with_tolerance(xml_notes, midi_notes)
        
        # Save results
        output_path = Path(timing_file).parent / "midi_matches.json"
        matcher.save_matches_to_json(matches, output_path)
        
        # Display statistics
        stats = matcher.get_match_statistics(matches)
        print(f"📊 FINAL STATISTICS:")
        print(f"✅ Total matches: {stats['total_matches']}")
        print(f"🎯 Average confidence: {stats['average_confidence']:.3f}")
        print(f"⏱️  Average timing error: {stats['average_timing_error_ms']:.1f}ms")
        print(f"🎵 Pitch accuracy: {stats['pitch_accuracy']:.1%}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()