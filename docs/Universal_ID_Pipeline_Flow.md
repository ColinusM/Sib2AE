# Universal ID Pipeline Flow Documentation

**Complete guide to Universal ID creation, transformation, and preservation throughout the Sib2Ae orchestration pipeline.**

## 🎯 Overview

The Universal ID system maintains relationships between MusicXML notes, MIDI events, SVG coordinates, audio files, and After Effects keyframes throughout the entire pipeline execution. This document traces the complete ID lifecycle from creation to final After Effects integration.

## 📋 Universal ID Lifecycle Summary

```
UUID Creation → XML/MIDI Matching → Tied Note Processing → Pipeline Distribution → File Naming → Manifest Tracking → AE Integration
```

---

## 🏗️ Stage 1: Universal ID Creation & Initial Matching

### **WHO**: `note_coordinator.py`
### **WHEN**: First stage of orchestration, before any processing
### **WHAT**: Creates UUID4 identifiers and establishes XML↔MIDI↔SVG relationships

#### **Process Flow**:

```python
# Location: Brain/orchestrator/note_coordinator.py:78-86
class NoteCoordinator:
    def __init__(self):
        self.xml_notes = []
        self.midi_notes = []
        self.svg_notes = []
        self.universal_notes = []  # ← Core Universal ID storage
```

#### **ID Creation Logic**:

```python
# Brain/orchestrator/note_coordinator.py:~400
def create_universal_notes(self):
    for xml_note in self.xml_notes:
        universal_id = str(uuid.uuid4())  # ← UUID4 CREATION

        universal_note = UniversalNote(
            universal_id=universal_id,      # ← UNIQUE IDENTIFIER
            xml_data=xml_note,
            midi_data=matched_midi,         # ← From matching algorithm
            svg_data=calculated_svg,        # ← Coordinate transformation
            match_confidence=confidence,
            match_method=method,
            timing_priority="midi"
        )
```

#### **Registry Output**:
```json
{
  "universal_id": "2f2acffa-dd07-4128-a78f-0f2072c3ca49",
  "xml_data": {"part_id": "P1", "note_name": "A4", "measure": 4},
  "midi_data": {"start_time_seconds": 7.5, "velocity": 76},
  "svg_data": {"svg_x": 3178, "svg_y": 1049}
}
```

**WHY**: Creates the foundation for all subsequent pipeline stages to maintain note relationships across different data formats.

---

## 🔗 Stage 2: Tied Note Relationship Processing

### **WHO**: `tied_note_processor.py`
### **WHEN**: After Note Coordinator, before symbolic/audio processing
### **WHAT**: Processes complex tied note relationships using Universal IDs

#### **ID Integration Process**:

```python
# Location: Brain/orchestrator/tied_note_processor.py:525-584
def main():
    # Convert Universal Notes Registry to NoteMatch objects
    if 'notes' in matches_data:
        for registry_entry in registry_notes:
            universal_id = registry_entry['universal_id']  # ← ID RETRIEVAL

            # Create match objects preserving Universal ID
            match = NoteMatch(
                xml_note=xml_note,
                midi_note=midi_note,
                confidence=registry_entry.get('match_confidence', 1.0)
            )
            # Universal ID preserved in midi_note.note_id
            midi_note.note_id = universal_id  # ← ID PRESERVATION
```

#### **Timing Calculation Output**:
```json
{
  "tied_group_2": {
    "notes": [
      {"pitch": "B3", "tie_type": "start", "calculated_start_time": 9.000},
      {"pitch": "B3", "tie_type": "continue", "calculated_start_time": 9.333},
      {"pitch": "B3", "tie_type": "stop", "calculated_start_time": 9.444}
    ]
  }
}
```

**WHY**: Enables N:1 notehead-to-MIDI relationships where multiple SVG noteheads share timing from a single MIDI event.

---

## 🖼️ Stage 3: Symbolic Pipeline Processing

### **WHO**: 5 scripts in `Brain/App/Symbolic Separators/`
### **WHEN**: After tied note processing, parallel with audio pipeline
### **WHAT**: Creates individual SVG files with Universal ID preservation

