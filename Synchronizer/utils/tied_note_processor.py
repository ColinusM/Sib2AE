#!/usr/bin/env python3
"""
Tied Note Processor

This module handles complex tied note relationships where the number of visual
noteheads differs from MIDI events (e.g., 3 noteheads for 1 MIDI note in tied sequences).
It processes tied note chains, coordinates multiple noteheads with single MIDI events,
and calculates start times for tied notes based on master MIDI timing.

Critical Features:
- Handles complex 3:1 notehead-to-MIDI relationships
- Processes tied note chains and relationships
- Coordinates multiple noteheads with single MIDI events
- Calculates timing approximations for tied-to notes
- Preserves master MIDI timing integrity for primary tied notes
"""

import sys
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
import json
import math

# Import our established data models
from .xml_temporal_parser import MusicXMLNote, XMLTemporalParser
from .midi_matcher import MIDINote, MIDIMatcher, NoteMatch


@dataclass
class TiedNoteGroup:
    """Represents a group of tied notes that form a single musical entity"""
    group_id: str                           # Unique identifier for this tied group
    notes: List[MusicXMLNote]              # All notes in the tied sequence
    primary_note: MusicXMLNote             # The first note (gets MIDI timing)
    tied_notes: List[MusicXMLNote]         # Subsequent notes (calculated timing)
    total_duration: float                  # Combined duration in beats
    master_midi_start_time: Optional[float] = None  # From matched MIDI note
    master_midi_end_time: Optional[float] = None    # From matched MIDI note
    matched_midi_note: Optional[MIDINote] = None    # The single MIDI note for this group
    
    def __post_init__(self):
        """Automatically categorize notes after initialization"""
        if self.notes:
            # Sort notes by onset time to ensure chronological order
            self.notes = sorted(self.notes, key=lambda x: x.onset_time)
            self.primary_note = self.notes[0]
            self.tied_notes = self.notes[1:] if len(self.notes) > 1 else []
            
            # Calculate total duration
            self.total_duration = sum(note.duration for note in self.notes)


@dataclass
class TiedNoteAssignment:
    """Represents a tied note with calculated start timing for After Effects"""
    note: MusicXMLNote                     # The XML note
    calculated_start_time: float           # Calculated start time in seconds
    is_primary: bool                       # True if this gets MIDI timing directly
    tied_group_id: str                     # Links to the tied group
    master_start_time: float               # From master MIDI reference
    position_in_group: int                 # 0=primary, 1=first tied, etc.
    timing_confidence: float               # Confidence in calculated timing (0-1)


