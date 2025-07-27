name: "MIDI-SVG Synchronization System with Tied Note Handling"
description: |

## Purpose

Comprehensive PRP for implementing a MIDI-SVG synchronization system that merges symbolic (SVG noteheads) and audio (MIDI keyframes) pipelines to create perfectly timed After Effects animations with proper tied note handling and tolerance-based matching for both quantized and unquantized MIDI.

## Core Principles

1. **MusicXML-First Approach**: Use MusicXML as source of truth for note relationships and tie detection
2. **Tolerance-Based Matching**: Support unquantized MIDI with configurable timing tolerance (100ms default)
3. **Tied Note Intelligence**: Handle complex tied note sequences with proper timing calculation
4. **After Effects Integration**: Generate frame-accurate timing compatible with 30 FPS AE workflow

---

## Goal

Create a synchronization system that:
- Matches individual SVG noteheads with corresponding MIDI notes and keyframe data
- Handles tied notes by creating logical note groups with proper timing
- Supports both quantized and unquantized MIDI workflows
- Outputs After Effects-compatible JSON with precise timing synchronization
- Maintains pixel-perfect coordination between visual and audio elements

## Why

- **User Value**: Enable automated music animation creation with professional timing accuracy
- **Pipeline Integration**: Merge existing symbolic and audio pipelines into unified workflow  
- **Tied Note Support**: Handle complex musical notation that current system ignores
- **Performance Scaling**: Support unquantized MIDI for realistic performance animation

## What

A two-tool synchronization system in new `Pipeline/` directory:
1. **context_gatherer.py**: XML-MIDI matcher that creates relationship mappings
2. **coordinator.py**: Master pipeline orchestrator that produces synchronized outputs

### Success Criteria

- [ ] XML-MIDI note matching with 95%+ accuracy for test scores
- [ ] Tied note sequences properly grouped and timed
- [ ] Unquantized MIDI matching within 100ms tolerance
- [ ] After Effects JSON imports with frame-accurate timing
- [ ] All existing pipeline functionality preserved

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- url: https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/tie/
  why: Official MusicXML tie element specification for proper tie detection

- url: https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/tied/
  why: Logical tie elements vs notational tie elements distinction

- url: https://mido.readthedocs.io/en/latest/midi_files.html
  why: MIDI timing extraction and tick-to-seconds conversion patterns

- url: https://ae-scripting.docsforadobe.dev/properties/property/
  why: After Effects keyframe format and timing requirements

- url: https://link.springer.com/article/10.1007/s11042-014-2136-6
  why: Audio-visual synchronization tolerance research (100ms+ tolerance acceptable)

- file: Separators/truly_universal_noteheads_extractor.py
  why: Existing MusicXML parsing patterns and coordinate transformation system

- file: Audio Separators/midi_note_separator.py
  why: MIDI processing patterns and note ID generation system

- file: Audio Separators/audio_to_keyframes_fast.py
  why: After Effects JSON keyframe format and 30 FPS timing

- docfile: PRPs/ai_docs/svg_coordinate_preservation_guide.md
  why: Universal coordinate system and pixel-perfect positioning requirements
