# PRP: Synchronized Music Animation System for After Effects

## Goal

Build a comprehensive MIDI-to-SVG synchronization system that matches individual noteheads from the symbolic separators with their corresponding MIDI notes and keyframe data, enabling frame-accurate music animations in After Effects. **CRITICAL**: The system must preserve timing integrity from the **master MIDI file before extraction** and handle tied notes where the number of MIDI notes differs from visual noteheads (e.g., 3 noteheads for 1 MIDI note in tied sequences). Each notehead must have start times that correspond exactly to the MIDI note timing in seconds from the original master MIDI.

## Why

- **Creative Innovation**: Enable frame-accurate music visualizations where each notehead animates precisely with its corresponding audio
- **Professional Workflow**: Bridge the gap between musical notation (symbolic) and audio processing (temporal) for production-ready After Effects integration
- **Musical Accuracy**: Handle complex musical concepts like tied notes that create visual-temporal mismatches (3 noteheads for 1 MIDI note in tied sequences)
- **Unquantized Support**: Handle real performance data with timing tolerance matching for professional music production

## What

Create a synchronization system with two new tools in a `Synchronizer/` directory:

1. **`context_gatherer.py`**: Early analysis tool that creates XML-MIDI-SVG relationships before pipeline execution
2. **`synchronization_coordinator.py`**: Master orchestrator that coordinates both pipelines and generates the final synchronized output

### Success Criteria

- [ ] **Master MIDI timing preserved**: All timing calculations reference the original master MIDI file before note extraction
- [ ] **Tied note mismatch handled**: Properly manage cases where 3 noteheads correspond to 1 MIDI note in tied sequences
- [ ] **Pipeline merge strategy**: Both symbolic and audio pipelines merge at the end with coordinated timing
- [ ] **Individual notehead timing**: Each SVG notehead has start time in seconds corresponding to correct MIDI note
- [ ] **Keyframe correlation**: Each notehead linked to corresponding keyframe data from audio analysis
- [ ] **MIDI-to-notehead matching**: 100ms tolerance for unquantized MIDI (configurable) with >95% accuracy
- [ ] **After Effects integration**: Final JSON format importable with correct start times for each object
- [ ] **Execution flexibility**: Support both sequential ("audio symbolic separators first") and parallel pipeline execution
- [ ] **Backward compatibility**: Existing pipeline functionality remains completely unchanged

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- url: https://www.w3.org/2021/06/musicxml40/
  why: Official MusicXML 4.0 specification for tied note processing

- url: https://ae-scripting.docsforadobe.dev/
  why: After Effects ExtendScript documentation for automated project creation

- url: https://mido.readthedocs.io/en/latest/
  why: MIDI processing library for tick-to-seconds conversion and tempo map handling

- file: /Separators/truly_universal_noteheads_extractor.py
  why: Current XML processing patterns, coordinate system, and notehead extraction logic

- file: /Audio Separators/midi_note_separator.py
  why: Current MIDI processing patterns, note separation, and file naming conventions

- file: /Audio Separators/audio_to_keyframes_fast.py
  why: Current keyframe generation format and After Effects compatibility patterns

- doc: https://www.midi.org/specifications/midi1-specifications/standard-midi-files-smf
  section: Timing and Tick Resolution
  critical: PPQ (Pulses Per Quarter Note) and tempo map handling for accurate timing

- file: /CLAUDE.md
  why: Universal coordinate system, Helsinki Special Std font codes, and pipeline architecture