class TiedNoteProcessor:
    """
    Processor for handling tied note relationships and timing calculations.
    
    Handles the complex case where multiple visual noteheads (3 in tied sequences)
    correspond to a single MIDI note event from the master MIDI file.
    """
    
    def __init__(self, beats_per_minute: float = 120.0, verbose: bool = True):
        """
        Initialize tied note processor.
        
        Args:
            beats_per_minute: Default tempo for beat-to-seconds conversion
            verbose: Whether to print detailed processing information
        """
        self.default_bpm = beats_per_minute
        self.verbose = verbose
        self.tied_groups: Dict[str, TiedNoteGroup] = {}
        self.assignments: List[TiedNoteAssignment] = []
        
        if self.verbose:
            print(f"🔗 TIED NOTE PROCESSOR INITIALIZED")
            print(f"🎵 Default tempo: {beats_per_minute} BPM")
            print()
    
    def process_tied_relationships(
        self, 
        xml_notes: List[MusicXMLNote],
        tied_groups_data: Dict[str, List[MusicXMLNote]],
        note_matches: List[NoteMatch],
        tempo_map: List[Tuple[float, float]] = None
    ) -> List[TiedNoteAssignment]:
        """
        Process tied note relationships and create timing assignments.
        
        Args:
            xml_notes: All XML notes from the score
            tied_groups_data: Tied note groups from XML parser
            note_matches: Matched XML-MIDI note pairs
            tempo_map: List of (time_seconds, bpm) pairs from master MIDI
            
        Returns:
            List of TiedNoteAssignment objects with calculated timing
        """
        if self.verbose:
            print(f"TIED NOTE RELATIONSHIP PROCESSING")
            print("=" * 50)
            print(f"🎼 Total XML notes: {len(xml_notes)}")
            print(f"🔗 Tied groups: {len(tied_groups_data)}")
            print(f"🎯 Note matches: {len(note_matches)}")
            print()
        
        # Step 1: Create structured tied note groups
        self._create_tied_note_groups(tied_groups_data)
        
        # Step 2: Match tied groups with MIDI notes
        self._match_tied_groups_with_midi(note_matches)
        
        # Step 3: Calculate timing for all notes in tied groups
        self._calculate_tied_note_timing(tempo_map or [(0.0, self.default_bpm)])
        
        # Step 4: Handle non-tied notes (direct 1:1 mapping)
        self._process_non_tied_notes(xml_notes, note_matches)
        
        # Step 5: Validate and sort assignments
        self._validate_assignments()
        
        return self.assignments
    
    def _create_tied_note_groups(self, tied_groups_data: Dict[str, List[MusicXMLNote]]):
        """Create structured TiedNoteGroup objects from raw tied note data"""
        if self.verbose:
            print(f"📋 Creating structured tied note groups...")
        
        for group_id, notes_list in tied_groups_data.items():
            if len(notes_list) < 2:
                if self.verbose:
                    print(f"⚠️  Skipping single-note group: {group_id}")
                continue
            
            tied_group = TiedNoteGroup(
                group_id=group_id,
                notes=notes_list,
                primary_note=notes_list[0],  # Will be properly sorted in __post_init__
                tied_notes=[],
                total_duration=0
            )
            
            self.tied_groups[group_id] = tied_group
            
            if self.verbose:
                print(f"✅ Group {group_id}: {len(notes_list)} notes, "
                      f"primary: {tied_group.primary_note.pitch} @ M{tied_group.primary_note.measure_number}")
        
        if self.verbose:
            print(f"📊 Created {len(self.tied_groups)} tied note groups")
            print()
    
    def _match_tied_groups_with_midi(self, note_matches: List[NoteMatch]):
        """Match tied note groups with their corresponding MIDI notes"""
        if self.verbose:
            print(f"🎯 Matching tied groups with MIDI notes...")
        
        # Create lookup for matched notes
        xml_to_midi_map = {}
        for match in note_matches:
            xml_key = self._create_xml_note_key(match.xml_note)
            xml_to_midi_map[xml_key] = match
        
        matched_groups = 0
        
        for group_id, tied_group in self.tied_groups.items():
            # Try to match the primary note of the tied group
            primary_key = self._create_xml_note_key(tied_group.primary_note)
            
            if primary_key in xml_to_midi_map:
                match = xml_to_midi_map[primary_key]
                tied_group.matched_midi_note = match.midi_note
                tied_group.master_midi_start_time = match.midi_note.start_time
                tied_group.master_midi_end_time = match.midi_note.end_time
                matched_groups += 1
                
                if self.verbose:
                    print(f"✅ Group {group_id} matched with MIDI: "
                          f"{match.midi_note.pitch_name} @ {match.midi_note.start_time:.3f}s "
                          f"(confidence: {match.confidence:.2f})")
            else:
                if self.verbose:
                    print(f"❌ Group {group_id} primary note not matched: "
                          f"{tied_group.primary_note.pitch} @ {tied_group.primary_note.onset_time:.3f}s")
        
        if self.verbose:
            print(f"📈 Matched {matched_groups}/{len(self.tied_groups)} tied groups with MIDI")
            print()
    
    def _calculate_tied_note_timing(self, tempo_map: List[Tuple[float, float]]):
        """Calculate precise timing for all notes in tied groups"""
        if self.verbose:
            print(f"⏱️  Calculating tied note timing...")
        
        for group_id, tied_group in self.tied_groups.items():
            if tied_group.matched_midi_note is None:
                if self.verbose:
                    print(f"⚠️  Skipping unmatched group: {group_id}")
                continue
            
            # Primary note gets exact MIDI timing
            primary_assignment = TiedNoteAssignment(
                note=tied_group.primary_note,
                calculated_start_time=tied_group.master_midi_start_time,
                is_primary=True,
                tied_group_id=group_id,
                master_start_time=tied_group.master_midi_start_time,
                position_in_group=0,
                timing_confidence=1.0  # Exact from MIDI
            )
            self.assignments.append(primary_assignment)
            
            if self.verbose:
                print(f"🎯 Primary note {tied_group.primary_note.pitch}: "
                      f"{tied_group.master_midi_start_time:.3f}s (MIDI exact)")
            
            # Calculate timing for tied notes (approximations)
            if tied_group.tied_notes:
                self._calculate_tied_approximations(tied_group, tempo_map)
    
    def _calculate_tied_approximations(
        self, 
        tied_group: TiedNoteGroup, 
        tempo_map: List[Tuple[float, float]]
    ):
        """Calculate approximate start times for tied notes in a group"""
        primary_note = tied_group.primary_note
        master_start = tied_group.master_midi_start_time
        master_end = tied_group.master_midi_end_time
        total_midi_duration = master_end - master_start
        
        # Calculate proportional timing based on XML durations
        cumulative_xml_duration = primary_note.duration
        total_xml_duration = tied_group.total_duration
        
        for i, tied_note in enumerate(tied_group.tied_notes):
            # Calculate proportional position within the tied group
            proportion = cumulative_xml_duration / total_xml_duration
            
            # Calculate start time as proportion of MIDI duration
            calculated_start = master_start + (proportion * total_midi_duration)
            
            # Confidence decreases for later tied notes
            confidence = max(0.3, 0.9 - (i * 0.2))
            
            tied_assignment = TiedNoteAssignment(
                note=tied_note,
                calculated_start_time=calculated_start,
                is_primary=False,
                tied_group_id=tied_group.group_id,
                master_start_time=master_start,
                position_in_group=i + 1,
                timing_confidence=confidence
            )
            self.assignments.append(tied_assignment)
            
            if self.verbose:
                print(f"  🔗 Tied note {tied_note.pitch} pos{i+1}: "
                      f"{calculated_start:.3f}s (calculated, confidence: {confidence:.2f})")
            
            # Update cumulative duration for next iteration
            cumulative_xml_duration += tied_note.duration
    
    def _process_non_tied_notes(
        self, 
        xml_notes: List[MusicXMLNote], 
        note_matches: List[NoteMatch]
    ):
        """Process notes that are not part of tied groups (direct 1:1 mapping)"""
        if self.verbose:
            print(f"🎵 Processing non-tied notes...")
        
        # Get set of all notes that are already in tied groups
        tied_notes_set = set()
        for tied_group in self.tied_groups.values():
            for note in tied_group.notes:
                tied_notes_set.add(self._create_xml_note_key(note))
        
        # Create lookup for matched notes
        xml_to_midi_map = {}
        for match in note_matches:
            xml_key = self._create_xml_note_key(match.xml_note)
            xml_to_midi_map[xml_key] = match
        
        non_tied_count = 0
        
        # Process notes that are not in tied groups
        for xml_note in xml_notes:
            xml_key = self._create_xml_note_key(xml_note)
            
            # Skip if this note is already part of a tied group
            if xml_key in tied_notes_set:
                continue
            
            # Check if this note has a MIDI match
            if xml_key in xml_to_midi_map:
                match = xml_to_midi_map[xml_key]
                
                assignment = TiedNoteAssignment(
                    note=xml_note,
                    calculated_start_time=match.midi_note.start_time,
                    is_primary=True,  # Non-tied notes are always primary
                    tied_group_id="",  # No tied group
                    master_start_time=match.midi_note.start_time,
                    position_in_group=0,
                    timing_confidence=match.confidence
                )
                self.assignments.append(assignment)
                non_tied_count += 1
        
        if self.verbose:
            print(f"✅ Processed {non_tied_count} non-tied notes with direct MIDI timing")
            print()
    
    def _validate_assignments(self):
        """Validate and sort all timing assignments"""
        if self.verbose:
            print(f"🔍 Validating timing assignments...")
        
        # Sort by calculated start time
        self.assignments.sort(key=lambda x: x.calculated_start_time)
        
        # Validation statistics
        total_assignments = len(self.assignments)
        primary_count = sum(1 for a in self.assignments if a.is_primary)
        tied_count = total_assignments - primary_count
        avg_confidence = sum(a.timing_confidence for a in self.assignments) / total_assignments if total_assignments > 0 else 0
        
        if self.verbose:
            print(f"📊 VALIDATION RESULTS:")
            print(f"✅ Total assignments: {total_assignments}")
            print(f"🎯 Primary notes (MIDI exact): {primary_count}")
            print(f"🔗 Tied notes (calculated): {tied_count}")
            print(f"📈 Average confidence: {avg_confidence:.3f}")
            
            # Show timing range
            if self.assignments:
                start_time = self.assignments[0].calculated_start_time
                end_time = self.assignments[-1].calculated_start_time
                print(f"⏱️  Timing range: {start_time:.3f}s to {end_time:.3f}s")
            print()
    
    def _create_xml_note_key(self, note: MusicXMLNote) -> str:
        """Create unique key for XML note identification"""
        return f"{note.part_id}_{note.measure_number}_{note.beat_position:.3f}_{note.pitch}"
    
    def get_tied_groups_summary(self) -> Dict:
        """Get comprehensive summary of tied note processing"""
        tied_relationships = []
        
        for group_id, tied_group in self.tied_groups.items():
            group_summary = {
                'group_id': group_id,
                'note_count': len(tied_group.notes),
                'primary_pitch': tied_group.primary_note.pitch,
                'total_duration_beats': tied_group.total_duration,
                'has_midi_match': tied_group.matched_midi_note is not None,
                'master_start_time': tied_group.master_midi_start_time,
                'master_end_time': tied_group.master_midi_end_time,
                'notes': []
            }
            
            for note in tied_group.notes:
                note_info = {
                    'pitch': note.pitch,
                    'measure': note.measure_number,
                    'beat_position': note.beat_position,
                    'tie_type': note.tie_type,
                    'duration': note.duration
                }
                group_summary['notes'].append(note_info)
            
            tied_relationships.append(group_summary)
        
        # Assignment statistics
        assignment_stats = {
            'total_assignments': len(self.assignments),
            'primary_assignments': sum(1 for a in self.assignments if a.is_primary),
            'tied_assignments': sum(1 for a in self.assignments if not a.is_primary),
            'average_confidence': sum(a.timing_confidence for a in self.assignments) / len(self.assignments) if self.assignments else 0,
            'timing_spread_seconds': (
                max(a.calculated_start_time for a in self.assignments) - 
                min(a.calculated_start_time for a in self.assignments)
            ) if self.assignments else 0
        }
        
        return {
            'tied_groups_count': len(self.tied_groups),
            'tied_relationships': tied_relationships,
            'assignment_statistics': assignment_stats,
            'processing_summary': {
                'total_tied_groups': len(self.tied_groups),
                'matched_tied_groups': sum(1 for tg in self.tied_groups.values() if tg.matched_midi_note is not None),
                'complex_relationships': sum(1 for tg in self.tied_groups.values() if len(tg.notes) >= 3),
                'tempo_handling': 'proportional_approximation'
            }
        }
    
    def save_assignments_to_json(self, output_path: Path):
        """Save tied note assignments to JSON file for analysis"""
        output_data = {
            'processor_config': {
                'default_bpm': self.default_bpm,
                'verbose': self.verbose
            },
            'tied_groups_summary': self.get_tied_groups_summary(),
            'assignments': []
        }
        
        for assignment in self.assignments:
            assignment_dict = {
                'note': {
                    'pitch': assignment.note.pitch,
                    'measure': assignment.note.measure_number,
                    'beat_position': assignment.note.beat_position,
                    'part_id': assignment.note.part_id,
                    'tie_type': assignment.note.tie_type,
                    'onset_time_beats': assignment.note.onset_time
                },
                'timing': {
                    'calculated_start_time': assignment.calculated_start_time,
                    'master_start_time': assignment.master_start_time,
                    'is_primary': assignment.is_primary,
                    'timing_confidence': assignment.timing_confidence
                },
                'tied_info': {
                    'tied_group_id': assignment.tied_group_id,
                    'position_in_group': assignment.position_in_group,
                    'is_tied_note': bool(assignment.tied_group_id)
                }
            }
            output_data['assignments'].append(assignment_dict)
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        if self.verbose:
            print(f"💾 Tied note assignments saved to: {output_path}")
        
        return output_path
    
    def get_after_effects_timing_data(self) -> List[Dict]:
        """
        Generate After Effects compatible timing data for each notehead.
        
        Returns:
            List of timing objects ready for AE integration
        """
        ae_timing_data = []
        
        for assignment in self.assignments:
            timing_entry = {
                'notehead_id': f"{assignment.note.part_id}_{assignment.note.measure_number}_{assignment.note.pitch}",
                'start_time_seconds': assignment.calculated_start_time,
                'pitch': assignment.note.pitch,
                'measure': assignment.note.measure_number,
                'part_id': assignment.note.part_id,
                'is_primary_note': assignment.is_primary,
                'tied_group_id': assignment.tied_group_id if assignment.tied_group_id else None,
                'timing_confidence': assignment.timing_confidence,
                'timing_source': 'midi_exact' if assignment.is_primary else 'calculated_approximation'
            }
            ae_timing_data.append(timing_entry)
        
        return ae_timing_data