```

### Current Codebase Tree

```bash
/Users/colinmignot/Claude Code/Sib2Ae/PRPs-agentic-eng/
├── Audio Separators/           # Audio processing pipeline
│   ├── midi_note_separator.py      # MIDI → individual notes  
│   ├── midi_to_audio_renderer_fast.py  # MIDI → WAV (parallel)
│   └── audio_to_keyframes_fast.py      # WAV → AE keyframes
├── Separators/                 # SVG processing pipeline  
│   ├── truly_universal_noteheads_extractor.py  # XML → SVG noteheads
│   ├── xml_based_instrument_separator.py      # Instrument separation
│   └── truly_universal_noteheads_subtractor.py # Remove noteheads
├── Base/                       # Input files
│   ├── SS 9.musicxml              # MusicXML source
│   ├── SS 9 full.svg             # Complete SVG score
│   └── Saint-Saens Trio No 2.mid  # MIDI source
├── Symbolic Separators/        # SVG outputs organized by instrument
│   └── {Instrument}/individual_noteheads/
└── Audio/                      # Audio outputs and keyframes
    ├── {Instrument}/*.wav
    └── Keyframes/{Instrument}/*.json
```

### Desired Codebase Tree with New Files

```bash
Pipeline/                       # NEW: Synchronization system
├── context_gatherer.py            # XML-MIDI matcher with tie detection
├── coordinator.py                 # Master pipeline orchestrator  
├── tied_note_processor.py         # Tied note grouping and timing
├── tolerance_matcher.py           # Unquantized MIDI matching
└── ae_sync_generator.py           # After Effects JSON output
```

### Known Gotchas of Codebase & Library Quirks

```python
# CRITICAL: MusicXML namespace handling
import xml.etree.ElementTree as ET
ET.register_namespace('', 'http://www.w3.org/2000/svg')  # Required before parsing

# CRITICAL: Coordinate transformation constants (universal across codebase)
X_SCALE = 3.206518      # Pixel scaling factor - DO NOT CHANGE
X_OFFSET = 564.93       # Pixel offset - DO NOT CHANGE  
FLUTE_BASE_Y = 1037     # Upper staff Y position
VIOLIN_BASE_Y = 1417    # Lower staff Y position

# CRITICAL: Note ID generation must be sequential across entire score
# Current: note_000, note_001, note_002... (3-digit zero-padded)
# Both pipelines use this pattern - maintain consistency

# CRITICAL: Helsinki Special Std notehead codes
# Code 70 (\u0046): Hollow noteheads (half/whole notes)
# Code 102 (\u0066): Filled noteheads (quarter/eighth/sixteenth notes)

# CRITICAL: After Effects timing at 30 FPS
# Frame = round(seconds * 30.0)
# Timing precision limited to 1/30th second (33.33ms)

# GOTCHA: No existing tie detection in codebase
# XML contains <tie type="start/stop"> but completely ignored
# Must implement from scratch following W3C specification

# GOTCHA: MIDI timing uses ticks, XML uses beats
# Conversion: seconds = (ticks / ppq) * (60.0 / bpm)
# Must handle tempo changes throughout score
```

## Implementation Blueprint

### Data Models and Structure

Core data models ensuring type safety and consistency across synchronization system.

```python
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from enum import Enum

@dataclass 
class NoteIdentity:
    """Unique note identification across all formats"""
    id: str                    # "000", "001", "002"...
    part_id: str              # "P1", "P2"...  
    instrument: str           # "Flûte", "Violon"...
    pitch: str                # "A4", "B3", "C4"...
    measure: int              # 4, 5, 6...
    
@dataclass
class TieInfo:
    """Tie relationship data from MusicXML"""
    type: str                 # "start", "stop", "continue"
    tied_type: str           # "start", "stop" (logical ties)
    is_tie_start: bool
    is_tie_stop: bool
    
@dataclass
class TimingData:
    """Comprehensive timing information"""
    midi_start_seconds: float       # Absolute MIDI timing
    midi_end_seconds: float         # MIDI note duration
    xml_beat_position: float        # Beat within measure
    calculated_start_seconds: float # For tied notes
    ae_start_frame: int            # 30 FPS frame number
    ae_end_frame: int              # End frame
    
@dataclass
class SynchronizedNote:
    """Complete note with all synchronization data"""
    identity: NoteIdentity
    timing: TimingData
    tie_info: Optional[TieInfo]
    svg_file: str                  # Path to individual notehead SVG
    audio_file: str               # Path to WAV audio file  
    keyframes_file: str           # Path to AE keyframes JSON
    svg_coordinates: tuple[float, float]  # (x, y) pixel position
    midi_velocity: int            # 0-127 MIDI velocity
```

### List of Tasks to be Completed

```yaml
Task 1:
CREATE Pipeline/context_gatherer.py:
  - IMPLEMENT parse_musicxml_with_ties() following existing pattern in Separators/
  - DETECT <tie> and <tied> elements using W3C MusicXML specification
  - EXTRACT beat positions, measure numbers, pitch data 
  - BUILD comprehensive note index with tie relationships
  - MIRROR error handling patterns from existing XML parsers

Task 2:  
CREATE Pipeline/tied_note_processor.py:
  - IMPLEMENT group_tied_notes() for complex tie chains
  - CALCULATE proportional timing for tied-to notes using beat positions
  - HANDLE cross-measure ties and tempo changes
  - PRESERVE first note as primary, others as visual-only
  - FOLLOW timing calculation patterns from research

Task 3:
CREATE Pipeline/tolerance_matcher.py:
  - IMPLEMENT xml_midi_matcher() with configurable tolerance (100ms default)
  - MATCH by pitch + instrument + timing within tolerance
  - RESOLVE conflicts by selecting closest timing match
  - LOG unmatched notes and tolerance exceeded cases
  - SUPPORT both quantized and unquantized MIDI workflows

Task 4:
CREATE Pipeline/ae_sync_generator.py:
  - GENERATE After Effects JSON with precise 30 FPS timing
  - EMBED visual appearance timing and audio onset timing  
  - FOLLOW keyframe format from Audio Separators/audio_to_keyframes_fast.py
  - INCLUDE note start times, durations, and coordinate data
  - OPTIMIZE for minimal clicks AE import workflow

Task 5:
CREATE Pipeline/coordinator.py:
  - ORCHESTRATE complete synchronization pipeline
  - EXECUTE both symbolic and audio pipelines in parallel
  - COORDINATE timing data between all processing stages
  - OUTPUT master synchronization JSON for AE import
  - MAINTAIN backward compatibility with existing workflows

Task 6:
ENHANCE Separators/truly_universal_noteheads_extractor.py:
  - MODIFY extract_xml_notes() to capture tie information
  - ADD tie detection to existing parsing loop
  - PRESERVE all existing functionality and patterns
  - EXTEND note data structure with tie fields

Task 7:
ENHANCE Audio Separators/midi_note_separator.py:
  - MODIFY to accept pre-generated note index from context_gatherer
  - MAINTAIN sequential ID generation for backward compatibility
  - PRESERVE MIDI timing data for synchronization correlation
  - ADD tempo map extraction for accurate timing conversion
```

### Per Task Pseudocode

```python
# Task 1: Context Gatherer
def parse_musicxml_with_ties(musicxml_file: str) -> Dict[str, Any]:
    # PATTERN: Follow existing XML parsing in Separators/
    tree = ET.parse(musicxml_file)
    root = tree.getroot()
    
    notes_with_ties = []
    note_counter = 0
    
    for part in root.findall('part'):
        part_id = part.get('id')
        cumulative_x = 0
        
        for measure in part.findall('measure'):
            measure_num = int(measure.get('number'))
            
            for note in measure.findall('note'):
                if note.find('rest') is not None:
                    continue
                    
                # EXISTING PATTERN: Extract pitch and coordinates
                pitch_data = extract_pitch_info(note)
                coordinates = extract_coordinates(note, cumulative_x)
                
                # NEW: Extract tie information
                tie_elements = note.findall('tie')
                tied_elements = note.findall('notations/tied')
                tie_info = build_tie_info(tie_elements, tied_elements)
                
                # BUILD comprehensive note record
                note_record = {
                    'id': f"{note_counter:03d}",
                    'part_id': part_id,
                    'measure': measure_num,
                    'tie_info': tie_info,
                    **pitch_data,
                    **coordinates
                }
                notes_with_ties.append(note_record)
                note_counter += 1
    
    return {'notes': notes_with_ties, 'tie_groups': group_tied_notes(notes_with_ties)}

# Task 3: Tolerance Matcher  
def match_xml_midi_with_tolerance(xml_notes: List, midi_notes: List, tolerance_ms: int = 100) -> List:
    matches = []
    used_midi_indices = set()
    
    for xml_note in xml_notes:
        candidates = []
        
        for midi_idx, midi_note in enumerate(midi_notes):
            if midi_idx in used_midi_indices:
                continue
                
            # CRITICAL: Exact pitch match required
            if midi_note['pitch'] != xml_note['pitch']:
                continue
                
            # CRITICAL: Instrument/part match required  
            if not instruments_match(midi_note['instrument'], xml_note['part_id']):
                continue
                
            # TOLERANCE: Check timing within threshold
            time_diff_ms = abs(midi_note['start_ms'] - xml_note['expected_start_ms'])
            if time_diff_ms <= tolerance_ms:
                candidates.append((midi_idx, midi_note, time_diff_ms))
        
        # SELECT closest match
        if candidates:
            best_idx, best_midi, time_error = min(candidates, key=lambda x: x[2])
            matches.append({
                'xml_note': xml_note,
                'midi_note': best_midi, 
                'time_error_ms': time_error
            })
            used_midi_indices.add(best_idx)
            
    return matches

# Task 4: After Effects Sync Generator
def generate_ae_sync_json(synchronized_notes: List[SynchronizedNote]) -> Dict:
    # PATTERN: Follow AE JSON format from audio_to_keyframes_fast.py
    ae_data = {
        "composition": {
            "name": f"Synchronized_Music_Animation",
            "frameRate": 30,
            "duration": max(note.timing.ae_end_frame for note in synchronized_notes) / 30.0
        },
        "layers": []
    }
    
    for note in synchronized_notes:
        # TIMING: Convert seconds to 30 FPS frames
        start_frame = round(note.timing.calculated_start_seconds * 30.0)
        end_frame = round(note.timing.midi_end_seconds * 30.0)
        
        layer_data = {
            "name": note.identity.id,
            "sourcePath": note.svg_file,
            "startTime": note.timing.calculated_start_seconds,
            "duration": note.timing.midi_end_seconds - note.timing.calculated_start_seconds,
            "properties": {
                "position": {
                    "keyframes": [[start_frame, list(note.svg_coordinates)]]
                },
                "scale": load_keyframes_from_audio(note.keyframes_file, "scale"),
                "opacity": load_keyframes_from_audio(note.keyframes_file, "opacity")
            }
        }
        ae_data["layers"].append(layer_data)
    
    return ae_data
```

### Integration Points

```yaml
FILE_STRUCTURE:
  - create: Pipeline/ directory for new synchronization tools
  - preserve: All existing Separators/ and "Audio Separators/" functionality
  - extend: Existing tools to capture additional tie and timing data

COORDINATE_SYSTEM:
  - maintain: Universal coordinate transformation constants  
  - preserve: Staff position mappings and pixel-perfect accuracy
  - extend: Coordinate data with timing synchronization

TIMING_SYSTEM:
  - integrate: MIDI ticks-to-seconds conversion with MusicXML beat positions
  - support: Both quantized and unquantized MIDI workflows
  - target: 30 FPS After Effects frame-accurate timing

ID_GENERATION:
  - unify: Sequential note ID system across both pipelines
  - preserve: Existing 3-digit zero-padded format (000, 001, 002...)
  - coordinate: ID generation from single source (MusicXML) for consistency
```

## Validation Loop

### Level 1: Syntax & Style

```bash
# Run these FIRST - fix any errors before proceeding
ruff check Pipeline/ --fix          # Auto-fix style issues
mypy Pipeline/                      # Type checking for new modules

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests

```python
# CREATE test_synchronization_system.py with comprehensive test cases:

def test_tie_detection_accuracy():
    """Verify tie elements properly detected from MusicXML"""
    xml_file = "Base/SS 9.musicxml"
    notes = parse_musicxml_with_ties(xml_file)
    
    # Test for known tied notes in SS 9.musicxml
    tied_notes = [n for n in notes['notes'] if n['tie_info']['is_tie_start']]
    assert len(tied_notes) >= 2  # Known tied sequences in test file
    
def test_midi_xml_matching_tolerance():
    """Test tolerance-based matching with known timing variations"""
    xml_notes = [{"pitch": "A4", "expected_start_ms": 1000}]
    midi_notes = [{"pitch": "A4", "start_ms": 1050}]  # 50ms difference
    
    matches = match_xml_midi_with_tolerance(xml_notes, midi_notes, tolerance_ms=100)
    assert len(matches) == 1
    assert matches[0]['time_error_ms'] == 50

def test_ae_frame_timing_accuracy():
    """Verify 30 FPS frame timing calculations"""
    note = create_test_synchronized_note(start_seconds=1.0, end_seconds=2.0)
    ae_json = generate_ae_sync_json([note])
    
    layer = ae_json['layers'][0]
    assert layer['startTime'] == 1.0
    assert layer['duration'] == 1.0
    
def test_tied_note_timing_calculation():
    """Test proportional timing for tied note sequences"""
    tied_group = create_test_tied_sequence()  # 3-note tied sequence
    processed = calculate_tied_note_timing(tied_group)
    
    # First note gets actual MIDI timing
    assert processed[0]['timing']['calculated_start_seconds'] == processed[0]['timing']['midi_start_seconds']
    
    # Subsequent notes get proportional timing
    assert processed[1]['timing']['calculated_start_seconds'] > processed[0]['timing']['calculated_start_seconds']
    assert processed[2]['timing']['calculated_start_seconds'] > processed[1]['timing']['calculated_start_seconds']

def test_coordinate_preservation():
    """Ensure universal coordinate system maintained"""
    svg_coords = extract_svg_coordinates("Symbolic Separators/Flute/individual_noteheads/notehead_000_P1_A4_M4.svg")
    xml_coords = extract_xml_coordinates("Base/SS 9.musicxml", note_id="000")
    
    # Verify coordinate transformation accuracy (within 1 pixel)
    assert abs(svg_coords[0] - xml_coords[0]) <= 1.0
    assert abs(svg_coords[1] - xml_coords[1]) <= 1.0
```

```bash
# Run and iterate until passing:
uv run pytest test_synchronization_system.py -v
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Test

```bash
# Test complete synchronization workflow
cd /Users/colinmignot/Claude\ Code/Sib2Ae/PRPs-agentic-eng/

# Run complete synchronization pipeline
python Pipeline/coordinator.py "Base/SS 9.musicxml" "Base/SS 9 full.svg" "Base/Saint-Saens Trio No 2.mid"

# Expected outputs:
# - Pipeline/synchronized_output/master_sync.json
# - Pipeline/synchronized_output/ae_import.json
# - All existing Separators/ and Audio Separators/ outputs preserved

# Verify timing accuracy
python -c "
import json
with open('Pipeline/synchronized_output/master_sync.json') as f:
    data = json.load(f)
print(f'Notes synchronized: {len(data[\"synchronized_notes\"])}')
print(f'Tie groups detected: {len(data[\"tie_groups\"])}')
print(f'Timing accuracy: {data[\"metrics\"][\"avg_error_ms\"]}ms')
"

# Expected: 6 notes synchronized (matching test files), <50ms average error
```

### Level 4: After Effects Validation

```bash
# Validate After Effects import compatibility
# 1. Copy generated ae_import.json to AE script location
cp Pipeline/synchronized_output/ae_import.json ~/Desktop/test_ae_import.json

# 2. Test import script (create basic AE JSX for validation)
cat > ~/Desktop/test_import.jsx << 'EOF'
var jsonFile = new File("~/Desktop/test_ae_import.json");
jsonFile.open("r");
var importData = JSON.parse(jsonFile.read());
jsonFile.close();

var comp = app.project.items.addComp(
    importData.composition.name,
    1920, 1080, 1.0,
    importData.composition.duration,
    importData.composition.frameRate
);

alert("Import successful: " + importData.layers.length + " layers created");
EOF

# 3. Manual validation in After Effects
# - Open After Effects
# - Run test_import.jsx script
# - Verify timing accuracy and layer organization
```

## Final Validation Checklist

- [ ] All tests pass: `uv run pytest test_synchronization_system.py -v`
- [ ] No linting errors: `uv run ruff check Pipeline/`
- [ ] No type errors: `uv run mypy Pipeline/`
- [ ] Integration test successful: Coordinator produces synchronized output
- [ ] Tie detection working: Known tied notes properly grouped
- [ ] MIDI matching accurate: <100ms tolerance achieved for unquantized
- [ ] AE import functional: JSON format compatible with After Effects
- [ ] Existing pipelines preserved: All current functionality maintained
- [ ] Performance acceptable: Processing time <2x current pipeline duration

## Anti-Patterns to Avoid

- ❌ Don't modify existing coordinate transformation constants - they're calibrated
- ❌ Don't change sequential note ID format - both pipelines depend on it  
- ❌ Don't ignore tie detection errors - log and handle gracefully
- ❌ Don't hardcode timing tolerance - make it configurable for different use cases
- ❌ Don't break existing file naming conventions - maintain backward compatibility
- ❌ Don't skip frame rate conversion - After Effects requires precise 30 FPS timing
- ❌ Don't assume MIDI and XML note order matches - use tolerance-based matching

## Confidence Score

**9/10** - High confidence for one-pass implementation success due to:
✅ Comprehensive codebase analysis with specific patterns identified
✅ Extensive research on MusicXML, MIDI, and AE integration standards  
✅ Clear implementation blueprint with proven patterns from existing code
✅ Robust validation framework with multiple testing levels
✅ Well-defined data structures and tolerance algorithms from academic research
✅ Existing infrastructure provides solid foundation for synchronization

Risk mitigation through iterative validation and preservation of existing functionality ensures robust implementation path.