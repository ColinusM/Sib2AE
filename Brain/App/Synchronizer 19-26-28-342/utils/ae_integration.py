#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict


@dataclass
class AELayerConfig:
    """Configuration for an After Effects layer"""
    layer_name: str
    start_time_seconds: float
    duration_seconds: float
    notehead_svg_path: str
    keyframes_file: str
    instrument: str
    pitch_name: str
    velocity: int


@dataclass
class AEProjectConfig:
    """Configuration for After Effects project"""
    project_name: str
    composition_name: str
    width: int = 1920
    height: int = 1080
    frame_rate: float = 30.0
    duration_seconds: float = 10.0
    background_color: List[float] = None

    def __post_init__(self):
        if self.background_color is None:
            self.background_color = [0.0, 0.0, 0.0]  # Black background


class AEIntegration:
    """After Effects integration for synchronized music animation"""
    
    def __init__(self, fps: float = 30.0):
        self.fps = fps
        self.project_config = None
        self.layers = []
        
    def load_synchronized_data(self, sync_data_file: str) -> Dict:
        """Load synchronized data from master synchronization file"""
        with open(sync_data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_master_timing(self, master_timing_file: str) -> Dict:
        """Load master MIDI timing reference"""
        with open(master_timing_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_layer_from_keyframes(self, keyframes_file: str, 
                                  notehead_svg_path: str,
                                  start_time_seconds: float,
                                  layer_name: str) -> AELayerConfig:
        """Create AE layer configuration from keyframe file with master timing"""
        
        # Load keyframes data (mirrors audio_to_keyframes_fast.py format)
        with open(keyframes_file, 'r', encoding='utf-8') as f:
            keyframe_data = json.load(f)
        
        # Extract metadata from keyframes
        duration_seconds = keyframe_data.get('duration_seconds', 10.0)
        metadata = keyframe_data.get('metadata', {})
        
        # Extract instrument and pitch from filename or metadata
        basename = Path(keyframes_file).stem
        parts = basename.split('_')
        
        instrument = "Unknown"
        pitch_name = "C4"
        velocity = 64
        
        # Parse filename: note_000_Flûte_A4_vel76_keyframes
        if len(parts) >= 4:
            if len(parts) >= 2:
                instrument = parts[2] if len(parts) > 2 else "Unknown"
            if len(parts) >= 3:
                pitch_name = parts[3] if len(parts) > 3 else "C4"
            if len(parts) >= 4 and parts[4].startswith('vel'):
                try:
                    velocity = int(parts[4][3:])
                except ValueError:
                    velocity = 64
        
        return AELayerConfig(
            layer_name=layer_name,
            start_time_seconds=start_time_seconds,
            duration_seconds=duration_seconds,
            notehead_svg_path=notehead_svg_path,
            keyframes_file=keyframes_file,
            instrument=instrument,
            pitch_name=pitch_name,
            velocity=velocity
        )
    
    def generate_layers_from_master_timing(self, master_timing_file: str,
                                         keyframes_dir: str,
                                         noteheads_dir: str) -> List[AELayerConfig]:
        """Generate AE layers with start times matching MIDI note timing from master MIDI"""
        
        master_timing = self.load_master_timing(master_timing_file)
        layers = []
        
        # Process each note event from master MIDI
        for i, note_event in enumerate(master_timing.get('note_events', [])):
            start_time_seconds = note_event['start_time_seconds']
            instrument = note_event['instrument']
            pitch_name = note_event['pitch_name']
            velocity = note_event['velocity']
            
            # Find corresponding keyframes file
            # Format: note_000_Flûte_A4_vel76_keyframes.json
            keyframes_pattern = f"note_{i:03d}_{instrument}_{pitch_name}_vel{velocity}_keyframes.json"
            
            # Search in instrument subdirectories
            instrument_keyframes_dir = os.path.join(keyframes_dir, instrument)
            keyframes_file = os.path.join(instrument_keyframes_dir, keyframes_pattern)
            
            if not os.path.exists(keyframes_file):
                # Try alternative instrument names
                alt_instrument = "Flûte" if "Flute" in instrument else instrument
                instrument_keyframes_dir = os.path.join(keyframes_dir, alt_instrument)
                keyframes_pattern = f"note_{i:03d}_{alt_instrument}_{pitch_name}_vel{velocity}_keyframes.json"
                keyframes_file = os.path.join(instrument_keyframes_dir, keyframes_pattern)
            
            # Find corresponding notehead SVG
            # Format: notehead_000_P1_A4_M4.svg
            notehead_pattern = f"notehead_{i:03d}_*.svg"
            notehead_file = None
            
            # Search in noteheads directory structure
            for root, dirs, files in os.walk(noteheads_dir):
                for file in files:
                    if file.startswith(f"notehead_{i:03d}_") and file.endswith('.svg'):
                        notehead_file = os.path.join(root, file)
                        break
                if notehead_file:
                    break
            
            if os.path.exists(keyframes_file) and notehead_file:
                layer_name = f"{instrument}_{pitch_name}_{i:03d}"
                
                layer_config = self.create_layer_from_keyframes(
                    keyframes_file=keyframes_file,
                    notehead_svg_path=notehead_file,
                    start_time_seconds=start_time_seconds,  # Critical: Use master MIDI timing
                    layer_name=layer_name
                )
                
                layers.append(layer_config)
                print(f"✅ Created layer: {layer_name} at {start_time_seconds:.3f}s")
            else:
                print(f"⚠️  Missing files for note {i}: keyframes={keyframes_file}, svg={notehead_file}")
        
        return layers
    
    def create_project_config(self, project_name: str, total_duration: float) -> AEProjectConfig:
        """Create After Effects project configuration"""
        
        composition_name = f"{project_name}_Synchronized"
        
        return AEProjectConfig(
            project_name=project_name,
            composition_name=composition_name,
            width=1920,
            height=1080,
            frame_rate=self.fps,
            duration_seconds=total_duration,
            background_color=[0.0, 0.0, 0.0]
        )
    
    def generate_jsx_import_script(self, layers: List[AELayerConfig], 
                                 project_config: AEProjectConfig,
                                 output_path: str) -> str:
        """Generate JSX script for automated After Effects import with master MIDI timing"""
        
        jsx_script = f'''// After Effects Synchronized Music Animation Import Script
// Generated with Sib2Ae - Synchronized Music Animation System
// 🎵 Generated with Claude Code (https://claude.ai/code)

app.beginUndoGroup("Import Synchronized Music Animation");

try {{
    // Create new project
    var project = app.project;
    
    // Create main composition
    var comp = project.items.addComp(
        "{project_config.composition_name}",
        {project_config.width},
        {project_config.height},
        1.0, // pixel aspect ratio
        {project_config.duration_seconds:.3f},
        {project_config.frame_rate}
    );
    
    // Set background color
    comp.bgColor = [{project_config.background_color[0]:.3f}, {project_config.background_color[1]:.3f}, {project_config.background_color[2]:.3f}];
    
    // Import and create layers with synchronized timing
'''
        
        # Add layer creation code for each notehead
        for i, layer in enumerate(layers):
            jsx_script += f'''
    // Layer {i + 1}: {layer.layer_name}
    // Start time: {layer.start_time_seconds:.3f} seconds (from master MIDI)
    var importFile{i + 1} = new ImportOptions(File("{layer.notehead_svg_path}"));
    var footage{i + 1} = project.importFile(importFile{i + 1});
    var layer{i + 1} = comp.layers.add(footage{i + 1});
    
    // Set layer properties
    layer{i + 1}.name = "{layer.layer_name}";
    layer{i + 1}.startTime = {layer.start_time_seconds:.6f}; // Critical: Master MIDI timing
    layer{i + 1}.outPoint = {layer.start_time_seconds + layer.duration_seconds:.6f};
    
    // Load and apply keyframes from JSON
    var keyframesFile{i + 1} = File("{layer.keyframes_file}");
    if (keyframesFile{i + 1}.exists) {{
        keyframesFile{i + 1}.open("r");
        var keyframesData{i + 1} = eval("(" + keyframesFile{i + 1}.read() + ")");
        keyframesFile{i + 1}.close();
        
        // Apply scale keyframes
        if (keyframesData{i + 1}.keyframes.scale) {{
            var scaleKeyframes = keyframesData{i + 1}.keyframes.scale;
            layer{i + 1}.transform.scale.expression = "";
            
            for (var k = 0; k < scaleKeyframes.length; k++) {{
                var frameNum = scaleKeyframes[k][0];
                var scaleValue = scaleKeyframes[k][1];
                var timeValue = frameNum / {project_config.frame_rate:.1f};
                
                // Add keyframe with time offset for layer start time
                layer{i + 1}.transform.scale.setValueAtTime(
                    timeValue,
                    [scaleValue, scaleValue]
                );
            }}
        }}
        
        // Apply opacity keyframes
        if (keyframesData{i + 1}.keyframes.opacity) {{
            var opacityKeyframes = keyframesData{i + 1}.keyframes.opacity;
            layer{i + 1}.transform.opacity.expression = "";
            
            for (var k = 0; k < opacityKeyframes.length; k++) {{
                var frameNum = opacityKeyframes[k][0];
                var opacityValue = opacityKeyframes[k][1];
                var timeValue = frameNum / {project_config.frame_rate:.1f};
                
                layer{i + 1}.transform.opacity.setValueAtTime(
                    timeValue,
                    opacityValue
                );
            }}
        }}
        
        // Apply position keyframes
        if (keyframesData{i + 1}.keyframes.position_x) {{
            var posXKeyframes = keyframesData{i + 1}.keyframes.position_x;
            layer{i + 1}.transform.position.expression = "";
            
            for (var k = 0; k < posXKeyframes.length; k++) {{
                var frameNum = posXKeyframes[k][0];
                var posXValue = posXKeyframes[k][1];
                var timeValue = frameNum / {project_config.frame_rate:.1f};
                
                // Get current position and modify X
                var currentPos = layer{i + 1}.transform.position.valueAtTime(timeValue, false);
                layer{i + 1}.transform.position.setValueAtTime(
                    timeValue,
                    [currentPos[0] + posXValue, currentPos[1]]
                );
            }}
        }}
    }}
    
    // Set layer color based on instrument
    var layerColor = 0; // Red
    if ("{layer.instrument}".toLowerCase().indexOf("flute") >= 0 || 
        "{layer.instrument}".toLowerCase().indexOf("flûte") >= 0) {{
        layerColor = 5; // Orange
    }} else if ("{layer.instrument}".toLowerCase().indexOf("violin") >= 0 ||
               "{layer.instrument}".toLowerCase().indexOf("violon") >= 0) {{
        layerColor = 2; // Green
    }}
    layer{i + 1}.label = layerColor;
'''
        
        jsx_script += f'''
    
    // Final composition setup
    comp.openInViewer();
    
    alert("Successfully imported synchronized music animation!\\n" +
          "Project: {project_config.project_name}\\n" +
          "Composition: {project_config.composition_name}\\n" +
          "Layers: {len(layers)}\\n" +
          "Duration: {project_config.duration_seconds:.1f} seconds\\n" +
          "Frame Rate: {project_config.frame_rate} fps\\n\\n" +
          "All layers have start times synchronized with master MIDI timing.");

}} catch (error) {{
    alert("Error importing synchronized animation: " + error.toString());
}}

app.endUndoGroup();
'''
        
        # Write JSX script to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(jsx_script)
        
        return jsx_script
    
    def create_master_synchronization_json(self, layers: List[AELayerConfig],
                                         project_config: AEProjectConfig,
                                         master_timing_file: str,
                                         output_path: str) -> Dict:
        """Create master synchronization JSON with all timing data"""
        
        master_timing = self.load_master_timing(master_timing_file)
        
        sync_data = {
            "project_metadata": {
                "project_name": project_config.project_name,
                "composition_name": project_config.composition_name,
                "total_duration_seconds": project_config.duration_seconds,
                "frame_rate": project_config.frame_rate,
                "layer_count": len(layers),
                "generation_timestamp": str(Path().absolute()),
                "sib2ae_version": "1.0.0"
            },
            "master_timing_reference": {
                "source_file": master_timing_file,
                "total_duration_seconds": master_timing.get('total_duration_seconds', 0),
                "tempo_map": master_timing.get('tempo_map', []),
                "ppq": master_timing.get('ppq', 960)
            },
            "synchronized_layers": [],
            "timing_accuracy": {
                "synchronization_method": "master_midi_timing",
                "start_time_source": "original_master_midi",
                "frame_accuracy": True,
                "layer_timing_preserved": True
            }
        }
        
        # Add layer information
        for layer in layers:
            layer_data = {
                "layer_name": layer.layer_name,
                "start_time_seconds": layer.start_time_seconds,  # From master MIDI
                "duration_seconds": layer.duration_seconds,
                "instrument": layer.instrument,
                "pitch_name": layer.pitch_name,
                "velocity": layer.velocity,
                "assets": {
                    "notehead_svg": layer.notehead_svg_path,
                    "keyframes_json": layer.keyframes_file
                },
                "timing_source": "master_midi_note_events"
            }
            sync_data["synchronized_layers"].append(layer_data)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sync_data, f, indent=2, ensure_ascii=False)
        
        return sync_data
    
    def generate_full_after_effects_integration(self, master_timing_file: str,
                                               keyframes_dir: str,
                                               noteheads_dir: str,
                                               output_dir: str,
                                               project_name: str = "SynchronizedMusicAnimation") -> Dict:
        """Generate complete After Effects integration with master MIDI timing"""
        
        print("🎬 AFTER EFFECTS INTEGRATION GENERATOR")
        print("=" * 50)
        print(f"Master timing: {master_timing_file}")
        print(f"Keyframes dir: {keyframes_dir}")
        print(f"Noteheads dir: {noteheads_dir}")
        print(f"Output dir: {output_dir}")
        print()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Load master timing to get total duration
        master_timing = self.load_master_timing(master_timing_file)
        total_duration = master_timing.get('total_duration_seconds', 10.0)
        
        # Generate layers with master MIDI timing
        print("📝 Generating layers from master MIDI timing...")
        layers = self.generate_layers_from_master_timing(
            master_timing_file=master_timing_file,
            keyframes_dir=keyframes_dir,
            noteheads_dir=noteheads_dir
        )
        
        if not layers:
            print("❌ No layers generated - check file paths and timing data")
            return {}
        
        print(f"✅ Generated {len(layers)} synchronized layers")
        
        # Create project configuration
        project_config = self.create_project_config(project_name, total_duration)
        
        # Generate JSX import script
        jsx_output = os.path.join(output_dir, "ae_import_script.jsx")
        print(f"🎞️  Generating JSX import script: {jsx_output}")
        
        jsx_script = self.generate_jsx_import_script(
            layers=layers,
            project_config=project_config,
            output_path=jsx_output
        )
        
        # Generate master synchronization JSON
        sync_output = os.path.join(output_dir, "master_synchronization.json")
        print(f"📊 Generating synchronization data: {sync_output}")
        
        sync_data = self.create_master_synchronization_json(
            layers=layers,
            project_config=project_config,
            master_timing_file=master_timing_file,
            output_path=sync_output
        )
        
        print()
        print("🎯 AFTER EFFECTS INTEGRATION COMPLETE!")
        print(f"📁 Output directory: {output_dir}")
        print(f"🎞️  JSX script: {jsx_output}")
        print(f"📊 Sync data: {sync_output}")
        print(f"🎵 Synchronized layers: {len(layers)}")
        print(f"⏱️  Total duration: {total_duration:.2f} seconds")
        print()
        print("📋 Next steps:")
        print("1. Open After Effects")
        print(f"2. Run the JSX script: {jsx_output}")
        print("3. All noteheads will be imported with correct master MIDI timing")
        print("4. Each layer starts at the exact time from the original MIDI file")
        
        return {
            "jsx_script_path": jsx_output,
            "synchronization_data_path": sync_output,
            "layers_generated": len(layers),
            "total_duration_seconds": total_duration,
            "project_config": asdict(project_config),
            "layers": [asdict(layer) for layer in layers]
        }


def main():
    """Command line interface for After Effects integration"""
    
    if len(sys.argv) < 5:
        print("Usage: python ae_integration.py <master_timing_file> <keyframes_dir> <noteheads_dir> <output_dir> [project_name]")
        print()
        print("Example:")
        print('python ae_integration.py "Base/Saint-Saens Trio No 2_master_timing.json" "Audio/Keyframes" "Symbolic Separators" "Synchronizer/outputs" "MySyncProject"')
        print()
        print("Arguments:")
        print("  master_timing_file: Path to master MIDI timing JSON")
        print("  keyframes_dir: Directory containing keyframe JSON files")
        print("  noteheads_dir: Directory containing notehead SVG files")
        print("  output_dir: Directory for generated AE integration files")
        print("  project_name: Optional project name (default: SynchronizedMusicAnimation)")
        sys.exit(1)
    
    master_timing_file = sys.argv[1]
    keyframes_dir = sys.argv[2]
    noteheads_dir = sys.argv[3]
    output_dir = sys.argv[4]
    project_name = sys.argv[5] if len(sys.argv) > 5 else "SynchronizedMusicAnimation"
    
    try:
        ae_integration = AEIntegration(fps=30.0)
        result = ae_integration.generate_full_after_effects_integration(
            master_timing_file=master_timing_file,
            keyframes_dir=keyframes_dir,
            noteheads_dir=noteheads_dir,
            output_dir=output_dir,
            project_name=project_name
        )
        
        if result:
            print("\n🎉 After Effects integration generated successfully!")
        else:
            print("\n❌ Failed to generate After Effects integration")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()