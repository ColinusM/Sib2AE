# PRP: Synchronized Music Animation System for Sib2Ae

## Goal

Implement a synchronized music animation system that merges the SVG processing pipeline (visual noteheads) with the audio processing pipeline (MIDI timing and keyframes) to create perfectly timed After Effects animations. The system will match individual noteheads to their corresponding MIDI notes, handle tied note sequences, and generate a unified synchronization format for After Effects import.

## Why

### Business Value
- **Complete After Effects Integration**: Enables pixel-perfect music visualization with synchronized audio
- **Professional Animation Workflow**: Bridges the gap between music notation and motion graphics
- **Automated Synchronization**: Eliminates manual timing alignment work in After Effects
- **Scalable Production**: Handles complex scores with multiple instruments and tied note sequences

### User Impact
- **Music Visualizers**: Create frame-accurate animations synchronized to musical performance
- **Educational Content**: Generate animated scores that highlight individual notes as they play
- **Performance Analysis**: Visualize musical timing and expression through synchronized graphics
- **Commercial Production**: Professional-grade music video and advertising content creation

## What

### Core Features
- **XML-MIDI Note Matching**: Match visual noteheads to MIDI notes using pitch, timing, and tolerance algorithms
- **Tied Note Handling**: Process tied note sequences with accurate duration calculation and visual correlation
- **Synchronization Bridge**: Create unified timing system from MusicXML beats to MIDI seconds to After Effects frames
- **Enhanced Output Format**: Generate master JSON with synchronized timing data for After Effects import
- **Pipeline Integration**: Seamlessly merge existing SVG and audio processing workflows

### Success Criteria
- [ ] XML notes accurately matched to MIDI notes with 100ms tolerance (configurable)
- [ ] Tied notes properly consolidated with calculated start times for all visual elements
- [ ] Individual noteheads linked to corresponding audio files and keyframe data
- [ ] Master synchronization JSON generated with frame-accurate After Effects timing
- [ ] Both quantized and unquantized MIDI support with adaptive tolerance
- [ ] Complete pipeline maintains existing SVG and audio output quality
- [ ] Performance optimization supports large scores (100+ notes) in under 30 seconds

## All Needed Context

### Documentation & References

- **MusicXML Tied Notes Specification**: https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/tied/
  - Why: Official specification for detecting and processing tied note sequences
  - Key: `<tie type="start">` vs `<tied type="start">` distinction for sound vs. visual behavior

- **MIDI Timing Standards**: https://midi.org/community/midi-specifications/calculating-millisecond-time-from-delta-time
  - Why: Authoritative source for MIDI tick-to-time conversion algorithms
  - Key: PPQ (pulses per quarter note) standards and microsecond precision requirements

- **After Effects ExtendScript Documentation**: https://ae-scripting.docsforadobe.dev/
  - Why: Official JSX automation for programmatic After Effects project creation
  - Key: JSON keyframe import and expression-driven animation patterns

- **Music Synchronization Research**: https://transactions.ismir.net/articles/10.5334/tismir.149
  - Why: Academic foundation for audio-MIDI alignment algorithms and tolerance values
  - Key: Dynamic Time Warping and 50ms tolerance standards for musical applications

### Code Examples from Codebase

**XML Processing Pattern** (from `truly_universal_noteheads_extractor.py:22-35`):
```python
for part in root.findall('part'):
    part_id = part.get('id')
    cumulative_x = 0
    
    for measure in part.findall('measure'):
        measure_num = int(measure.get('number'))
        measure_width = float(measure.get('width', 0))
        
        for note in measure.findall('note'):
            if note.find('rest') is not None:
                continue
            # Process individual notes with coordinate transformation
```

**MIDI Analysis Pattern** (from `midi_note_separator.py:48-59`):
```python
note_info = {
    'id': note_id,
    'track': track_idx,
    'track_name': track.name,
    'note': msg.note,
    'note_name': note_to_name(msg.note),
    'velocity': velocity,
    'start_ticks': start_time,
    'end_ticks': current_time,
    'duration_ticks': duration,
    'channel': msg.channel
}
```

