#!/usr/bin/env python3

import mido
import sys
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# General MIDI Instrument Program Numbers for track-based detection
TRACK_INSTRUMENT_MAP = {
    "Flûte": 74,        # Flute
    "Violon": 41,       # Violin
    "Piano": 1,         # Acoustic Grand Piano
    "Viola": 42,        # Viola
    "Cello": 43,        # Cello
    "Contrebasse": 44,  # Contrabass
    "Clarinette": 72,   # Clarinet
    "Trompette": 57,    # Trumpet
    "Trombone": 58,     # Trombone
}

def load_universal_registry(registry_path: Optional[str]) -> Optional[Dict]:
    """Load Universal ID registry for note matching"""
    if not registry_path or not os.path.exists(registry_path):
        print(f"⚠️  Universal ID registry not found: {registry_path or 'None'}")
        print("   Proceeding with sequential ID generation")
        return None

    try:
        with open(registry_path, 'r') as f:
            registry_data = json.load(f)

        print(f"✅ Loaded Universal ID registry: {len(registry_data.get('notes', []))} notes")
        return registry_data
    except Exception as e:
        print(f"⚠️  Failed to load Universal ID registry: {e}")
        return None

def create_id_lookup_tables(registry_data: Dict) -> Dict:
    """Create lookup tables for efficient Universal ID matching"""
    if not registry_data:
        return {}

    lookup = {
        'by_pitch_and_track': {},  # (pitch_name, track_index) -> universal_id
        'by_pitch_only': {},       # pitch_name -> [universal_ids]
        'all_notes': {}            # universal_id -> note_data
    }

    for note in registry_data.get('notes', []):
        universal_id = note.get('universal_id')
        xml_data = note.get('xml_data', {})
        midi_data = note.get('midi_data')

        if not universal_id or not midi_data:
            continue

        # Store complete note data
        lookup['all_notes'][universal_id] = note

        # Create pitch-based lookups
        pitch_name = xml_data.get('note_name')  # e.g., "A4"
        track_index = midi_data.get('track_index', 0)

        if pitch_name:
            # Pitch + track lookup (most specific)
            key = (pitch_name, track_index)
            if key not in lookup['by_pitch_and_track']:
                lookup['by_pitch_and_track'][key] = []
            lookup['by_pitch_and_track'][key].append(universal_id)

            # Pitch-only lookup (fallback)
            if pitch_name not in lookup['by_pitch_only']:
                lookup['by_pitch_only'][pitch_name] = []
            lookup['by_pitch_only'][pitch_name].append(universal_id)

    return lookup

def find_universal_id_for_note(note_info: Dict, lookup: Dict, used_ids: set) -> Tuple[Optional[str], float]:
    """Find best matching Universal ID for a MIDI note"""
    if not lookup:
        return None, 0.0

    pitch_name = note_info['note_name']
    track_index = note_info['track']

    # Strategy 1: Exact pitch + track match
    key = (pitch_name, track_index)
    candidates = lookup.get('by_pitch_and_track', {}).get(key, [])

    for universal_id in candidates:
        if universal_id not in used_ids:
            used_ids.add(universal_id)
            return universal_id, 0.95  # High confidence for exact match

    # Strategy 2: Pitch-only match (different track)
    candidates = lookup.get('by_pitch_only', {}).get(pitch_name, [])

    for universal_id in candidates:
        if universal_id not in used_ids:
            used_ids.add(universal_id)
            return universal_id, 0.75  # Medium confidence for pitch-only match

    # No match found
    return None, 0.0

