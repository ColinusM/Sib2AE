#!/usr/bin/env python3

import librosa
import numpy as np
import os
import sys
import json
import glob
from pathlib import Path
from typing import Dict, List, Tuple
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

def analyze_audio_features_fast(audio_file: str, sr: int = 22050) -> Dict:
    """Extract audio features optimized for speed."""
    
    print(f"🔊 Analyzing: {os.path.basename(audio_file)}")
    
    # Load audio with lower sample rate and shorter duration for speed
    y, sr = librosa.load(audio_file, sr=sr, duration=10.0)  # Max 10 seconds
    duration = len(y) / sr
    
    print(f"   Duration: {duration:.3f}s, Sample Rate: {sr}Hz")
    
    # Use larger hop length for fewer frames = faster processing
    hop_length = 1024  # Doubled from 512
    frame_length = 2048
    
    # 1. Core features only (skip expensive ones)
    # RMS energy for amplitude
    rms = librosa.feature.rms(y=y, hop_length=hop_length, frame_length=frame_length)[0]
    
    # Spectral centroid (brightness) - fast
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
    
    # Zero crossing rate - very fast
    zcr = librosa.feature.zero_crossing_rate(y, hop_length=hop_length)[0]
    
    # Skip expensive pitch detection and use simpler approach
    # Use spectral centroid as pitch proxy
    pitch_proxy = spectral_centroid.copy()
    
    # Simplified onset detection
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=hop_length, units='frames')
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)
    
    # Skip expensive beat tracking for speed
    # Use simple tempo estimation
    tempo = 120.0  # Default tempo
    
    # Only compute first 3 MFCCs for speed
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=3, hop_length=hop_length)
    
    # Create time axis
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    
    # Fast normalization function
    def normalize_fast(feature, min_val=0, max_val=100):
        if len(feature) == 0:
            return []
        feature_min = np.min(feature)
        feature_max = np.max(feature)
        if feature_max == feature_min:
            return [min_val] * len(feature)
        norm = (feature - feature_min) / (feature_max - feature_min)
        return (norm * (max_val - min_val) + min_val).tolist()
    
    return {
        'duration': duration,
        'sample_rate': sr,
        'times': times.tolist(),
        'features': {
            'amplitude': normalize_fast(rms * 100, 0, 100),
            'brightness': normalize_fast(spectral_centroid, 0, 100),
            'roughness': normalize_fast(zcr * 100, 0, 100),
            'pitch_proxy': normalize_fast(pitch_proxy, 0, 100),
            'mfcc_1': normalize_fast(mfccs[0], 0, 100),
            'mfcc_2': normalize_fast(mfccs[1], 0, 100) if len(mfccs) > 1 else [0] * len(times),
        },
        'events': {
            'onsets': onset_times.tolist(),
            'tempo': float(tempo)
        }
    }

def generate_after_effects_keyframes_fast(analysis: Dict, audio_filename: str) -> Dict:
    """Generate simplified After Effects keyframes for speed."""
    
    features = analysis['features']
    times = analysis['times']
    fps = 30
    
    # Reduce keyframe density for speed (every 3rd frame instead of every frame)
    frame_step = 3
    
    def time_to_frame(time_sec):
        return int(time_sec * fps)
    
    # Create simplified keyframe arrays
    keyframes = {}
    
    # Only essential properties for speed
    keyframes['scale'] = []
    keyframes['opacity'] = []
    keyframes['hue'] = []
    keyframes['position_x'] = []
    
    # Sample fewer keyframes for speed
    for i in range(0, len(times), frame_step):  # Skip frames for speed
        if i >= len(features['amplitude']):
            break
            
        time = times[i]
        frame = time_to_frame(time)
        
        # Scale: 50-150% based on amplitude
        scale_val = 50 + (features['amplitude'][i] * 1.0)
        keyframes['scale'].append([frame, scale_val])
        
        # Opacity: 20-100% based on amplitude
        opacity_val = 20 + (features['amplitude'][i] * 0.8)
        keyframes['opacity'].append([frame, opacity_val])
        
        # Hue: simplified color mapping
        hue_val = (features['brightness'][i] * 3.6) % 360  # Map to 0-360
        keyframes['hue'].append([frame, hue_val])
        
        # Position X: based on roughness
        pos_x = (features['roughness'][i] - 50) * 2  # -100 to +100
        keyframes['position_x'].append([frame, pos_x])
    
    # Add onset markers (simplified)
    keyframes['onset_markers'] = []
    for onset_time in analysis['events']['onsets'][:5]:  # Limit to first 5 onsets
        frame = time_to_frame(onset_time)
        keyframes['onset_markers'].append([frame, 100])
    
    return {
        'audio_file': audio_filename,
        'duration_seconds': analysis['duration'],
        'duration_frames': time_to_frame(analysis['duration']),
        'fps': fps,
        'tempo': analysis['events']['tempo'],
        'keyframes': keyframes,
        'metadata': {
            'total_keyframes': len(keyframes['scale']),
            'onset_count': len(analysis['events']['onsets']),
            'analysis_features': list(features.keys()),
            'optimization': 'fast_mode'
        }
    }