**Keyframe Structure Pattern** (from `audio_to_keyframes.py`):
```python
keyframes = {
    'scale': [[frame_number, scale_value], ...],
    'opacity': [[frame_number, opacity_value], ...],
    'onset_markers': [[frame_number, 100], ...]
}
```

### Current File Structure Context

```
Sib2Ae/
├── Separators/                     # SVG Processing Pipeline
│   ├── truly_universal_noteheads_extractor.py
│   ├── xml_based_instrument_separator.py
│   └── sib2ae_master_pipeline.py
├── Audio Separators/               # Audio Processing Pipeline  
│   ├── midi_note_separator.py
│   ├── midi_to_audio_renderer_fast.py
│   └── audio_to_keyframes_fast.py
├── Symbolic Separators/            # SVG Output
│   └── [Instrument]/individual_noteheads/
├── Audio/                          # Audio Output
│   ├── [Instrument]/               # WAV files
│   └── Keyframes/                  # JSON files
└── Base/                           # Input files
    ├── SS 9.musicxml
    ├── SS 9 full.svg
    └── Saint-Saens Trio No 2.mid
```

### Known Gotchas

**CRITICAL: XML vs MIDI Part Identification**
- XML uses `<score-part id="P1">` with `<part-name>Flûte</part-name>`
- MIDI uses track names that may not exactly match XML part names
- Must implement fuzzy matching: "Flûte" (XML) vs "Flute" (MIDI track name)

**CRITICAL: Tied Note Duration Calculation**
- XML `<tie type="start">` and `<tie type="stop">` create visual noteheads but single MIDI note
- Subsequent tied noteheads need calculated start times based on beat position
- All tied noteheads must end at the same time as the MIDI note end time

**CRITICAL: Timing System Conversions**
- XML: Divisions-based timing (256 per quarter note)
- MIDI: Ticks per beat (typically 480-960 PPQ)
- Output: 30 FPS frame timing for After Effects
- Conversion errors accumulate - use integer arithmetic where possible

**CRITICAL: Unquantized MIDI Tolerance**
- Default 100ms tolerance for matching XML to unquantized MIDI
- Pitch must match exactly (enharmonic equivalent handling required)
- Log all matches and misses for debugging
- Prefer closest match when multiple candidates within tolerance

**CRITICAL: File Naming Consistency** 
- SVG: `notehead_000_P1_A4_M4.svg` (includes measure)
- Audio: `note_000_Flûte_A4_vel76.wav` (includes velocity)
- Must create unified naming convention for synchronization mapping

### Universal Coordinate System Constants
```python
# From existing codebase (truly_universal_noteheads_extractor.py)
X_SCALE = 3.206518      # Universal X scaling factor  
X_OFFSET = 564.93       # Universal X offset
FLUTE_BASE_Y = 1037     # Upper staff base Y position
VIOLIN_BASE_Y = 1417    # Lower staff base Y position
STAFF_SEPARATION = 380  # Pixel separation between staves
```

### Performance Requirements
- Process Saint-Saëns Trio (9 noteheads) in under 5 seconds
- Scale to larger scores (100+ notes) within 30 seconds
- Memory usage under 1GB for typical orchestral score
- Support parallel processing where possible

## Implementation Blueprint

### Phase 1: Context Gatherer Tool (`Synchronization/context_gatherer.py`)

**Purpose**: Standalone XML/MIDI/SVG analyzer that creates master relationship file

