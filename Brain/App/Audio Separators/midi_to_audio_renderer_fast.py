#!/usr/bin/env python3

import os
import sys
import subprocess
import glob
import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional
import json
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

# Import Universal ID registry utilities
sys.path.append(str(Path(__file__).parent.parent.parent / "orchestrator"))
from registry_utils import create_registry_for_script, UniversalIDRegistry, get_universal_id_with_fallback

# General MIDI Instrument Program Numbers
INSTRUMENT_PROGRAM_MAP = {
    "Flûte": 74,        # Flute
    "Violon": 41,       # Violin
    "Piano": 1,         # Acoustic Grand Piano
    "Viola": 42,        # Viola
    "Cello": 43,        # Cello
    "Contrebasse": 44,  # Contrabass
    "Clarinette": 72,   # Clarinet
    "Trompette": 57,    # Trumpet
    "Trombone": 58,     # Trombone
    "Cor": 61,          # French Horn
    "Tuba": 59,         # Tuba
    "Piccolo": 73,      # Piccolo
    "Hautbois": 69,     # Oboe
    "Basson": 71,       # Bassoon
    "Saxophone": 65,    # Soprano Sax (default)
    "Harpe": 47,        # Orchestral Harp
    "Timpani": 48,      # Timpani
}

def find_soundfont():
    """Find available soundfont files on the system."""

    # Priority order: working soundfonts first (largest to smallest)
    soundfont_paths = [
        # High-quality 247MB SGM soundfont (highest priority)
        "soundfonts/SGM_V2_final.sf2",
        # Working soundfont from homebrew
        "/opt/homebrew/Cellar/fluid-synth/2.4.8/share/fluid-synth/sf2/VintageDreamsWaves-v2.sf2",
        # Local project soundfonts (if downloaded)
        "SGM_V2_complete.sf2",
        "archive_soundfont.sf2",
        # System locations
        "/usr/share/soundfonts/*.sf2",
        "/usr/local/share/soundfonts/*.sf2",
        "/opt/homebrew/share/soundfonts/*.sf2",
        "~/Library/Audio/Sounds/Banks/*.sf2",
        "/Library/Audio/Sounds/Banks/*.sf2"
    ]

    # Also check for FluidSynth's default soundfont
    default_soundfonts = [
        "/opt/homebrew/Cellar/fluid-synth/2.4.8/share/fluid-synth/sf2/VintageDreamsWaves-v2.sf2",
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

def extract_universal_id_from_filename(filename: str) -> Optional[str]:
    """Extract Universal ID suffix from filename if present"""
    # Pattern: name_XXXX.ext where XXXX is 4-character UUID suffix
    basename = os.path.basename(filename)
    match = re.search(r'_([a-f0-9]{4})\.\w+$', basename)
    return match.group(1) if match else None

def extract_instrument_from_filename(filename):
    """Extract instrument name from MIDI filename."""
    # Example: "note_001_Flûte_G4_vel76.mid" or "note_001_Flûte_G4_vel76_2584.mid"
    basename = os.path.basename(filename)

    # Remove extension first
    name_without_ext = basename.replace('.mid', '').replace('.wav', '')

    # Remove Universal ID suffix if present (4-char hex at end)
    name_without_id = re.sub(r'_[a-f0-9]{4}$', '', name_without_ext)

    parts = name_without_id.split('_')

    if len(parts) >= 3:
        instrument = parts[2]  # "Flûte"
        return instrument
    return "Piano"  # Default fallback

def get_instrument_program(instrument_name):
    """Get General MIDI program number for instrument."""
    return INSTRUMENT_PROGRAM_MAP.get(instrument_name, 1)  # Default to Piano

def render_single_midi(args):
    """Render a single MIDI file to audio (for parallel processing)."""
    midi_file, output_file, soundfont = args

    try:
        # Extract instrument for logging (program change will be added to MIDI in future)
        instrument_name = extract_instrument_from_filename(midi_file)
        program_number = get_instrument_program(instrument_name)

        # Build optimized FluidSynth command for speed
        cmd = ["fluidsynth",
               "-ni"]           # No interactive mode, quiet

        if soundfont:
            cmd.append(soundfont)

        cmd.extend([
            midi_file,
            "-F", output_file,
            "-r", "22050",      # Lower sample rate (22kHz vs 44kHz) = 2x faster
            "-g", "0.5"         # Increased gain for instrument clarity
        ])
        
        # Run FluidSynth with optimized settings
        result = subprocess.run(cmd,
                              capture_output=True,
                              text=True,
                              timeout=10)  # Shorter timeout

        if result.returncode == 0:
            # Verify file was created with minimum size
            if os.path.exists(output_file) and os.path.getsize(output_file) > 500:
                file_size = os.path.getsize(output_file)

                # Check for Universal ID preservation
                universal_id = extract_universal_id_from_filename(output_file)
                id_info = f" [UUID:{universal_id}]" if universal_id else " [Sequential]"

                return (True, midi_file, f"{file_size} bytes ({instrument_name} GM{program_number}){id_info}")
            else:
                return (False, midi_file, "File too small or missing")
        else:
            return (False, midi_file, result.stderr)

    except subprocess.TimeoutExpired:
        return (False, midi_file, "Timeout")
    except Exception as e:
        return (False, midi_file, str(e))

def analyze_midi_directory_fast(midi_dir: str, registry: Optional[UniversalIDRegistry] = None) -> Dict:
    """Quickly analyze MIDI files in directory and organize by instrument."""

    # Search for MIDI files recursively in subdirectories
    midi_files = glob.glob(os.path.join(midi_dir, "**", "*.mid"), recursive=True)
    instruments = {}
    
    for midi_file in midi_files:
        filename = os.path.basename(midi_file)
        
        # Parse filename to extract instrument info
        parts = filename.replace('.mid', '').split('_')
        
        if len(parts) >= 3:
            # Get Universal ID using registry if available, otherwise extract from filename
            if registry and registry.total_entries > 0:
                # Use registry lookup for robust Universal ID retrieval
                match = get_universal_id_with_fallback(
                    registry,
                    lambda: registry.get_universal_id_from_filename(filename),
                    filename
                )
                universal_id = match.universal_id
                registry_source = match.match_method
            else:
                # Fallback to filename extraction
                universal_id = extract_universal_id_from_filename(filename)
                registry_source = "filename_extraction"

            # Get instrument name (handles both new and old filename patterns)
            instrument_name = extract_instrument_from_filename(filename)

            if instrument_name not in instruments:
                instruments[instrument_name] = []

            instruments[instrument_name].append({
                'midi_file': midi_file,
                'filename': filename,
                'note_id': parts[1] if len(parts) > 1 else 'unknown',
                'note_info': '_'.join(parts[3:]) if len(parts) > 3 else 'unknown',
                'universal_id': universal_id,  # Preserve Universal ID for audio file naming
                'registry_source': registry_source  # Track data source for validation
            })
    
    return instruments

def render_midi_collection_to_audio_fast(midi_dir: str, registry: Optional[UniversalIDRegistry] = None):
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
    instruments = analyze_midi_directory_fast(midi_dir, registry)
    
    if not instruments:
        print("❌ No MIDI files found in directory")
        return
    
    total_files = sum(len(files) for files in instruments.values())
    print(f"🎼 Found {len(instruments)} instruments, {total_files} files total:")
    for instrument, files in instruments.items():
        program = get_instrument_program(instrument)
        print(f"  {instrument}: {len(files)} notes → GM Program #{program}")
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

            # Generate audio filename (preserves Universal ID if present)
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
                print(f"{subindent}{file} ({file_size} bytes)")

def main():
    parser = argparse.ArgumentParser(
        description="Fast MIDI to Audio Renderer with Universal ID preservation"
    )
    parser.add_argument(
        "midi_directory",
        help="Directory containing MIDI files to render"
    )
    parser.add_argument(
        "--registry",
        help="Path to Universal ID registry JSON file",
        default=None
    )
    args = parser.parse_args()

    midi_dir = args.midi_directory
    registry_path = args.registry
    
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
    
    # Create registry instance
    registry = create_registry_for_script(registry_path, "midi_to_audio_renderer_fast")

    try:
        render_midi_collection_to_audio_fast(midi_dir, registry)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()