def main():
    """CLI interface for testing tied note processor functionality"""
    if len(sys.argv) < 4:
        print("Usage: python tied_note_processor.py <musicxml_file> <master_timing_json> <matches_json> [tempo_bpm]")
        print("Example: python tied_note_processor.py 'Base/SS 9.musicxml' timing.json matches.json 120")
        sys.exit(1)
    
    musicxml_file = sys.argv[1]
    timing_file = sys.argv[2] 
    matches_file = sys.argv[3]
    tempo_bpm = float(sys.argv[4]) if len(sys.argv) > 4 else 120.0
    
    # Validate input files
    for filepath in [musicxml_file, timing_file, matches_file]:
        if not os.path.exists(filepath):
            print(f"❌ ERROR: File not found: {filepath}")
            sys.exit(1)
    
    try:
        print(f"TIED NOTE PROCESSOR TEST")
        print("=" * 50)
        print(f"📄 MusicXML: {musicxml_file}")
        print(f"⏱️  Master timing: {timing_file}")
        print(f"🎯 Matches: {matches_file}")
        print(f"🎵 Tempo: {tempo_bpm} BPM")
        print()
        
        # Step 1: Parse XML for tied notes
        xml_parser = XMLTemporalParser(Path(musicxml_file))
        all_xml_notes = xml_parser.extract_all_notes()
        tied_groups_data = xml_parser.extract_tied_notes()
        
        print(f"✅ XML Analysis Complete:")
        print(f"   📝 Total notes: {len(all_xml_notes)}")
        print(f"   🔗 Tied groups: {len(tied_groups_data)}")
        print()
        
        # Step 2: Load MIDI timing and matches
        with open(timing_file, 'r') as f:
            master_timing = json.load(f)
        
        with open(matches_file, 'r') as f:
            matches_data = json.load(f)
        
        # Convert to NoteMatch objects (simplified for testing)
        note_matches = []
        # In real implementation, this would reconstruct NoteMatch objects
        print(f"✅ Loaded {len(matches_data.get('matches', []))} note matches")
        print()
        
        # Step 3: Process tied relationships
        processor = TiedNoteProcessor(beats_per_minute=tempo_bpm, verbose=True)
        
        # Extract tempo map from master timing
        tempo_map = master_timing.get('tempo_map', [(0.0, tempo_bpm)])
        
        assignments = processor.process_tied_relationships(
            xml_notes=all_xml_notes,
            tied_groups_data=tied_groups_data,
            note_matches=note_matches,  # Would be properly loaded in real implementation
            tempo_map=tempo_map
        )
        
        # Step 4: Generate outputs
        output_dir = Path(timing_file).parent
        assignments_file = output_dir / "tied_note_assignments.json"
        processor.save_assignments_to_json(assignments_file)
        
        # Step 5: Generate AE timing data
        ae_timing = processor.get_after_effects_timing_data()
        ae_file = output_dir / "ae_timing_data.json"
        with open(ae_file, 'w') as f:
            json.dump(ae_timing, f, indent=2)
        
        print(f"✅ After Effects timing data saved to: {ae_file}")
        
        # Final summary
        summary = processor.get_tied_groups_summary()
        print(f"\n🎯 TIED NOTE PROCESSING COMPLETE!")
        print(f"✅ Total assignments: {summary['assignment_statistics']['total_assignments']}")
        print(f"🎯 Primary (MIDI exact): {summary['assignment_statistics']['primary_assignments']}")
        print(f"🔗 Tied (calculated): {summary['assignment_statistics']['tied_assignments']}")
        print(f"📈 Average confidence: {summary['assignment_statistics']['average_confidence']:.3f}")
        print(f"⏱️  Timing spread: {summary['assignment_statistics']['timing_spread_seconds']:.3f}s")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()