**Core Algorithm**:
```python
def gather_musical_context(xml_file: str, midi_file: str, svg_file: str) -> Dict:
    # 1. Extract XML note data with tied note detection
    xml_notes = extract_xml_notes_with_ties(xml_file)
    
    # 2. Extract MIDI timing data with tick-to-seconds conversion
    midi_notes = extract_midi_timing_data(midi_file)
    
    # 3. Create XML-MIDI note matching with tolerance
    note_matches = match_xml_to_midi_notes(xml_notes, midi_notes, tolerance_ms=100)
    
    # 4. Calculate tied note timing using beat position interpolation
    tied_note_timing = calculate_tied_note_positions(note_matches)
    
    # 5. Generate unified note relationships
    return create_master_relationships(note_matches, tied_note_timing)
```

**XML Tied Note Detection**:
```python
def detect_tied_note_sequences(xml_notes: List[Dict]) -> List[List[Dict]]:
    """
    Group notes into tied sequences using <tie> elements
    Returns: List of tied note groups, each group sharing same MIDI timing
    """
    tied_groups = []
    current_group = []
    
    for note in xml_notes:
        tie_start = note.get('tie_start', False)
        tie_stop = note.get('tie_stop', False)
        
        if tie_start and not current_group:
            current_group = [note]  # Start new tied sequence
        elif tie_stop and current_group:
            current_group.append(note)
            tied_groups.append(current_group)  # Complete sequence
            current_group = []
        elif current_group:
            current_group.append(note)  # Continue sequence
        else:
            tied_groups.append([note])  # Standalone note
    
    return tied_groups
```

**XML-MIDI Matching Algorithm**:
```python
def match_xml_to_midi_notes(xml_notes: List[Dict], midi_notes: List[Dict], 
                           tolerance_ms: int = 100) -> List[Dict]:
    """
    Match XML notes to MIDI notes using pitch + timing proximity
    Supports both quantized and unquantized MIDI with configurable tolerance
    """
    matches = []
    
    for xml_note in xml_notes:
        xml_pitch = xml_note['pitch']  # e.g., 'A4'
        xml_time_estimate = calculate_xml_note_timing(xml_note)  # Beat position to seconds
        
        best_match = None
        min_time_diff = float('inf')
        
        for midi_note in midi_notes:
            # Hard requirement: pitch must match exactly
            if midi_note['note_name'] != xml_pitch:
                continue
                
            # Calculate timing difference in milliseconds
            midi_time = midi_note['start_time_seconds']
            time_diff = abs(xml_time_estimate - midi_time) * 1000
            
            # Check if within tolerance and better than previous match
            if time_diff <= tolerance_ms and time_diff < min_time_diff:
                best_match = midi_note
                min_time_diff = time_diff
        
        if best_match:
            print(f"✅ Matched {xml_pitch} (tolerance: {min_time_diff:.1f}ms)")
            matches.append({
                'xml_note': xml_note,
                'midi_note': best_match,
                'time_difference_ms': min_time_diff
            })
        else:
            print(f"❌ No match found for {xml_pitch} at {xml_time_estimate:.2f}s")
    
    return matches
```

**Tied Note Timing Calculation**:
```python
def calculate_tied_note_positions(note_matches: List[Dict]) -> Dict:
    """
    Calculate start times for tied-to notes using beat position interpolation
    """
    tied_timing = {}
    
    for match in note_matches:
        xml_note = match['xml_note']
        midi_note = match['midi_note']
        
        if xml_note.get('tied_sequence'):
            tied_notes = xml_note['tied_sequence']
            midi_start = midi_note['start_time_seconds']
            midi_end = midi_note['end_time_seconds']
            midi_duration = midi_end - midi_start
            
            # Calculate proportional timing for each tied note
            for i, tied_note in enumerate(tied_notes):
                if i == 0:  # First note (tied-from) gets actual MIDI timing
                    tied_timing[tied_note['id']] = {
                        'start_time': midi_start,
                        'end_time': midi_end,
                        'is_primary': True
                    }
                else:  # Subsequent notes (tied-to) get calculated timing
                    # Proportional calculation based on beat position
                    beat_position_ratio = calculate_beat_position_ratio(tied_note, tied_notes)
                    calculated_start = midi_start + (midi_duration * beat_position_ratio)
                    
                    tied_timing[tied_note['id']] = {
                        'start_time': calculated_start,
                        'end_time': midi_end,  # All tied notes end together
                        'is_primary': False
                    }
    
    return tied_timing
```