def analyze_midi_structure(midi_file: str, registry_data: Optional[Dict] = None) -> Dict:
    """Analyze MIDI file structure and extract note information."""
    print(f"MIDI NOTE SEPARATOR")
    print("=" * 50)
    print(f"Input MIDI: {midi_file}")

    # Initialize Universal ID system
    lookup = {}
    used_universal_ids = set()

    if registry_data:
        print(f"🔗 Universal ID Mode: Registry-based matching")
        lookup = create_id_lookup_tables(registry_data)
        print(f"   Lookup tables: {len(lookup.get('by_pitch_and_track', {}))} pitch+track, {len(lookup.get('by_pitch_only', {}))} pitch-only")
    else:
        print(f"🔢 Sequential ID Mode: Registry not available")

    print()

    # Load MIDI file
    mid = mido.MidiFile(midi_file)

    # Extract basic info
    print(f"🎵 MIDI Type: {mid.type}")
    print(f"⏱️  Ticks per beat: {mid.ticks_per_beat}")
    print(f"🎼 Number of tracks: {len(mid.tracks)}")
    print()

    # Analyze each track
    all_notes = []
    note_id = 0
    
    for track_idx, track in enumerate(mid.tracks):
        print(f"Track {track_idx}: {track.name or 'Unnamed'}")
        track_notes = []
        active_notes = {}  # note -> (start_time, velocity)
        current_time = 0
        
        for msg in track:
            current_time += msg.time
            
            if msg.type == 'note_on' and msg.velocity > 0:
                # Note starts
                active_notes[msg.note] = (current_time, msg.velocity)
                
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                # Note ends
                if msg.note in active_notes:
                    start_time, velocity = active_notes[msg.note]
                    duration = current_time - start_time
                    
                    note_info = {
                        'id': note_id,
                        'track': track_idx,
                        'track_name': track.name or f'Track_{track_idx}',
                        'note': msg.note,
                        'note_name': note_to_name(msg.note),
                        'velocity': velocity,
                        'start_ticks': start_time,
                        'end_ticks': current_time,
                        'duration_ticks': duration,
                        'channel': msg.channel
                    }

                    # Try to find Universal ID for this note
                    universal_id, confidence = find_universal_id_for_note(note_info, lookup, used_universal_ids)
                    note_info['universal_id'] = universal_id
                    note_info['match_confidence'] = confidence
                    
                    track_notes.append(note_info)
                    all_notes.append(note_info)
                    note_id += 1
                    
                    del active_notes[msg.note]
        
        print(f"  Notes found: {len(track_notes)}")
        
        # Show note summary for this track
        if track_notes:
            notes_by_pitch = {}
            for note in track_notes:
                pitch = note['note_name']
                if pitch not in notes_by_pitch:
                    notes_by_pitch[pitch] = 0
                notes_by_pitch[pitch] += 1
            
            print(f"  Pitch distribution: {dict(sorted(notes_by_pitch.items()))}")
        print()
    
    print(f"🎯 TOTAL NOTES: {len(all_notes)}")
    
    return {
        'midi_file': mid,
        'notes': all_notes,
        'ticks_per_beat': mid.ticks_per_beat,
        'type': mid.type
    }

def note_to_name(note_number: int) -> str:
    """Convert MIDI note number to note name."""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = note_number // 12 - 1
    note = notes[note_number % 12]
    return f"{note}{octave}"

def get_instrument_program_from_track(track_name):
    """Get General MIDI program number from track name."""
    # Clean track name and look for instrument match
    clean_track_name = track_name.replace(' ', '_').replace('/', '_')

    # Direct match
    if clean_track_name in TRACK_INSTRUMENT_MAP:
        return TRACK_INSTRUMENT_MAP[clean_track_name]

    # Partial match
    for instrument, program in TRACK_INSTRUMENT_MAP.items():
        if instrument.lower() in clean_track_name.lower():
            return program

    return 1  # Default to Piano

def create_single_note_midi(original_midi: mido.MidiFile, note_info: Dict, output_file: str):
    """Create a MIDI file containing only one specific note."""
    
    # Create new MIDI file with same settings
    new_mid = mido.MidiFile(type=original_midi.type, ticks_per_beat=original_midi.ticks_per_beat)

    # Create a new track for this note
    track = mido.MidiTrack()

    # Add track name
    track.append(mido.MetaMessage('track_name', name=f"Note_{note_info['id']}_{note_info['note_name']}", time=0))

    # Set tempo (copy from original if available)
    for original_track in original_midi.tracks:
        for msg in original_track:
            if msg.type == 'set_tempo':
                track.append(msg.copy(time=0))
                break
        else:
            continue
        break
    else:
        # Default tempo if none found
        track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))  # 120 BPM

    # Add program change for instrument-specific sound
    program_number = get_instrument_program_from_track(note_info['track_name'])
    track.append(mido.Message('program_change',
                             channel=note_info['channel'],
                             program=program_number - 1,  # MIDI uses 0-based: Flute=73, Violin=40
                             time=0))
    
    # Add the note on event at time 0 (remove leading silence)
    track.append(mido.Message('note_on',
                             channel=note_info['channel'],
                             note=note_info['note'],
                             velocity=note_info['velocity'],
                             time=0))

    # Add the note off event after the note duration
    track.append(mido.Message('note_off',
                             channel=note_info['channel'],
                             note=note_info['note'],
                             velocity=0,
                             time=note_info['duration_ticks']))
    
    # End of track
    track.append(mido.MetaMessage('end_of_track', time=0))
    
    new_mid.tracks.append(track)
    
    # Save the file
    new_mid.save(output_file)

