#!/usr/bin/env python3

import mido
import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple

def analyze_midi_structure(midi_file: str) -> Dict:
    """Analyze MIDI file structure and extract note information."""
    print(f"MIDI NOTE SEPARATOR")
    print("=" * 50)
    print(f"Input MIDI: {midi_file}")
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

def separate_midi_notes(midi_file: str):
    """Separate MIDI file into individual note files."""
    
    # Analyze MIDI structure
    analysis = analyze_midi_structure(midi_file)
    
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

        filename = f"note_{note['id']:03d}_{track_name}_{note['note_name']}_vel{note['velocity']}.mid"
        output_file = os.path.join(instrument_dir, filename)
        
        # Create single-note MIDI file
        create_single_note_midi(analysis['midi_file'], note, output_file)
        
        print(f"✅ Created: {filename}")
        print(f"   Track: {note['track_name']}")
        print(f"   Note: {note['note_name']} (MIDI {note['note']})")
        print(f"   Velocity: {note['velocity']}")
        print(f"   Duration: {note['duration_ticks']} ticks")
        print(f"   Start: {note['start_ticks']} ticks")
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
    if len(sys.argv) < 2:
        print("Usage: python midi_note_separator.py <midi_file>")
        print("Example: python midi_note_separator.py 'Base/Saint-Saens Trio No 2.mid'")
        sys.exit(1)
    
    midi_file = sys.argv[1]
    
    if not os.path.exists(midi_file):
        print(f"❌ ERROR: MIDI file not found: {midi_file}")
        sys.exit(1)
    
    try:
        separate_midi_notes(midi_file)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()