```

### Current Codebase Structure

```bash
/
├── Base/                                      # Input files
│   ├── SS 9.musicxml                         # MusicXML score data
│   ├── SS 9 full.svg                         # Complete SVG score
│   └── Saint-Saens Trio No 2.mid             # MIDI source file
├── Separators/                               # SVG Processing Pipeline
│   ├── truly_universal_noteheads_extractor.py    # Extract noteheads from MusicXML
│   ├── xml_based_instrument_separator.py         # Separate instruments
│   └── individual_noteheads_creator.py           # Create individual notehead files
├── Audio Separators/                         # Audio Processing Pipeline
│   ├── midi_note_separator.py                    # Split MIDI into individual notes
│   ├── midi_to_audio_renderer_fast.py            # Convert MIDI to audio (optimized)
│   └── audio_to_keyframes_fast.py                # Generate AE keyframes (optimized)
├── Audio/                                    # Audio output directory
│   ├── [Instrument]/                             # Audio files by instrument
│   └── Keyframes/                                # After Effects keyframe JSON files
└── pyproject.toml                           # Python dependencies and project config
```

### Desired Codebase Structure with New Files

```bash
/
├── Synchronizer/                             # NEW: Synchronization system
│   ├── context_gatherer.py                      # Early XML/MIDI/SVG analysis
│   ├── synchronization_coordinator.py           # Master pipeline orchestrator  
│   ├── utils/
│   │   ├── xml_temporal_parser.py                # MusicXML timing & tied notes
│   │   ├── midi_matcher.py                       # Tolerance-based MIDI matching
│   │   ├── tied_note_processor.py                # Tied note relationship handling
│   │   └── ae_integration.py                     # After Effects JSX generation
│   └── outputs/
│       ├── master_synchronization.json           # Final synchronized data
│       └── ae_import_script.jsx                  # AE automation script
├── [All existing directories unchanged]
```

### Known Gotchas & Library Quirks

```python
# CRITICAL: Master MIDI timing integrity preservation
# Extract ALL timing data from original MIDI BEFORE running note separation
# The midi_note_separator.py process must not alter original timing relationships
# Store master timing as authoritative reference for all synchronization

# CRITICAL: Pipeline execution order dependencies
# Option 1: Sequential - "audio symbolic separators first" then audio separators
# Option 2: Parallel - coordinate both pipelines with shared timing reference
# Must maintain timing consistency regardless of execution approach

# CRITICAL: Tied note visual-temporal mismatch
# XML shows tied relationships, MIDI consolidates into single note event
# 3 visual noteheads = 1 MIDI note in complex tied sequences
# First notehead gets MIDI timing, others get calculated approximations

# CRITICAL: MusicXML tied note detection requires both <tie> and <tied> elements
# <tie> affects MIDI timing, <tied> affects visual notation
# Must process both to understand complete tied note relationships

# CRITICAL: mido library timing conversion from master MIDI
# tick_to_seconds = (tick / ticks_per_beat) * (60 / tempo_bpm)
# Tempo can change mid-piece, requires tempo map tracking
# PRESERVE original timing calculations before note extraction

# CRITICAL: SVG coordinate system uses absolute pixels
# Staff ranges: Staff 0: Y 950-1100, Staff 1: Y 1250-1500, etc.
# Filter out Y values < 100 to avoid opacity conflicts

# CRITICAL: Helsinki Special Std font noteheads
# Code 70: '\u0046' (hollow), Code 102: '\u0066' (filled)
# Must preserve exact font family and character codes

# CRITICAL: After Effects keyframe format with start times
# [[frame_number, value], [frame_number, value], ...]
# Frame rate: 30 FPS, values: 0-100 normalized range
# Each notehead object needs start time in seconds from master MIDI

# GOTCHA: ProcessPoolExecutor for parallel processing
# Current audio processing achieves 8x speedup
# Must maintain this performance while adding synchronization
# Coordinate parallel execution with shared timing reference

