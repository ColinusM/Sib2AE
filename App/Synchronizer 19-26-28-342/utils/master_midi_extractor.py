#!/usr/bin/env python3
"""
Master MIDI Timing Extractor

This module extracts timing data from the original master MIDI file BEFORE any note separation.
It preserves original timing relationships as the authoritative reference for synchronization.

Critical Features:
- Extract timing from master MIDI before any processing
- Preserve tempo map and all timing relationships
- Create MasterMIDITiming dataclass as authoritative reference
- Handle tempo changes mid-piece with tempo map tracking
- Support both tick-based and seconds-based timing
"""

import mido
import sys
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
import json


@dataclass
class MasterMIDITiming:
    """Timing data extracted from original master MIDI before note separation"""
    master_midi_path: Path          # Original MIDI file path
    tempo_map: List[Tuple[float, float]]  # (time_seconds, bpm) pairs
    total_duration_seconds: float   # Total piece duration
    ppq: int                       # Pulses per quarter note (ticks_per_beat)
    note_events: List[Dict]        # All note events with original timing
    track_info: List[Dict]         # Track metadata and instrument information
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['master_midi_path'] = str(self.master_midi_path)
        return result
    
    def save_to_json(self, output_path: Path):
        """Save master timing data to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"✅ Master timing data saved to: {output_path}")


class MasterMIDIExtractor:
    """
    Extracts comprehensive timing data from the original master MIDI file.
    
    This extractor processes the master MIDI file BEFORE any note separation
    to preserve original timing relationships as the authoritative reference.
    """
    
    def __init__(self, master_midi_path: Path):
        """Initialize with path to master MIDI file"""
        self.master_midi_path = Path(master_midi_path)
        if not self.master_midi_path.exists():
            raise FileNotFoundError(f"Master MIDI file not found: {master_midi_path}")
        
        self.master_midi = mido.MidiFile(str(self.master_midi_path))
        self.master_timing = None
        
    def extract_master_timing(self) -> MasterMIDITiming:
        """
        Extract comprehensive timing data from master MIDI file.
        
        Returns:
            MasterMIDITiming object with complete timing information
        """
        print(f"MASTER MIDI TIMING EXTRACTOR")
        print("=" * 50)
        print(f"🎵 Processing: {self.master_midi_path.name}")
        print(f"📊 Type: {self.master_midi.type}")
        print(f"⏱️  Ticks per beat (PPQ): {self.master_midi.ticks_per_beat}")
        print(f"🎼 Tracks: {len(self.master_midi.tracks)}")
        print()
        
        # Initialize timing tracking
        tempo_map = []
        note_events = []
        track_info = []
        current_time_seconds = 0.0
        current_tempo = 500000  # Default 120 BPM (microseconds per beat)
        
        # Process each track for comprehensive analysis
        for track_idx, track in enumerate(self.master_midi.tracks):
            track_data = self._analyze_track(track_idx, track)
            track_info.append(track_data)
            
            # Reset timing for this track
            track_time_ticks = 0
            track_time_seconds = 0.0
            track_tempo = 500000
            active_notes = {}  # note -> (start_time_seconds, velocity, start_ticks)
            
            print(f"Track {track_idx}: {track_data['name']}")
            
            # Process all messages in track
            for msg in track:
                # Update time tracking
                track_time_ticks += msg.time
                track_time_seconds += mido.tick2second(
                    msg.time, 
                    self.master_midi.ticks_per_beat, 
                    track_tempo
                )
                
                # Handle tempo changes
                if msg.type == 'set_tempo':
                    old_bpm = 60000000 / track_tempo
                    new_bpm = 60000000 / msg.tempo
                    tempo_map.append((track_time_seconds, new_bpm))
                    track_tempo = msg.tempo
                    print(f"  ⏱️  Tempo change at {track_time_seconds:.3f}s: {old_bpm:.1f} → {new_bpm:.1f} BPM")
                
                # Handle note events
                elif msg.type == 'note_on' and msg.velocity > 0:
                    # Note starts
                    active_notes[msg.note] = (track_time_seconds, msg.velocity, track_time_ticks)
                    
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    # Note ends
                    if msg.note in active_notes:
                        start_time_seconds, velocity, start_ticks = active_notes[msg.note]
                        duration_seconds = track_time_seconds - start_time_seconds
                        duration_ticks = track_time_ticks - start_ticks
                        
                        note_event = {
                            'track_index': track_idx,
                            'track_name': track_data['name'],
                            'pitch_midi': msg.note,
                            'pitch_name': self._midi_to_note_name(msg.note),
                            'velocity': velocity,
                            'start_time_seconds': start_time_seconds,
                            'end_time_seconds': track_time_seconds,
                            'duration_seconds': duration_seconds,
                            'start_time_ticks': start_ticks,
                            'end_time_ticks': track_time_ticks,
                            'duration_ticks': duration_ticks,
                            'channel': msg.channel,
                            'instrument': track_data['instrument']
                        }
                        
                        note_events.append(note_event)
                        del active_notes[msg.note]
                
                # Update global time tracking for overall duration
                current_time_seconds = max(current_time_seconds, track_time_seconds)
            
            print(f"  🎵 Notes: {len([n for n in note_events if n['track_index'] == track_idx])}")
            print(f"  🎶 Duration: {track_time_seconds:.3f}s")
            print()
        
        # Sort note events by start time for chronological order
        note_events.sort(key=lambda x: x['start_time_seconds'])
        
        # Add default tempo if none found
        if not tempo_map:
            default_bpm = 60000000 / current_tempo
            tempo_map.append((0.0, default_bpm))
            print(f"⚠️  No tempo changes found, using default: {default_bpm:.1f} BPM")
        
        # Create master timing object
        self.master_timing = MasterMIDITiming(
            master_midi_path=self.master_midi_path,
            tempo_map=tempo_map,
            total_duration_seconds=current_time_seconds,
            ppq=self.master_midi.ticks_per_beat,
            note_events=note_events,
            track_info=track_info
        )
        
        # Summary
        print(f"📊 MASTER TIMING EXTRACTION COMPLETE")
        print(f"🎯 Total notes: {len(note_events)}")
        print(f"⏱️  Total duration: {current_time_seconds:.3f} seconds")
        print(f"🎵 Tempo changes: {len(tempo_map)}")
        print(f"🎼 Tracks processed: {len(track_info)}")
        print()
        
        return self.master_timing
    
    def _analyze_track(self, track_idx: int, track: mido.MidiTrack) -> Dict:
        """Analyze individual track for metadata and instrument information"""
        track_name = getattr(track, 'name', f'Track_{track_idx}')
        
        # Extract track name from meta messages
        for msg in track:
            if msg.type == 'track_name':
                track_name = msg.name
                break
        
        # Determine instrument type based on track name and content
        instrument = self._determine_instrument(track_name, track)
        
        # Count messages by type
        message_types = {}
        for msg in track:
            msg_type = msg.type
            if msg_type not in message_types:
                message_types[msg_type] = 0
            message_types[msg_type] += 1
        
        return {
            'index': track_idx,
            'name': track_name,
            'instrument': instrument,
            'message_count': len(track),
            'message_types': message_types
        }
    
    def _determine_instrument(self, track_name: str, track: mido.MidiTrack) -> str:
        """Determine instrument type from track name and MIDI data"""
        track_name_lower = track_name.lower()
        
        # Common instrument name mappings
        instrument_keywords = {
            'flute': 'Flute',
            'flûte': 'Flute',
            'violin': 'Violin',
            'violon': 'Violin',
            'piano': 'Piano',
            'cello': 'Cello',
            'viola': 'Viola',
            'oboe': 'Oboe',
            'clarinet': 'Clarinet',
            'horn': 'Horn',
            'trumpet': 'Trumpet',
            'trombone': 'Trombone',
            'percussion': 'Percussion',
            'drums': 'Drums'
        }
        
        # Check track name for instrument keywords
        for keyword, instrument in instrument_keywords.items():
            if keyword in track_name_lower:
                return instrument
        
        # Default to track name if no specific instrument found
        if track_name and track_name != f'Track_{track_name}':
            return track_name
        
        return 'Unknown'
    
    def _midi_to_note_name(self, note_number: int) -> str:
        """Convert MIDI note number to note name (e.g., 60 -> C4)"""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = note_number // 12 - 1
        note = notes[note_number % 12]
        return f"{note}{octave}"
    
    def get_tempo_at_time(self, time_seconds: float) -> float:
        """Get the BPM tempo at a specific time in seconds"""
        if not self.master_timing or not self.master_timing.tempo_map:
            return 120.0  # Default BPM
        
        # Find the most recent tempo change before or at the given time
        current_tempo = self.master_timing.tempo_map[0][1]  # Default to first tempo
        
        for tempo_time, tempo_bpm in self.master_timing.tempo_map:
            if tempo_time <= time_seconds:
                current_tempo = tempo_bpm
            else:
                break
        
        return current_tempo
    
    def save_master_timing(self, output_path: Optional[Path] = None):
        """Save master timing data to JSON file"""
        if not self.master_timing:
            raise ValueError("Master timing not extracted yet. Call extract_master_timing() first.")
        
        if output_path is None:
            output_path = self.master_midi_path.parent / f"{self.master_midi_path.stem}_master_timing.json"
        
        self.master_timing.save_to_json(output_path)
        return output_path


def main():
    """CLI interface for master MIDI timing extraction"""
    if len(sys.argv) < 2:
        print("Usage: python master_midi_extractor.py <master_midi_file> [output_json]")
        print("Example: python master_midi_extractor.py 'Base/Saint-Saens Trio No 2.mid'")
        print("         python master_midi_extractor.py 'Base/Saint-Saens Trio No 2.mid' 'timing.json'")
        sys.exit(1)
    
    midi_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(midi_file):
        print(f"❌ ERROR: MIDI file not found: {midi_file}")
        sys.exit(1)
    
    try:
        # Extract master timing
        extractor = MasterMIDIExtractor(Path(midi_file))
        master_timing = extractor.extract_master_timing()
        
        # Save to JSON
        output_path = Path(output_file) if output_file else None
        saved_path = extractor.save_master_timing(output_path)
        
        print(f"🎯 SUCCESS! Master timing extracted and saved")
        print(f"📁 Output file: {saved_path}")
        print()
        
        # Display summary
        print("MASTER TIMING SUMMARY:")
        print("-" * 30)
        print(f"📊 Source: {master_timing.master_midi_path.name}")
        print(f"⏱️  Duration: {master_timing.total_duration_seconds:.3f} seconds")
        print(f"🎵 Total notes: {len(master_timing.note_events)}")
        print(f"🎼 Tracks: {len(master_timing.track_info)}")
        print(f"⚡ PPQ: {master_timing.ppq}")
        print(f"🎶 Tempo changes: {len(master_timing.tempo_map)}")
        
        # Show tempo map
        if master_timing.tempo_map:
            print("\nTEMPO MAP:")
            for time_sec, bpm in master_timing.tempo_map:
                print(f"  {time_sec:6.3f}s: {bpm:6.1f} BPM")
        
        # Show track summary
        print("\nTRACK SUMMARY:")
        for track in master_timing.track_info:
            note_count = len([n for n in master_timing.note_events if n['track_index'] == track['index']])
            print(f"  Track {track['index']}: {track['name']} ({track['instrument']}) - {note_count} notes")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()