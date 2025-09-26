#!/usr/bin/env python3

import os
import sys
import subprocess
import glob
from pathlib import Path
from typing import List, Dict
import json

def find_soundfont():
    """Find available soundfont files on the system."""
    
    # Common soundfont locations on macOS
    soundfont_paths = [
        "/usr/share/soundfonts/*.sf2",
        "/usr/local/share/soundfonts/*.sf2",
        "/opt/homebrew/share/soundfonts/*.sf2",
        "/System/Library/Components/CoreAudio.component/Contents/Resources/gs_instruments.dls",
        "~/Library/Audio/Sounds/Banks/*.sf2",
        "/Library/Audio/Sounds/Banks/*.sf2"
    ]
    
    # Also check for FluidSynth's default soundfont
    default_soundfonts = [
        "/usr/share/soundfonts/FluidR3_GM.sf2",
        "/usr/local/share/soundfonts/FluidR3_GM.sf2",
        "/opt/homebrew/share/soundfonts/FluidR3_GM.sf2"
    ]
    
    soundfont_paths.extend(default_soundfonts)
    
    for pattern in soundfont_paths:
        expanded_pattern = os.path.expanduser(pattern)
        matches = glob.glob(expanded_pattern)
        if matches:
            return matches[0]
    
    # If no soundfont found, try to download a basic one
    print("⚠️  No soundfont found. Attempting to use system default...")
    return None

def render_midi_to_audio(midi_file: str, output_file: str, soundfont: str = None) -> bool:
    """Render a MIDI file to audio using FluidSynth."""
    
    try:
        # Build FluidSynth command
        cmd = ["fluidsynth", "-ni"]
        
        if soundfont:
            cmd.extend([soundfont])
        else:
            # Try to use system default
            print(f"⚠️  Using system default soundfont for {os.path.basename(midi_file)}")
        
        cmd.extend([
            midi_file,
            "-F", output_file,
            "-r", "44100",  # Sample rate
            "-g", "0.5"     # Gain
        ])
        
        # Run FluidSynth
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return True
        else:
            print(f"❌ FluidSynth error for {midi_file}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout rendering {midi_file}")
        return False
    except Exception as e:
        print(f"❌ Error rendering {midi_file}: {e}")
        return False

def analyze_midi_directory(midi_dir: str) -> Dict:
    """Analyze MIDI files in directory and organize by instrument."""
    
    midi_files = glob.glob(os.path.join(midi_dir, "*.mid"))
    
    instruments = {}
    
    for midi_file in midi_files:
        filename = os.path.basename(midi_file)
        
        # Parse filename to extract instrument info
        # Expected format: note_XXX_InstrumentName_NoteInfo_velXX.mid
        parts = filename.replace('.mid', '').split('_')
        
        if len(parts) >= 3:
            instrument_name = parts[2]  # e.g., "Flûte", "Violon"
            
            if instrument_name not in instruments:
                instruments[instrument_name] = []
            
            instruments[instrument_name].append({
                'midi_file': midi_file,
                'filename': filename,
                'note_id': parts[1] if len(parts) > 1 else 'unknown',
                'note_info': '_'.join(parts[3:]) if len(parts) > 3 else 'unknown'
            })
    
    return instruments

def render_midi_collection_to_audio(midi_dir: str):
    """Render all MIDI files in directory to audio, organized by instrument."""
    
    print("MIDI TO AUDIO RENDERER")
    print("=" * 50)
    print(f"Input directory: {midi_dir}")
    print()
    
    # Check if directory exists
    if not os.path.exists(midi_dir):
        print(f"❌ ERROR: Directory not found: {midi_dir}")
        return
    
    # Find soundfont
    soundfont = find_soundfont()
    if soundfont:
        print(f"🎵 Using soundfont: {soundfont}")
    else:
        print("🎵 Using system default soundfont")
    print()
    
    # Analyze MIDI files
    instruments = analyze_midi_directory(midi_dir)
    
    if not instruments:
        print("❌ No MIDI files found in directory")
        return
    
    print(f"🎼 Found {len(instruments)} instruments:")
    for instrument, files in instruments.items():
        print(f"  {instrument}: {len(files)} notes")
    print()
    
    # Create Audio output directory in new location
    audio_base_dir = "outputs/audio"
    os.makedirs(audio_base_dir, exist_ok=True)
    
    # Render each instrument's notes
    total_rendered = 0
    total_failed = 0
    
    for instrument_name, midi_files in instruments.items():
        print(f"🎻 Rendering {instrument_name}...")
        
        # Create instrument-specific directory
        instrument_dir = os.path.join(audio_base_dir, instrument_name)
        os.makedirs(instrument_dir, exist_ok=True)
        
        instrument_rendered = 0
        instrument_failed = 0
        
        for midi_info in midi_files:
            midi_file = midi_info['midi_file']
            filename = midi_info['filename']
            
            # Generate audio filename
            audio_filename = filename.replace('.mid', '.wav')
            audio_file = os.path.join(instrument_dir, audio_filename)
            
            print(f"  🎵 Rendering: {filename} → {audio_filename}")
            
            # Render to audio
            success = render_midi_to_audio(midi_file, audio_file, soundfont)
            
            if success:
                # Check if file was actually created and has content
                if os.path.exists(audio_file) and os.path.getsize(audio_file) > 1000:  # At least 1KB
                    print(f"    ✅ Success: {os.path.getsize(audio_file)} bytes")
                    instrument_rendered += 1
                    total_rendered += 1
                else:
                    print(f"    ❌ Failed: File too small or missing")
                    instrument_failed += 1
                    total_failed += 1
            else:
                print(f"    ❌ Failed to render")
                instrument_failed += 1
                total_failed += 1
        
        print(f"  📊 {instrument_name}: {instrument_rendered} success, {instrument_failed} failed")
        print()
    
    # Summary
    print(f"🎯 RENDERING COMPLETE!")
    print(f"📁 Output directory: {audio_base_dir}")
    print(f"✅ Successfully rendered: {total_rendered} files")
    print(f"❌ Failed to render: {total_failed} files")
    print()
    
    # Show directory structure
    print("📁 Audio file structure:")
    for root, dirs, files in os.walk(audio_base_dir):
        level = root.replace(audio_base_dir, '').count(os.sep)
        indent = '  ' * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = '  ' * (level + 1)
        for file in files:
            if file.endswith('.wav'):
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                print(f"{subindent}{file} ({file_size:,} bytes)")

def main():
    if len(sys.argv) < 2:
        print("Usage: python midi_to_audio_renderer.py <midi_directory>")
        print("Example: python midi_to_audio_renderer.py 'Base/Saint-Saens Trio No 2_individual_notes'")
        sys.exit(1)
    
    midi_dir = sys.argv[1]
    
    # Check if FluidSynth is available
    try:
        result = subprocess.run(["fluidsynth", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ ERROR: FluidSynth not available")
            print("Install with: brew install fluidsynth")
            sys.exit(1)
    except FileNotFoundError:
        print("❌ ERROR: FluidSynth not found")
        print("Install with: brew install fluidsynth")
        sys.exit(1)
    
    try:
        render_midi_collection_to_audio(midi_dir)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()