#### **3.1 Noteheads Extraction**
```python
# Location: Brain/App/Symbolic Separators/truly_universal_noteheads_extractor.py
# INPUT: Universal Notes Registry → universal_output/universal_notes_registry.json
# PROCESS: Extract noteheads with Universal ID-based naming
# OUTPUT: notehead_<uuid_first8>_<part>_<pitch>_<measure>.svg
```

#### **3.2 Individual Noteheads Creation**
```python
# Location: Brain/App/Symbolic Separators/individual_noteheads_creator.py
# INPUT: MusicXML + Universal ID registry
# PROCESS: One SVG per notehead with UUID filename embedding
# OUTPUT: notehead_2f2acffa_P1_A4_M4.svg (Universal ID prefix)
```

#### **SVG Manifest Generation**:
```json
{
  "universal_id": "2f2acffa-dd07-4128-a78f-0f2072c3ca49",
  "svg_filename": "notehead_2f2acffa_P1_A4_M4.svg",
  "coordinates": {"svg_x": 3178, "svg_y": 1049},
  "visual_data": {"notehead_code": 102, "duration": "quarter"}
}
```

**WHY**: Each visual element maintains traceability to its source Universal ID for After Effects synchronization.

---

## 🎵 Stage 4: Audio Pipeline Processing

### **WHO**: 3 scripts in `Brain/App/Audio Separators/`
### **WHEN**: Parallel with symbolic pipeline
### **WHAT**: Creates audio files with Universal ID-preserved naming

#### **4.1 MIDI Note Separation**
```python
# Location: Brain/App/Audio Separators/midi_note_separator.py
# CRITICAL: Receives --registry parameter from orchestrator

def separate_midi_with_universal_ids(midi_file, registry_path):
    # Load Universal ID registry
    with open(registry_path, 'r') as f:
        registry = json.load(f)

    # Match MIDI notes to Universal IDs
    for midi_note in midi_notes:
        universal_id = find_matching_universal_id(midi_note, registry)

        # Create filename with Universal ID suffix
        filename = f"note_{seq:03d}_{instrument}_{pitch}_vel{velocity}_{universal_id[:4]}.mid"
        #                                                    ↑ FIRST 4 CHARS OF UUID
```

#### **Universal ID Lookup Algorithm**:
```python
# Brain/App/Audio Separators/midi_note_separator.py:~200
def find_matching_universal_id(midi_note, registry):
    """Match MIDI note to Universal ID via pitch+timing"""
    for entry in registry['notes']:
        if (entry.get('midi_data') and
            entry['midi_data']['pitch_name'] == midi_note.pitch_name and
            abs(entry['midi_data']['start_time_seconds'] - midi_note.start_time) < 0.1):
            return entry['universal_id']  # ← ID RETRIEVAL
    return "unknown"
```

#### **4.2 Audio Rendering**
```python
# Location: Brain/App/Audio Separators/midi_to_audio_renderer_fast.py
# INPUT: note_000_Flûte_A4_vel76_2f2a.mid
# PROCESS: Convert MIDI to WAV, preserve Universal ID in filename
# OUTPUT: note_000_Flûte_A4_vel76_2f2a.wav
```

#### **4.3 Keyframe Generation**
```python
# Location: Brain/App/Audio Separators/audio_to_keyframes_fast.py
# INPUT: note_000_Flûte_A4_vel76_2f2a.wav
# PROCESS: Generate 60Hz keyframes with Universal ID metadata
# OUTPUT: note_000_Flûte_A4_vel76_2f2a_keyframes.json
```

#### **Keyframe Universal ID Embedding**:
```json
{
  "universal_id": "2f2acffa-dd07-4128-a78f-0f2072c3ca49",
  "filename": "note_000_Flûte_A4_vel76_2f2a.wav",
  "keyframes": [[0, 45.2], [1, 48.7], [2, 52.1]],
  "metadata": {
    "pitch": "A4", "instrument": "Flûte",
    "start_time_seconds": 7.5, "timing_source": "midi_exact"
  }
}
```