# GOTCHA: xml.etree.ElementTree namespace handling
# Always preserve {http://www.w3.org/2000/svg} namespaces
# Never use text-based line processing for SVG manipulation
```

## Implementation Blueprint

### Data Models and Structure

Create core data models for synchronization with type safety and validation.

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from pathlib import Path

@dataclass
class MusicXMLNote:
    """Complete note representation from MusicXML analysis"""
    pitch: str              # "A4", "C#3", etc.
    duration: int           # In divisions units
    beat_position: float    # Position within measure
    measure_number: int     # Measure location
    part_id: str           # Instrument/part identifier
    voice: Optional[int]    # Voice within part
    tie_type: Optional[str] # "start", "stop", "continue", None
    tied_group_id: Optional[str] # Unique ID for tied note groups
    onset_time: float      # Cumulative time from start of piece

@dataclass
class MIDINote:
    """MIDI note representation with precise timing"""
    pitch: int              # MIDI note number (60 = C4)
    velocity: int           # 0-127
    start_time: float       # Seconds from start of MIDI
    end_time: float         # End time in seconds
    channel: int            # MIDI channel
    instrument: str         # Derived instrument name

@dataclass
class SVGNotehead:
    """SVG notehead with coordinate and file information"""
    file_path: Path         # Path to individual notehead SVG
    element_id: str         # SVG element identifier
    coordinates: Tuple[float, float]  # (x, y) pixel coordinates
    staff_number: int       # Which staff (0, 1, 2, 3)
    instrument: str         # Derived from staff position

@dataclass
class MasterMIDITiming:
    """Timing data extracted from original master MIDI before note separation"""
    master_midi_path: Path          # Original MIDI file path
    tempo_map: List[Tuple[float, float]]  # (time_seconds, bpm) pairs
    total_duration_seconds: float   # Total piece duration
    ppq: int                       # Pulses per quarter note
    note_events: List[Dict]        # All note events with original timing

@dataclass
class SynchronizedNote:
    """Complete synchronized note with all timing and visual data"""
    note_id: str            # Unique identifier
    xml_note: MusicXMLNote
    midi_note: MIDINote
    svg_noteheads: List[SVGNotehead]  # Multiple for tied notes
    keyframes_file: Path    # Path to corresponding keyframe JSON
    master_start_time_seconds: float   # From original master MIDI
    master_end_time_seconds: float     # From original master MIDI
    calculated_start_time_seconds: float  # For tied notes (approximated)
    is_tied_primary: bool   # True if this is the animating note in tied group
    tied_group_id: Optional[str]  # Links tied notes together
```

### List of Tasks to be Completed (Implementation Order)

```yaml
Task 0: Extract Master MIDI Timing Reference
CREATE Synchronizer/utils/master_midi_extractor.py:
  - EXTRACT timing data from original master MIDI BEFORE any note separation
  - CREATE MasterMIDITiming object with tempo map and note events
  - PRESERVE original timing relationships as authoritative reference
  - IMPLEMENT tempo change detection and duration calculation

Task 1: Create Synchronizer Directory Structure
CREATE Synchronizer/:
  - Initialize directory with proper structure
  - Create utils/ subdirectory
  - Create outputs/ subdirectory
  - Add __init__.py files for proper Python modules

Task 2: Implement XML Temporal Parser
CREATE Synchronizer/utils/xml_temporal_parser.py:
  - MIRROR pattern from: Separators/truly_universal_noteheads_extractor.py
  - ADD tied note detection using <tie> and <tied> elements
  - ADD beat position calculation using <divisions>
  - ADD tempo extraction from <metronome> markings
  - IMPLEMENT note grouping for tied sequences

Task 3: Implement MIDI Matching Engine
CREATE Synchronizer/utils/midi_matcher.py:
  - MIRROR pattern from: Audio Separators/midi_note_separator.py
  - ADD tolerance-based matching (default 100ms, configurable)
  - ADD pitch + timing + instrument matching algorithm
  - IMPLEMENT confidence scoring for match quality
  - ADD support for unquantized MIDI variations

Task 4: Implement Tied Note Processor
CREATE Synchronizer/utils/tied_note_processor.py:
  - IMPLEMENT tied note relationship detection
  - ADD beat position to seconds conversion
  - ADD tied group duration calculation
  - IMPLEMENT start time approximation for tied-to notes

Task 5: Implement Context Gatherer (Core Analysis)
CREATE Synchronizer/context_gatherer.py:
  - INTEGRATE xml_temporal_parser for MusicXML analysis
  - INTEGRATE midi_matcher for MIDI event extraction
  - ADD SVG coordinate analysis using existing patterns
  - CREATE master relationship mapping JSON
  - ADD validation and error reporting

Task 6: Implement Synchronization Coordinator
CREATE Synchronizer/synchronization_coordinator.py:
  - ORCHESTRATE existing pipeline execution with master MIDI timing reference
  - IMPLEMENT execution modes: sequential ("audio symbolic separators first") OR parallel
  - COORDINATE both pipelines to merge at the end with consistent timing
  - INTEGRATE context gathering as preprocessing with master timing
  - MAINTAIN parallel processing efficiency with shared timing reference
  - ADD progress tracking and error handling
  - PRESERVE all existing tool outputs unchanged

Task 7: Implement After Effects Integration
CREATE Synchronizer/utils/ae_integration.py:
  - MIRROR keyframe format from: Audio Separators/audio_to_keyframes_fast.py
  - ADD JSX script generation for automated AE import with master MIDI timing
  - IMPLEMENT layer timing and start time setting from master timing reference
  - CREATE After Effects objects with start times matching MIDI note timing in seconds
  - ADD composition creation and asset organization
  - ENSURE each notehead object has correct start time from master MIDI

Task 8: Create Final Output Generator
CREATE Synchronizer/outputs/ generation:
  - COMBINE all pipeline outputs into master JSON
  - GENERATE After Effects import script
  - CREATE validation report with accuracy metrics
  - ADD documentation and usage examples

Task 9: Add CLI Integration
MODIFY existing workflow:
  - ADD command line interface for new synchronization mode
  - MAINTAIN backward compatibility with existing commands
  - ADD optional synchronization parameters
  - IMPLEMENT legacy mode fallback

Task 10: Comprehensive Testing and Validation
CREATE test suite:
  - UNIT tests for each utility module
  - INTEGRATION tests for full pipeline
  - PERFORMANCE tests to ensure no regression
  - ACCURACY tests with known musical examples
```

