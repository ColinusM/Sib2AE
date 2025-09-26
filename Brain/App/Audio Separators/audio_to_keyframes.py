#!/usr/bin/env python3

import librosa
import numpy as np
import os
import sys
import json
import glob
from pathlib import Path
from typing import Dict, List, Tuple
import scipy.signal

def analyze_audio_features(audio_file: str, sr: int = 44100) -> Dict:
    """Extract comprehensive audio features for keyframe generation."""
    
    print(f"🔊 Analyzing: {os.path.basename(audio_file)}")
    
    # Load audio
    y, sr = librosa.load(audio_file, sr=sr)
    duration = len(y) / sr
    
    print(f"   Duration: {duration:.3f}s, Sample Rate: {sr}Hz")
    
    # 1. Amplitude envelope (overall volume)
    hop_length = 512
    frame_length = 2048
    
    # RMS energy for smooth amplitude
    rms = librosa.feature.rms(y=y, hop_length=hop_length, frame_length=frame_length)[0]
    
    # 2. Spectral features
    # Spectral centroid (brightness)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
    
    # Spectral rolloff (frequency distribution)
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=hop_length)[0]
    
    # Zero crossing rate (texture/roughness)
    zcr = librosa.feature.zero_crossing_rate(y, hop_length=hop_length)[0]
    
    # 3. Pitch/frequency analysis
    # Fundamental frequency (F0)
    f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
    
    # 4. Onset detection
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=hop_length)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)
    
    # 5. Tempo and beat tracking
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
    beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop_length)
    
    # 6. MFCC features (timbre characteristics)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop_length)
    
    # Create time axis
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    
    # Normalize features for After Effects (0-100 range typically)
    def normalize_feature(feature, min_val=0, max_val=100):
        feature_clean = feature[~np.isnan(feature)]
        if len(feature_clean) == 0:
            return np.full_like(feature, min_val)
        feature_norm = (feature - np.nanmin(feature_clean)) / (np.nanmax(feature_clean) - np.nanmin(feature_clean))
        feature_norm = feature_norm * (max_val - min_val) + min_val
        feature_norm[np.isnan(feature_norm)] = min_val
        return feature_norm
    
    return {
        'duration': duration,
        'sample_rate': sr,
        'times': times.tolist(),
        'features': {
            'amplitude': normalize_feature(rms * 100, 0, 100).tolist(),  # Volume/Scale
            'brightness': normalize_feature(spectral_centroid, 0, 100).tolist(),  # Color/Brightness
            'frequency_spread': normalize_feature(spectral_rolloff, 0, 100).tolist(),  # Width/Spread
            'roughness': normalize_feature(zcr * 100, 0, 100).tolist(),  # Texture/Roughness
            'pitch': [float(p) if not np.isnan(p) else 0.0 for p in f0],  # Actual pitch in Hz
            'pitch_confidence': voiced_probs.tolist(),  # Pitch detection confidence
            'mfcc_1': normalize_feature(mfccs[1], 0, 100).tolist(),  # Timbre 1
            'mfcc_2': normalize_feature(mfccs[2], 0, 100).tolist(),  # Timbre 2
            'mfcc_3': normalize_feature(mfccs[3], 0, 100).tolist(),  # Timbre 3
        },
        'events': {
            'onsets': onset_times.tolist(),  # Note attack times
            'beats': beat_times.tolist(),  # Beat positions
            'tempo': float(tempo)  # Overall tempo
        }
    }