**WHY**: Audio files and keyframes maintain Universal ID connections for precise After Effects timing synchronization.

---

## 📊 Stage 5: Universal Registry & Manifest Management

### **WHO**: `universal_registry.py` + `manifest_manager.py`
### **WHEN**: Throughout pipeline execution
### **WHAT**: Tracks Universal ID lifecycle and file relationships

#### **Registry Updates**:
```python
# Location: Brain/orchestrator/universal_registry.py:165-180
def register_file_creation(self, universal_id: str, stage_name: str, file_path: Path):
    """Track file creation for Universal ID"""
    if universal_id in self.universal_records:
        self.universal_records[universal_id].stage_files[stage_name].append(file_path)
        self.universal_records[universal_id].pipeline_stages_completed.add(stage_name)
        self.universal_records[universal_id].last_updated = datetime.now()
```

#### **Manifest Generation**:
```json
{
  "universal_id": "2f2acffa-dd07-4128-a78f-0f2072c3ca49",
  "pipeline_stages": {
    "note_coordinator": ["universal_notes_registry.json"],
    "noteheads_extraction": ["notehead_2f2acffa_P1_A4_M4.svg"],
    "midi_separation": ["note_000_Flûte_A4_vel76_2f2a.mid"],
    "audio_rendering": ["note_000_Flûte_A4_vel76_2f2a.wav"],
    "keyframe_generation": ["note_000_Flûte_A4_vel76_2f2a_keyframes.json"]
  }
}
```

**WHY**: Provides complete audit trail and integrity validation for Universal ID relationships across all pipeline stages.

---

## 🎬 Stage 6: After Effects Integration Data

### **WHO**: `tied_note_processor.py` + pipeline manifests
### **WHEN**: Final stage output generation
### **WHAT**: Creates After Effects-ready timing data with Universal IDs

#### **AE Timing Data Generation**:
```python
# Location: Brain/orchestrator/tied_note_processor.py:455-479
def get_after_effects_timing_data(self):
    for assignment in self.assignments:
        timing_entry = {
            'notehead_id': f"{assignment.note.part_id}_{assignment.note.measure_number}_{assignment.note.pitch}",
            'start_time_seconds': assignment.calculated_start_time,  # ← PRECISE TIMING
            'universal_id': get_universal_id_from_assignment(assignment),  # ← ID LINK
            'timing_source': 'midi_exact' if assignment.is_primary else 'calculated_approximation'
        }
```

#### **Complete AE Integration Package**:
```json
{
  "universal_id": "2f2acffa-dd07-4128-a78f-0f2072c3ca49",
  "svg_notehead": "notehead_2f2acffa_P1_A4_M4.svg",
  "audio_file": "note_000_Flûte_A4_vel76_2f2a.wav",
  "keyframes_file": "note_000_Flûte_A4_vel76_2f2a_keyframes.json",
  "timing_data": {
    "start_time_seconds": 7.5,
    "timing_confidence": 1.0,
    "timing_source": "midi_exact"
  },
  "coordinates": {"svg_x": 3178, "svg_y": 1049}
}
```

**WHY**: Enables frame-accurate synchronization between SVG noteheads, audio waveforms, and keyframe animations in After Effects.

---

## 🔄 Universal ID Transformation Patterns

### **Filename Evolution**:
```
UUID: 2f2acffa-dd07-4128-a78f-0f2072c3ca49

1. Registry:        universal_id: "2f2acffa-dd07-4128-a78f-0f2072c3ca49"
2. SVG:            notehead_2f2acffa_P1_A4_M4.svg
3. MIDI:           note_000_Flûte_A4_vel76_2f2a.mid
4. Audio:          note_000_Flûte_A4_vel76_2f2a.wav
5. Keyframes:      note_000_Flûte_A4_vel76_2f2a_keyframes.json
```