def separate_midi_notes(midi_file: str, registry_path: Optional[str] = None):
    """Separate MIDI file into individual note files."""

    # Load Universal ID registry if provided
    registry_data = load_universal_registry(registry_path)

    # Analyze MIDI structure with Universal ID integration
    analysis = analyze_midi_structure(midi_file, registry_data)
    
    # Create base output directory
    base_name = Path(midi_file).stem
    base_output_dir = "outputs/midi"
    os.makedirs(base_output_dir, exist_ok=True)

    print(f"\n📁 Creating individual note files in: {base_output_dir}")
    print()

    # Create individual MIDI files for each note
    for note in analysis['notes']:
        # Generate filename and instrument directory
        track_name = note['track_name'].replace(' ', '_').replace('/', '_')
        instrument_dir = os.path.join(base_output_dir, track_name)
        os.makedirs(instrument_dir, exist_ok=True)

        # Generate filename with Universal ID suffix if available
        base_filename = f"note_{note['id']:03d}_{track_name}_{note['note_name']}_vel{note['velocity']}"

        if note.get('universal_id'):
            # Add 4-character UUID suffix for Universal ID preservation
            uuid_suffix = note['universal_id'][:4]
            filename = f"{base_filename}_{uuid_suffix}.mid"
        else:
            # Fallback to standard naming without Universal ID
            filename = f"{base_filename}.mid"

        output_file = os.path.join(instrument_dir, filename)
        
        # Create single-note MIDI file
        create_single_note_midi(analysis['midi_file'], note, output_file)

        # Get program change info for output
        program_number = get_instrument_program_from_track(note['track_name'])

        print(f"✅ Created: {filename}")
        print(f"   Track: {note['track_name']} → GM Program #{program_number}")
        print(f"   Note: {note['note_name']} (MIDI {note['note']})")
        print(f"   Velocity: {note['velocity']}")
        print(f"   Duration: {note['duration_ticks']} ticks")
        print(f"   Start: {note['start_ticks']} ticks")

        # Show Universal ID information if available
        if note.get('universal_id'):
            confidence = note.get('match_confidence', 0.0)
            print(f"   🔗 Universal ID: {note['universal_id'][:8]}... (confidence: {confidence:.1%})")
        else:
            print(f"   🔢 Sequential ID: {note['id']:03d} (no Universal ID match)")

        print()
    
    print(f"🎯 SUCCESS! Created {len(analysis['notes'])} individual note files")
    print(f"📁 Output directory: {base_output_dir}")
    
    # Summary by track
    track_summary = {}
    for note in analysis['notes']:
        track_name = note['track_name']
        if track_name not in track_summary:
            track_summary[track_name] = 0
        track_summary[track_name] += 1
    
    print(f"\nSUMMARY BY TRACK:")
    for track_name, count in track_summary.items():
        print(f"  {track_name}: {count} notes")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="MIDI Note Separator with Universal ID Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (sequential IDs)
  python midi_note_separator.py "Base/Saint-Saens Trio No 2.mid"

  # With Universal ID registry (preserves note relationships)
  python midi_note_separator.py "Base/Saint-Saens Trio No 2.mid" --registry "universal_output/universal_notes_registry.json"
        """
    )

    parser.add_argument("midi_file", help="Path to MIDI file")
    parser.add_argument("--registry", help="Path to Universal ID registry JSON file (optional)")

    args = parser.parse_args()

    if not os.path.exists(args.midi_file):
        print(f"❌ ERROR: MIDI file not found: {args.midi_file}")
        sys.exit(1)

    try:
        separate_midi_notes(args.midi_file, args.registry)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()