### Per Task Pseudocode 

```python
# Task 2: XML Temporal Parser Implementation
class XMLTemporalParser:
    def __init__(self, musicxml_path: Path):
        # PATTERN: Use xml.etree.ElementTree like existing tools
        self.tree = ET.parse(musicxml_path)
        self.root = self.tree.getroot()
        
    def extract_tied_notes(self) -> Dict[str, List[MusicXMLNote]]:
        # CRITICAL: Process both <tie> and <tied> elements
        # <tie type="start/stop"> affects timing
        # <tied type="start/stop"> affects notation
        tied_groups = {}
        
        for part in self.root.findall('.//part'):
            for measure in part.findall('measure'):
                for note in measure.findall('note'):
                    tie_elem = note.find('tie')
                    if tie_elem is not None:
                        # PATTERN: Group tied notes by pitch + voice
                        group_id = self._create_tie_group_id(note, measure)
                        # Add to tied_groups tracking
        
        return tied_groups
    
    def calculate_beat_position(self, note_elem, measure_elem) -> float:
        # CRITICAL: Extract <divisions> for timing resolution
        divisions = int(measure_elem.find('attributes/divisions').text)
        
        # Calculate cumulative position within measure
        cumulative_duration = 0
        for prev_note in measure_elem.findall('note'):
            if prev_note == note_elem:
                break
            duration = int(prev_note.find('duration').text)
            cumulative_duration += duration
            
        # Convert to beat position (1-based)
        beat_position = (cumulative_duration / divisions) + 1
        return beat_position

# Task 3: MIDI Matcher Implementation  
class MIDIMatcher:
    def __init__(self, tolerance_ms: float = 100.0):
        # CRITICAL: Default 100ms tolerance for unquantized MIDI
        self.tolerance = tolerance_ms / 1000.0
        
    def match_notes_with_tolerance(self, xml_notes: List[MusicXMLNote], 
                                 midi_notes: List[MIDINote]) -> List[Tuple]:
        matches = []
        
        for xml_note in xml_notes:
            candidates = []
            
            for midi_note in midi_notes:
                # CRITICAL: Pitch must match exactly
                if self._pitch_matches(xml_note.pitch, midi_note.pitch):
                    time_diff = abs(xml_note.onset_time - midi_note.start_time)
                    
                    if time_diff <= self.tolerance:
                        # Multi-factor confidence scoring
                        confidence = self._calculate_confidence(
                            xml_note, midi_note, time_diff
                        )
                        candidates.append((midi_note, confidence))
            
            # Select best match
            if candidates:
                best_match = max(candidates, key=lambda x: x[1])
                matches.append((xml_note, best_match[0], best_match[1]))
                
        return matches

# Task 0: Master MIDI Timing Extractor Implementation
class MasterMIDIExtractor:
    def __init__(self, master_midi_path: Path):
        # CRITICAL: Extract timing from original MIDI BEFORE any processing
        self.master_midi = mido.MidiFile(master_midi_path)
        self.master_timing = None
        
    def extract_master_timing(self) -> MasterMIDITiming:
        # PRESERVE original timing relationships as authoritative reference
        tempo_map = []
        note_events = []
        current_time = 0.0
        current_tempo = 500000  # Default 120 BPM
        
        for track in self.master_midi.tracks:
            for msg in track:
                current_time += mido.tick2second(msg.time, self.master_midi.ticks_per_beat, current_tempo)
                
                if msg.type == 'set_tempo':
                    tempo_map.append((current_time, 60000000 / msg.tempo))
                    current_tempo = msg.tempo
                elif msg.type == 'note_on' and msg.velocity > 0:
                    note_events.append({
                        'start_time': current_time,
                        'pitch': msg.note,
                        'velocity': msg.velocity,
                        'channel': msg.channel
                    })
        
        return MasterMIDITiming(
            master_midi_path=Path(self.master_midi.filename),
            tempo_map=tempo_map,
            total_duration_seconds=current_time,
            ppq=self.master_midi.ticks_per_beat,
            note_events=note_events
        )

# Task 5: Context Gatherer Implementation
class ContextGatherer:
    def __init__(self, musicxml_path: Path, midi_path: Path, svg_path: Path):
        # CRITICAL: Extract master timing FIRST before any processing
        self.master_extractor = MasterMIDIExtractor(midi_path)
        self.master_timing = self.master_extractor.extract_master_timing()
        self.xml_parser = XMLTemporalParser(musicxml_path)
        self.midi_matcher = MIDIMatcher()
        # PATTERN: Preserve existing coordinate system patterns
        
    def analyze_and_create_relationships(self) -> Dict:
        # Phase 1: Extract all musical data
        xml_notes = self.xml_parser.extract_all_notes()
        midi_notes = self._extract_midi_events()
        svg_coordinates = self._extract_svg_positions()
        
        # Phase 2: Create cross-format relationships
        matches = self.midi_matcher.match_notes_with_tolerance(xml_notes, midi_notes)
        
        # Phase 3: Handle tied note special cases
        tied_groups = self.xml_parser.extract_tied_notes()
        synchronized_notes = self._process_tied_relationships(matches, tied_groups)
        
        # Phase 4: Generate master relationship file with master MIDI timing
        master_data = {
            "project_metadata": self._create_metadata(),
            "master_midi_timing": self.master_timing,
            "synchronized_notes": [note.to_dict() for note in synchronized_notes],
            "timing_accuracy": self._calculate_accuracy_metrics(matches),
            "pipeline_merge_strategy": "end_merge_with_master_timing"
        }
        
        return master_data
```