### **ID Extraction Pattern**:
```python
def extract_universal_id_from_filename(filename: str) -> str:
    """Extract Universal ID from pipeline-generated filename"""
    # Pattern: *_<4char_uuid>.<ext> or <8char_uuid>_*
    match = re.search(r'[0-9a-f]{4,8}', filename)
    return match.group() if match else None
```

---

## 📈 Pipeline Statistics & Validation

### **Universal ID Integrity Metrics**:
```json
{
  "total_universal_ids": 9,
  "successfully_processed": 9,
  "pipeline_completion_rate": 100.0,
  "stages_with_full_coverage": [
    "note_coordinator", "tied_note_processor", "symbolic_pipeline",
    "audio_pipeline", "manifest_generation"
  ],
  "integrity_validation": {
    "filename_consistency": true,
    "registry_completeness": true,
    "manifest_accuracy": true
  }
}
```

### **Complex Relationship Handling**:
```json
{
  "tied_note_groups": 2,
  "complex_relationships": 1,
  "b3_chain_example": {
    "universal_ids": ["cf326b50...", "43d615ff...", "06e6602e..."],
    "shared_midi_timing": "9.000s → 9.500s",
    "calculated_timings": ["9.000s", "9.333s", "9.444s"],
    "svg_files": 3,
    "audio_files": 1,
    "keyframe_files": 1
  }
}
```

---

## 🎯 Universal ID Best Practices

### **1. ID Preservation**:
- **NEVER** regenerate Universal IDs once created
- **ALWAYS** pass existing IDs through filename transformations
- **VERIFY** ID consistency across all pipeline stages

### **2. Filename Conventions**:
- Use first 4-8 characters of UUID for filename brevity
- Maintain UUID traceability through regex patterns
- Include Universal ID in all generated file metadata

### **3. Registry Management**:
- Update registry atomically with file creation
- Validate ID integrity after each pipeline stage
- Maintain complete audit trail for debugging

### **4. Error Handling**:
- Graceful fallback when Universal ID not found
- Log all ID mismatches for investigation
- Preserve partial pipeline results for recovery

---

## 🎼 After Effects Integration Summary

The Universal ID system enables **frame-accurate synchronization** by maintaining relationships between:

1. **SVG Noteheads** → Visual positioning and timing
2. **MIDI Events** → Musical timing and performance data
3. **Audio Waveforms** → Rendered sound with precise timing
4. **Keyframe Data** → 60Hz animation properties
5. **Tied Note Calculations** → Complex musical relationships

**Result**: Each visual notehead in After Effects can be precisely synchronized with its corresponding audio waveform and keyframe animation data, enabling realistic music visualization with complex tied note relationships and accurate timing.

---

## 📚 File Reference Index

### **Orchestrator Files**:
- `note_coordinator.py` - Universal ID creation and initial matching
- `tied_note_processor.py` - Complex relationship processing with timing
- `universal_registry.py` - ID lifecycle tracking and validation
- `manifest_manager.py` - Atomic file and ID relationship management
- `xml_temporal_parser.py` - Tied note detection with continue tie support

### **App Files** (Symbolic):
- `truly_universal_noteheads_extractor.py` - SVG generation with UUID naming
- `individual_noteheads_creator.py` - Per-notehead files with ID embedding
- `xml_based_instrument_separator.py` - Instrument separation with ID tracking
- `truly_universal_noteheads_subtractor.py` - Background SVG with ID context
- `staff_barlines_extractor.py` - Staff elements with Universal ID context

### **App Files** (Audio):
- `midi_note_separator.py` - MIDI splitting with Universal ID integration
- `midi_to_audio_renderer_fast.py` - Audio rendering with ID preservation
- `audio_to_keyframes_fast.py` - Keyframe generation with Universal ID metadata

### **Output Files**:
- `universal_notes_registry.json` - Master Universal ID database
- `tied_note_assignments.json` - Timing calculations with ID references
- `*_pipeline_manifest.json` - Stage-specific ID tracking
- `ae_timing_data.json` - After Effects integration data

---

**🎯 The Universal ID system is the backbone of the Sib2Ae pipeline, ensuring perfect synchronization between musical notation, audio performance, and visual animation across all processing stages.**