### Phase 2: Coordinator Tool (`Synchronization/coordinator.py`)

**Purpose**: Pipeline orchestrator that manages both SVG and audio processing with synchronization

**Core Orchestration**:
```python
def coordinate_synchronized_pipeline(xml_file: str, svg_file: str, midi_file: str, 
                                   output_dir: str = "Synchronized_Output") -> str:
    """
    Run complete synchronized pipeline with parallel processing where safe
    """
    print("🎼 SYNCHRONIZED SIB2AE PIPELINE")
    print("=" * 50)
    
    # Phase 1: Context Analysis (Sequential - required for subsequent phases)
    context_file = f"{output_dir}/master_context.json"
    run_context_gatherer(xml_file, midi_file, svg_file, context_file)
    
    # Phase 2: Parallel Processing (SVG + Audio pipelines)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # SVG Pipeline (Enhanced with timing data)
        svg_future = executor.submit(run_enhanced_svg_pipeline, 
                                    xml_file, svg_file, context_file, output_dir)
        
        # Audio Pipeline (Standard processing)
        audio_future = executor.submit(run_audio_pipeline, 
                                     midi_file, output_dir)
        
        # Wait for both pipelines to complete
        svg_results = svg_future.result()
        audio_results = audio_future.result()
    
    # Phase 3: Final Synchronization (Merge SVG + Audio + Timing)
    master_json = create_master_synchronization_file(
        svg_results, audio_results, context_file, output_dir
    )
    
    # Phase 4: After Effects Project Generation (Optional)
    ae_project = generate_after_effects_project(master_json, output_dir)
    
    return master_json
```

**Enhanced SVG Pipeline**:
```python
def run_enhanced_svg_pipeline(xml_file: str, svg_file: str, 
                             context_file: str, output_dir: str) -> Dict:
    """
    Run SVG pipeline with enhanced timing metadata injection
    """
    # Load synchronization context
    with open(context_file, 'r') as f:
        context = json.load(f)
    
    # Run existing SVG tools with timing enhancement
    subprocess.run([
        'python', 'Separators/sib2ae_master_pipeline.py',
        xml_file, svg_file
    ])
    
    # Enhance individual noteheads with timing metadata
    enhance_svg_files_with_timing(context, output_dir)
    
    return {"status": "completed", "enhanced_svgs": True}
```

**Master Synchronization File Structure**:
```python
def create_master_synchronization_file(svg_results: Dict, audio_results: Dict, 
                                     context_file: str, output_dir: str) -> str:
    """
    Generate master JSON with complete synchronization data for After Effects
    """
    master_data = {
        "project_info": {
            "name": "Synchronized Sib2Ae Project",
            "xml_file": xml_file,
            "midi_file": midi_file,
            "total_duration_seconds": get_total_duration(context_file),
            "fps": 30,
            "created": datetime.now().isoformat()
        },
        "synchronized_notes": [],
        "after_effects": {
            "composition_settings": {
                "width": 1920,
                "height": 1080,
                "duration": get_total_duration(context_file),
                "fps": 30
            },
            "import_instructions": {
                "jsx_script": f"{output_dir}/ae_importer.jsx",
                "assets_directory": output_dir
            }
        }
    }
    
    # Load context and build synchronized note entries
    with open(context_file, 'r') as f:
        context = json.load(f)
    
    for note_relationship in context['note_relationships']:
        synchronized_note = {
            "note_id": note_relationship['xml_note']['id'],
            "instrument": note_relationship['xml_note']['part_name'],
            "pitch": note_relationship['xml_note']['pitch'],
            "measure": note_relationship['xml_note']['measure'],
            
            # MIDI Timing Data
            "midi_timing": {
                "start_seconds": note_relationship['midi_note']['start_time_seconds'],
                "end_seconds": note_relationship['midi_note']['end_time_seconds'],
                "velocity": note_relationship['midi_note']['velocity']
            },
            
            # After Effects Timing (30 FPS)
            "ae_timing": {
                "start_frame": int(note_relationship['midi_note']['start_time_seconds'] * 30),
                "end_frame": int(note_relationship['midi_note']['end_time_seconds'] * 30),
                "duration_frames": int((note_relationship['midi_note']['end_time_seconds'] - 
                                      note_relationship['midi_note']['start_time_seconds']) * 30)
            },
            
            # Asset References
            "assets": {
                "svg_files": note_relationship.get('svg_files', []),
                "audio_file": note_relationship.get('audio_file'),
                "keyframes_file": note_relationship.get('keyframes_file')
            },
            
            # Tied Note Information
            "tied_sequence": note_relationship.get('tied_sequence', {})
        }
        
        master_data['synchronized_notes'].append(synchronized_note)
    
    # Write master synchronization file
    master_file = f"{output_dir}/master_synchronization.json"
    with open(master_file, 'w') as f:
        json.dump(master_data, f, indent=2)
    
    print(f"✅ Master synchronization file created: {master_file}")
    return master_file
```