### Integration Points

```yaml
MASTER_MIDI_TIMING:
  - extract: Original master MIDI timing BEFORE any note separation
  - preserve: All timing relationships as authoritative reference
  - coordinate: Both pipelines use master timing for synchronization
  - ensure: "start times that correspond exactly to MIDI note timing in seconds from the original master MIDI"

PIPELINE_EXECUTION_STRATEGY:
  - sequential: "audio symbolic separators first" then audio separators (as mentioned in original requirements)
  - parallel: Both pipelines with shared master timing reference
  - merge: "merging the both pipelines at the end" with coordinated timing
  - flexibility: Support both execution modes based on user preference

TIED_NOTE_MISMATCH_HANDLING:
  - visual: Multiple noteheads (3 in tied sequences) from XML
  - temporal: Single MIDI note event from master MIDI
  - correlation: "3 noteheads for 1 MIDI note" as specified in requirements
  - timing: First notehead gets master MIDI timing, others get calculated approximations

XML_PROCESSING:
  - extend: Separators/truly_universal_noteheads_extractor.py
  - pattern: "Use existing xml.etree.ElementTree patterns"
  - add: "Temporal analysis and tied note detection"
  - critical: "number of MIDI notes not the same if notes are tied"

MIDI_PROCESSING:
  - preserve: Audio Separators/midi_note_separator.py existing functionality
  - pattern: "Use existing mido library patterns"
  - add: "Tolerance matching and confidence scoring with master timing reference"
  - ensure: No alteration of original timing relationships

SVG_COORDINATES:
  - extend: Separators/xml_based_instrument_separator.py
  - pattern: "Use existing staff range coordination mappings"
  - add: "Beat position to X-coordinate correlation"

KEYFRAME_FORMAT:
  - extend: Audio Separators/audio_to_keyframes_fast.py
  - pattern: "Maintain existing [[frame, value]] format"
  - add: "Layer start time metadata from master MIDI for After Effects"
  - ensure: "each note head the corresponding keyframe data"

AFTER_EFFECTS_OBJECTS:
  - create: "objects in After Effects with start times"
  - timing: "start times that is the same start time as corresponding MIDI note in seconds"
  - reference: Master MIDI timing as authoritative source
  - import: Custom After Effects script for automated import

PARALLEL_PROCESSING:
  - pattern: "Use ProcessPoolExecutor like fast versions"
  - maintain: "8x performance improvement from existing audio tools"
  - add: "Dual-pipeline coordination with shared master timing"
  - coordinate: Both pipelines merge at the end
```

