#!/usr/bin/env python3

import os
import sys
import subprocess
import glob
from pathlib import Path
from typing import List, Dict
import json
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

def find_soundfont():
    """Find available soundfont files on the system."""

    # Priority order: local project soundfont first, then system locations
    soundfont_paths = [
        # Local project soundfont (highest priority)
        "FluidR3_GM.sf2",
        "soundfonts/FluidR3_GM.sf2",
        # System locations
        "/usr/share/soundfonts/*.sf2",
        "/usr/local/share/soundfonts/*.sf2",
        "/opt/homebrew/share/soundfonts/*.sf2",
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
    
    return None

def render_single_midi(args):
    """Render a single MIDI file to audio (for parallel processing)."""
    midi_file, output_file, soundfont = args
    
    try:
        # Build optimized FluidSynth command for speed
        cmd = ["fluidsynth", 
               "-ni"]           # No interactive mode, quiet
        
        if soundfont:
            cmd.append(soundfont)
        
        cmd.extend([
            midi_file,
            "-F", output_file,
            "-r", "22050",      # Lower sample rate (22kHz vs 44kHz) = 2x faster
            "-g", "0.3"         # Lower gain to prevent clipping
        ])
        
        # Run FluidSynth with optimized settings
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True, 
                              timeout=10)  # Shorter timeout
        
        if result.returncode == 0:
            # Verify file was created with minimum size
            if os.path.exists(output_file) and os.path.getsize(output_file) > 500:
                return (True, midi_file, os.path.getsize(output_file))
            else:
                return (False, midi_file, "File too small or missing")
        else:
            return (False, midi_file, result.stderr)
            
    except subprocess.TimeoutExpired:
        return (False, midi_file, "Timeout")
    except Exception as e:
        return (False, midi_file, str(e))

def analyze_midi_directory_fast(midi_dir: str) -> Dict:
    """Quickly analyze MIDI files in directory and organize by instrument."""

    # Search for MIDI files recursively in subdirectories
    midi_files = glob.glob(os.path.join(midi_dir, "**", "*.mid"), recursive=True)
    instruments = {}
    
    for midi_file in midi_files:
        filename = os.path.basename(midi_file)
        
        # Parse filename to extract instrument info
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

def render_midi_collection_to_audio_fast(midi_dir: str):
    """Render all MIDI files to audio using parallel processing for speed."""
    
    print("FAST MIDI TO AUDIO RENDERER")
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
    instruments = analyze_midi_directory_fast(midi_dir)
    
    if not instruments:
        print("❌ No MIDI files found in directory")
        return
    
    total_files = sum(len(files) for files in instruments.values())
    print(f"🎼 Found {len(instruments)} instruments, {total_files} files total:")
    for instrument, files in instruments.items():
        print(f"  {instrument}: {len(files)} notes")
    print()
    
    # Create Audio output directory in new location
    audio_base_dir = "outputs/audio"
    os.makedirs(audio_base_dir, exist_ok=True)
    
    # Prepare all rendering tasks
    render_tasks = []
    
    for instrument_name, midi_files in instruments.items():
        # Create instrument-specific directory
        instrument_dir = os.path.join(audio_base_dir, instrument_name)
        os.makedirs(instrument_dir, exist_ok=True)
        
        for midi_info in midi_files:
            midi_file = midi_info['midi_file']
            filename = midi_info['filename']
            
            # Generate audio filename
            audio_filename = filename.replace('.mid', '.wav')
            audio_file = os.path.join(instrument_dir, audio_filename)
            
            render_tasks.append((midi_file, audio_file, soundfont))
    
    # Use parallel processing for much faster rendering
    cpu_count = mp.cpu_count()
    max_workers = min(cpu_count, len(render_tasks))  # Don't over-parallelize
    
    print(f"⚡ Using {max_workers} parallel workers for fast processing...")
    print()
    
    total_rendered = 0
    total_failed = 0
    
    # Process files in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_task = {executor.submit(render_single_midi, task): task for task in render_tasks}
        
        # Process results as they complete
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            midi_file, audio_file, soundfont = task
            
            try:
                success, processed_file, result = future.result()
                filename = os.path.basename(processed_file)
                
                if success:
                    print(f"✅ {filename} → {result:,} bytes")
                    total_rendered += 1
                else:
                    print(f"❌ {filename} → {result}")
                    total_failed += 1
                    
            except Exception as e:
                print(f"❌ {os.path.basename(midi_file)} → Exception: {e}")
                total_failed += 1
    
    print()
    print(f"🎯 FAST RENDERING COMPLETE!")
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
        print("Usage: python midi_to_audio_renderer_fast.py <midi_directory>")
        print("Example: python midi_to_audio_renderer_fast.py 'Base/Saint-Saens Trio No 2_individual_notes'")
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
        render_midi_collection_to_audio_fast(midi_dir)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()