def generate_after_effects_keyframes(analysis: Dict, audio_filename: str) -> Dict:
    """Generate After Effects compatible keyframe data."""
    
    features = analysis['features']
    times = analysis['times']
    fps = 30  # After Effects frame rate
    
    # Convert times to frame numbers
    def time_to_frame(time_sec):
        return int(time_sec * fps)
    
    # Create keyframe arrays
    keyframes = {}
    
    # Primary animation properties
    keyframes['scale'] = []  # Based on amplitude
    keyframes['opacity'] = []  # Based on amplitude with different curve
    keyframes['rotation'] = []  # Based on pitch changes
    keyframes['position_x'] = []  # Based on spectral centroid
    keyframes['position_y'] = []  # Based on frequency spread
    
    # Color properties
    keyframes['hue'] = []  # Based on pitch
    keyframes['saturation'] = []  # Based on brightness
    keyframes['lightness'] = []  # Based on amplitude
    
    # Effect properties
    keyframes['blur'] = []  # Based on roughness (inverted)
    keyframes['glow_intensity'] = []  # Based on spectral energy
    
    for i, time in enumerate(times):
        frame = time_to_frame(time)
        
        # Scale: 50-150% based on amplitude
        scale_val = 50 + (features['amplitude'][i] * 1.0)  # 50-150%
        keyframes['scale'].append([frame, scale_val])
        
        # Opacity: 20-100% based on amplitude
        opacity_val = 20 + (features['amplitude'][i] * 0.8)  # 20-100%
        keyframes['opacity'].append([frame, opacity_val])
        
        # Rotation: -180 to +180 degrees based on pitch changes
        if i > 0 and features['pitch'][i] > 0 and features['pitch'][i-1] > 0:
            pitch_change = (features['pitch'][i] - features['pitch'][i-1]) / max(features['pitch'][i], 1)
            rotation_val = pitch_change * 180  # Convert to degrees
        else:
            rotation_val = 0
        keyframes['rotation'].append([frame, rotation_val])
        
        # Position X: -100 to +100 based on spectral centroid
        pos_x = (features['brightness'][i] - 50) * 2  # -100 to +100
        keyframes['position_x'].append([frame, pos_x])
        
        # Position Y: -50 to +50 based on frequency spread
        pos_y = (features['frequency_spread'][i] - 50) * 1  # -50 to +50
        keyframes['position_y'].append([frame, pos_y])
        
        # Hue: 0-360 degrees based on pitch
        if features['pitch'][i] > 0:
            # Map pitch to hue (musical intervals to color wheel)
            normalized_pitch = (features['pitch'][i] - 200) / (2000 - 200)  # Normalize roughly
            hue_val = (normalized_pitch * 360) % 360
        else:
            hue_val = 0
        keyframes['hue'].append([frame, hue_val])
        
        # Saturation: 0-100% based on brightness
        saturation_val = features['brightness'][i]
        keyframes['saturation'].append([frame, saturation_val])
        
        # Lightness: 30-90% based on amplitude
        lightness_val = 30 + (features['amplitude'][i] * 0.6)  # 30-90%
        keyframes['lightness'].append([frame, lightness_val])
        
        # Blur: 0-10 pixels (inverted roughness for smoothness)
        blur_val = (100 - features['roughness'][i]) * 0.1  # 0-10 pixels
        keyframes['blur'].append([frame, blur_val])
        
        # Glow intensity: 0-100% based on combined energy
        glow_val = (features['amplitude'][i] + features['brightness'][i]) / 2
        keyframes['glow_intensity'].append([frame, glow_val])
    
    # Add onset and beat markers
    keyframes['onset_markers'] = []
    for onset_time in analysis['events']['onsets']:
        frame = time_to_frame(onset_time)
        keyframes['onset_markers'].append([frame, 100])  # Spike to 100%
        
    keyframes['beat_markers'] = []
    for beat_time in analysis['events']['beats']:
        frame = time_to_frame(beat_time)
        keyframes['beat_markers'].append([frame, 100])  # Spike to 100%
    
    return {
        'audio_file': audio_filename,
        'duration_seconds': analysis['duration'],
        'duration_frames': time_to_frame(analysis['duration']),
        'fps': fps,
        'tempo': analysis['events']['tempo'],
        'keyframes': keyframes,
        'metadata': {
            'total_keyframes': len(times),
            'onset_count': len(analysis['events']['onsets']),
            'beat_count': len(analysis['events']['beats']),
            'analysis_features': list(features.keys())
        }
    }

def process_audio_directory(audio_dir: str):
    """Process all audio files in directory and generate keyframe data."""
    
    print("AUDIO TO KEYFRAMES EXTRACTOR")
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
    
    if not audio_files:
        print("❌ No audio files found")
        return
    
    print(f"🎵 Found {len(audio_files)} audio files")
    print()
    
    # Create output directory structure in new location
    keyframes_base_dir = "outputs/json/keyframes"
    os.makedirs(keyframes_base_dir, exist_ok=True)
    
    # Process each audio file
    total_processed = 0
    failed_files = []
    
    for audio_file in audio_files:
        try:
            # Determine instrument from path
            relative_path = os.path.relpath(audio_file, audio_dir)
            path_parts = Path(relative_path).parts
            
            if len(path_parts) > 1:
                instrument = path_parts[0]  # e.g., "Flûte", "Violon"
            else:
                instrument = "Unknown"
            
            # Create instrument directory
            # All keyframes go directly in keyframes directory
            instrument_keyframes_dir = keyframes_base_dir
            
            # Analyze audio
            analysis = analyze_audio_features(audio_file)
            
            # Generate keyframes
            keyframe_data = generate_after_effects_keyframes(analysis, os.path.basename(audio_file))
            
            # Save keyframe data
            audio_basename = Path(audio_file).stem
            keyframe_file = os.path.join(instrument_keyframes_dir, f"{audio_basename}_keyframes.json")
            
            with open(keyframe_file, 'w', encoding='utf-8') as f:
                json.dump(keyframe_data, f, indent=2)
            
            print(f"✅ Generated keyframes: {keyframe_file}")
            print(f"   Duration: {analysis['duration']:.2f}s")
            print(f"   Keyframes: {keyframe_data['metadata']['total_keyframes']}")
            print(f"   Onsets: {keyframe_data['metadata']['onset_count']}")
            print(f"   Beats: {keyframe_data['metadata']['beat_count']}")
            print(f"   Tempo: {analysis['events']['tempo']:.1f} BPM")
            print()
            
            total_processed += 1
            
        except Exception as e:
            print(f"❌ Failed to process {audio_file}: {e}")
            failed_files.append(audio_file)
    
    # Summary
    print(f"🎯 KEYFRAME GENERATION COMPLETE!")
    print(f"📁 Output directory: {keyframes_base_dir}")
    print(f"✅ Successfully processed: {total_processed} files")
    print(f"❌ Failed to process: {len(failed_files)} files")
    
    if failed_files:
        print(f"\nFailed files:")
        for failed_file in failed_files:
            print(f"  - {failed_file}")
    
    # Show directory structure
    print(f"\n📁 Keyframe file structure:")
    for root, dirs, files in os.walk(keyframes_base_dir):
        level = root.replace(keyframes_base_dir, '').count(os.sep)
        indent = '  ' * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = '  ' * (level + 1)
        for file in files:
            if file.endswith('.json'):
                print(f"{subindent}{file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python audio_to_keyframes.py <audio_directory>")
        print("Example: python audio_to_keyframes.py 'Audio'")
        sys.exit(1)
    
    audio_dir = sys.argv[1]
    
    try:
        process_audio_directory(audio_dir)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()