### Phase 3: After Effects Integration

**JSX Generator**:
```python
def generate_after_effects_project(master_json: str, output_dir: str) -> str:
    """
    Generate JSX script for automated After Effects project creation
    """
    jsx_content = '''
// Auto-generated After Effects import script
var jsonFile = new File("''' + master_json + '''");
jsonFile.open("r");
var jsonData = JSON.parse(jsonFile.read());
jsonFile.close();

// Create main composition
var comp = app.project.items.addComp(
    jsonData.project_info.name,
    jsonData.after_effects.composition_settings.width,
    jsonData.after_effects.composition_settings.height,
    1,
    jsonData.after_effects.composition_settings.duration,
    jsonData.after_effects.composition_settings.fps
);

// Import and position synchronized notes
for (var i = 0; i < jsonData.synchronized_notes.length; i++) {
    var note = jsonData.synchronized_notes[i];
    
    // Import SVG notehead
    var svgFile = new File(note.assets.svg_files[0]);
    var footage = app.project.importFile(new ImportOptions(svgFile));
    var layer = comp.layers.add(footage);
    
    // Set layer timing
    layer.startTime = note.ae_timing.start_frame / 30;
    layer.inPoint = note.ae_timing.start_frame / 30;
    layer.outPoint = note.ae_timing.end_frame / 30;
    
    // Apply keyframe data via expressions
    if (note.assets.keyframes_file) {
        var keyframeData = footage(note.assets.keyframes_file).sourceData;
        layer.transform.scale.expression = "thisComp.layer('" + note.assets.keyframes_file + "').sourceData.scale";
        layer.transform.opacity.expression = "thisComp.layer('" + note.assets.keyframes_file + "').sourceData.opacity";
    }
}
'''
    
    jsx_file = f"{output_dir}/ae_importer.jsx"
    with open(jsx_file, 'w') as f:
        f.write(jsx_content)
    
    return jsx_file
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Code quality validation
ruff check Synchronization/ --fix
mypy Synchronization/ --strict

# XML/JSON validation
python -c "import xml.etree.ElementTree as ET; ET.parse('Base/SS 9.musicxml')"
python -c "import json; json.load(open('Synchronized_Output/master_synchronization.json'))"
```

### Level 2: Unit Tests
```bash
# Create comprehensive test suite
uv run pytest tests/test_synchronization.py -v

# Test components:
# - XML tied note detection accuracy
# - MIDI timing conversion precision  
# - Note matching algorithm with various tolerance values
# - Tied note timing calculation correctness
# - Master JSON structure validation
```