## Validation Loop

### Level 1: Syntax & Style

```bash
# Run these FIRST - fix any errors before proceeding
ruff check Synchronizer/ --fix
mypy Synchronizer/

# Expected: No errors. Fix any type hints or syntax issues before continuing.
```

### Level 2: Unit Tests

```python
# CREATE tests/test_synchronizer.py with comprehensive test cases:

def test_tied_note_detection():
    """XML parser correctly identifies tied note sequences"""
    xml_content = create_test_musicxml_with_ties()
    parser = XMLTemporalParser(xml_content)
    tied_groups = parser.extract_tied_notes()
    
    assert len(tied_groups) == 1
    assert len(tied_groups['group_1']) == 3  # Three tied notes
    assert tied_groups['group_1'][0].tie_type == "start"
    assert tied_groups['group_1'][-1].tie_type == "stop"

def test_midi_tolerance_matching():
    """MIDI matcher handles unquantized timing within tolerance"""
    xml_note = create_test_xml_note(start_time=1.000)
    midi_note = create_test_midi_note(start_time=1.050)  # 50ms difference
    
    matcher = MIDIMatcher(tolerance_ms=100)
    matches = matcher.match_notes_with_tolerance([xml_note], [midi_note])
    
    assert len(matches) == 1
    assert matches[0][2] > 0.8  # High confidence score

def test_context_gatherer_integration():
    """Context gatherer creates valid relationship mapping"""
    gatherer = ContextGatherer(test_xml, test_midi, test_svg)
    relationships = gatherer.analyze_and_create_relationships()
    
    assert "synchronized_notes" in relationships
    assert len(relationships["synchronized_notes"]) > 0
    assert relationships["timing_accuracy"]["match_rate"] > 0.95

def test_after_effects_jsx_generation():
    """Generated JSX script is valid ExtendScript"""
    sync_data = load_test_synchronization_data()
    jsx_generator = AEIntegration()
    jsx_script = jsx_generator.generate_import_script(sync_data)
    
    # Validate JSX syntax
    assert "app.project.items.addComp" in jsx_script
    assert "layer.startTime = " in jsx_script
    assert jsx_script.count('{') == jsx_script.count('}')  # Valid brackets
```

```bash
# Run and iterate until passing:
uv run pytest tests/test_synchronizer.py -v
# If failing: Debug with detailed logs, fix implementation, re-run
```

### Level 3: Integration Test