def process_single_audio_file(args):
    """Process a single audio file (for parallel processing)."""
    audio_file, output_dir = args
    
    try:
        # Determine instrument from path
        relative_path = os.path.relpath(audio_file, output_dir)
        path_parts = Path(relative_path).parts
        
        if len(path_parts) > 1:
            instrument = path_parts[0]
        else:
            instrument = "Unknown"
        
        # Create keyframes output directory
        keyframes_base_dir = "outputs/json/keyframes"
        os.makedirs(keyframes_base_dir, exist_ok=True)
        
        # Analyze audio (fast mode)
        analysis = analyze_audio_features_fast(audio_file)
        
        # Generate keyframes (fast mode)
        keyframe_data = generate_after_effects_keyframes_fast(analysis, os.path.basename(audio_file))
        
        # Save keyframe data
        audio_basename = Path(audio_file).stem
        keyframe_file = os.path.join(keyframes_base_dir, f"{audio_basename}_keyframes.json")
        
        with open(keyframe_file, 'w', encoding='utf-8') as f:
            json.dump(keyframe_data, f, indent=2)
        
        return (True, audio_file, keyframe_file, analysis['duration'], 
                keyframe_data['metadata']['total_keyframes'])
        
    except Exception as e:
        return (False, audio_file, str(e), 0, 0)

def process_audio_directory_fast(audio_dir: str):
    """Process all audio files using parallel processing for speed."""
    
    print("FAST AUDIO TO KEYFRAMES EXTRACTOR")
    print("=" * 50)
    print(f"Input directory: {audio_dir}")
    print()
    
    if not os.path.exists(audio_dir):
        print(f"❌ ERROR: Directory not found: {audio_dir}")
        return
    
    # Find all audio files
    audio_files = []
    for ext in ['*.wav', '*.mp3', '*.flac', '*.aiff']:
        audio_files.extend(glob.glob(os.path.join(audio_dir, '**', ext), recursive=True))
    
    # Exclude files in Keyframes directory
    audio_files = [f for f in audio_files if 'Keyframes' not in f]
    
    if not audio_files:
        print("❌ No audio files found")
        return
    
    print(f"🎵 Found {len(audio_files)} audio files")
    print()
    
    # Create keyframes base directory in new location
    keyframes_base_dir = "outputs/json/keyframes"
    os.makedirs(keyframes_base_dir, exist_ok=True)
    
    # Prepare tasks for parallel processing
    tasks = [(audio_file, audio_dir) for audio_file in audio_files]
    
    # Use parallel processing
    cpu_count = mp.cpu_count()
    max_workers = min(cpu_count, len(tasks))
    
    print(f"⚡ Using {max_workers} parallel workers for fast processing...")
    print()
    
    total_processed = 0
    failed_files = []
    
    # Process files in parallel with explicit shutdown
    executor = ProcessPoolExecutor(max_workers=max_workers)
    try:
        # Submit all tasks
        future_to_task = {executor.submit(process_single_audio_file, task): task for task in tasks}

        # Process results as they complete
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            audio_file, _ = task

            try:
                result = future.result()
                success, processed_file, output_info, duration, keyframes = result

                filename = os.path.basename(processed_file)

                if success:
                    print(f"✅ {filename}")
                    print(f"   Duration: {duration:.2f}s, Keyframes: {keyframes}")
                    total_processed += 1
                else:
                    print(f"❌ {filename} → {output_info}")
                    failed_files.append(processed_file)

            except Exception as e:
                print(f"❌ {os.path.basename(audio_file)} → Exception: {e}")
                failed_files.append(audio_file)
    finally:
        # Force shutdown and cleanup
        executor.shutdown(wait=True)
        del executor
    
    print()
    print(f"🎯 FAST KEYFRAME GENERATION COMPLETE!")
    print(f"📁 Output directory: {keyframes_base_dir}")
    print(f"✅ Successfully processed: {total_processed} files")
    print(f"❌ Failed to process: {len(failed_files)} files")
    
    if failed_files:
        print(f"\nFailed files:")
        for failed_file in failed_files[:5]:  # Show first 5 only
            print(f"  - {os.path.basename(failed_file)}")
        if len(failed_files) > 5:
            print(f"  ... and {len(failed_files) - 5} more")
    
    # Show directory structure
    print(f"\n📁 Keyframe file structure:")
    for root, dirs, files in os.walk(keyframes_base_dir):
        level = root.replace(keyframes_base_dir, '').count(os.sep)
        indent = '  ' * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = '  ' * (level + 1)
        for file in files[:3]:  # Show first 3 files only
            if file.endswith('.json'):
                print(f"{subindent}{file}")
        if len([f for f in files if f.endswith('.json')]) > 3:
            remaining = len([f for f in files if f.endswith('.json')]) - 3
            print(f"{subindent}... and {remaining} more files")

def main():
    if len(sys.argv) < 2:
        print("Usage: python audio_to_keyframes_fast.py <audio_directory>")
        print("Example: python audio_to_keyframes_fast.py 'Audio'")
        sys.exit(1)

    audio_dir = sys.argv[1]

    try:
        process_audio_directory_fast(audio_dir)
        # Force cleanup of multiprocessing resources
        import gc
        gc.collect()
        print("🎯 Cleanup complete, exiting...")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)
    finally:
        # Ensure all multiprocessing resources are cleaned up
        import multiprocessing as mp
        mp.util._exit_function()
        # Gentle exit after cleanup
        sys.exit(0)

if __name__ == "__main__":
    main()