### Level 3: Integration Test with Sample Data
```bash
# Test complete pipeline with Saint-Saëns Trio
python Synchronization/coordinator.py \
    "Base/SS 9.musicxml" \
    "Base/SS 9 full.svg" \
    "Base/Saint-Saens Trio No 2.mid" \
    "Test_Output"

# Validate outputs:
# - 9 noteheads properly matched to MIDI notes
# - Tied note sequences correctly identified  
# - Master JSON contains all required synchronization data
# - After Effects JSX script imports correctly
```

### Level 4: Performance Benchmark
```bash
# Measure processing time for various score sizes
time python Synchronization/coordinator.py [test_files]

# Performance targets:
# - Saint-Saëns Trio (9 notes): < 5 seconds
# - Medium score (50 notes): < 15 seconds  
# - Large score (100+ notes): < 30 seconds
```

### Level 5: After Effects Validation
```bash
# Test After Effects integration
# 1. Import master_synchronization.json into After Effects
# 2. Run generated JSX script
# 3. Verify synchronized animation playback
# 4. Check frame-accurate timing alignment
```

## File Structure

### New Directory Structure
```
Synchronization/                    # New synchronization tools
├── context_gatherer.py            # Standalone XML/MIDI/SVG analyzer  
├── coordinator.py                  # Pipeline orchestrator
├── xml_midi_matcher.py             # Core matching algorithms
├── tied_note_processor.py          # Tied note timing calculations
├── ae_project_generator.py         # After Effects JSX generation
└── __init__.py

Synchronized_Output/                # Generated synchronized output
├── master_synchronization.json    # Complete timing and asset data
├── ae_importer.jsx                 # After Effects import script
├── Symbolic_Separators/            # Enhanced SVG files with timing
├── Audio/                          # Audio files and keyframes
└── master_context.json             # Raw analysis data
```

### Dependencies
```python
# Additional imports needed
import xml.etree.ElementTree as ET  # XML processing (existing)
import mido                         # MIDI processing (existing)  
import json                         # JSON handling (standard library)
import concurrent.futures           # Parallel processing (standard library)
import subprocess                   # Pipeline orchestration (existing)
from datetime import datetime       # Timestamp generation (standard library)
from typing import Dict, List, Optional, Tuple  # Type hints (existing)
```

## Risk Mitigation

### High-Risk Areas
1. **Timing Precision Loss**: Multiple conversion steps (XML→MIDI→AE frames) may accumulate errors
   - **Mitigation**: Use integer arithmetic and validate against ground truth samples
   
2. **Complex Tied Note Sequences**: Edge cases with multiple ties in sequence  
   - **Mitigation**: Comprehensive test suite with complex musical examples
   
3. **Unquantized MIDI Variance**: Real performance data may not match XML timing
   - **Mitigation**: Configurable tolerance and fallback matching strategies

4. **Large Score Performance**: Memory and processing time for orchestral works
   - **Mitigation**: Streaming processing and parallel execution where possible

### Fallback Strategies
- Graceful degradation when note matching fails (log and continue)
- Default timing calculation when MIDI data is unavailable
- Manual override capabilities in master JSON for edge cases

## Success Metrics

### Quantitative Goals
- **Accuracy**: 95%+ successful note matching for typical scores
- **Performance**: Process 100-note scores in under 30 seconds
- **Precision**: Frame-accurate synchronization (±1 frame at 30 FPS)
- **Coverage**: Support both quantized and unquantized MIDI sources

### Qualitative Goals  
- **Workflow Integration**: Seamless addition to existing Sib2Ae pipeline
- **User Experience**: One-command synchronized output generation
- **Flexibility**: Configurable parameters for different use cases
- **Maintainability**: Clear separation of concerns and comprehensive testing

This PRP provides a comprehensive foundation for implementing synchronized music animation capabilities that bridge the gap between musical notation, MIDI performance data, and professional motion graphics workflows.

**PRP Confidence Score: 9/10** - Comprehensive research, detailed implementation plan, executable validation gates, and clear success criteria provide strong foundation for one-pass implementation success.