```bash
# Test master MIDI timing extraction FIRST
python Synchronizer/utils/master_midi_extractor.py "Base/Saint-Saens Trio No 2.mid"
# Expected: Master timing extracted with original note events and tempo map

# Test complete pipeline with real musical data
python Synchronizer/context_gatherer.py "Base/SS 9.musicxml" "Base/Saint-Saens Trio No 2.mid" "Base/SS 9 full.svg"

# Expected output: master_relationship.json with master_midi_timing section
# Verify: File contains master timing reference and synchronized_notes array
cat Synchronizer/outputs/master_relationship.json | jq '.master_midi_timing'
cat Synchronizer/outputs/master_relationship.json | jq '.synchronized_notes[0]'

# Test pipeline execution modes
python Synchronizer/synchronization_coordinator.py --mode sequential --run-full-pipeline
python Synchronizer/synchronization_coordinator.py --mode parallel --run-full-pipeline

# Expected: Both modes produce identical timing results
# Verify: Original SVG and audio files exist unchanged
# Verify: Master timing preserved in all outputs
# Verify: Tied note sequences properly handled (3 noteheads → 1 MIDI note)
```

### Level 4: After Effects Validation

```bash
# Test JSX script generation and AE import
python -c "
from Synchronizer.utils.ae_integration import AEIntegration
ae = AEIntegration()
jsx_script = ae.generate_from_sync_file('Synchronizer/outputs/master_synchronization.json')
print('Generated AE script length:', len(jsx_script))
"

# Manual AE test (if available):
# 1. Open After Effects
# 2. Run generated JSX script
# 3. Verify: Composition created with layers at correct start times
# 4. Verify: Keyframe data applied to layer properties

# Alternative validation - JSX syntax check:
node -c Synchronizer/outputs/ae_import_script.jsx
# Expected: No syntax errors
```

### Level 5: Musical Accuracy Validation

```bash
# Test with complex musical examples
python Synchronizer/context_gatherer.py \
    --xml "Base/complex_tied_notes.musicxml" \
    --midi "Base/complex_tied_notes.mid" \
    --tolerance 50 \
    --verbose

# Expected output with tied note handling:
# "Found 15 tied note groups"
# "Match accuracy: 98.5%"
# "Average timing error: 23ms"

# Performance regression test
time python Synchronizer/synchronization_coordinator.py --benchmark
# Expected: Performance within 10% of current pipeline execution time
```

## Final Validation Checklist

- [ ] **Master MIDI timing extraction**: Original timing preserved before any note separation
- [ ] **Pipeline execution modes**: Both sequential and parallel modes work with consistent timing
- [ ] **Tied note mismatch handling**: 3 noteheads correctly mapped to 1 MIDI note in tied sequences
- [ ] **After Effects objects timing**: Each notehead has start time matching MIDI note in seconds from master MIDI
- [ ] **Pipeline merge strategy**: Both symbolic and audio pipelines merge at end with coordinated timing
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check Synchronizer/`
- [ ] No type errors: `uv run mypy Synchronizer/`
- [ ] Context gatherer creates valid relationship JSON with master timing reference
- [ ] MIDI tolerance matching works with unquantized data
- [ ] Generated JSX script imports successfully in After Effects with correct start times
- [ ] All existing pipeline outputs remain unchanged (backward compatibility)
- [ ] Performance regression < 10% of current pipeline speed
- [ ] Musical accuracy > 95% for test cases

---

## Anti-Patterns to Avoid

- ❌ Don't modify existing SVG or audio processing tools - create coordination layer instead
- ❌ Don't skip tied note validation - musical accuracy is critical
- ❌ Don't hardcode timing tolerances - make them configurable
- ❌ Don't break parallel processing efficiency - maintain 8x speedup
- ❌ Don't ignore unquantized MIDI support - required for real performances
- ❌ Don't create new coordinate systems - use existing universal system
- ❌ Don't assume 1:1 note relationships - handle tied note complexities

## PRP Quality Score: 9/10

**Confidence Level**: High for one-pass implementation success through comprehensive context, validation loops, and proven patterns from existing codebase. The research provides deep understanding of tied note complexities, timing synchronization requirements, and integration strategies while maintaining full backward compatibility.