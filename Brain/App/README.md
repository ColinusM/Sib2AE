# Brain/App - Sib2Ae Pipeline Tools

Core processing tools for the Sib2Ae music notation to After Effects synchronization pipeline. This directory contains the individual scripts that transform MusicXML/MIDI/SVG data into After Effects-ready outputs.

## 🎯 Overview

The Brain/App directory houses two main processing categories:

- **Symbolic Separators**: SVG and MusicXML processing tools for visual notation elements
- **Audio Separators**: MIDI-to-audio processing and keyframe generation tools

These tools work independently but are coordinated by the Universal ID Pipeline Orchestrator to maintain synchronization across all output formats.

## 📦 Directory Structure

```
Brain/App/
├── Symbolic Separators/        # SVG and MusicXML processing (6 scripts)
│   ├── truly_universal_noteheads_extractor.py
│   ├── truly_universal_noteheads_subtractor.py
│   ├── xml_based_instrument_separator.py
│   ├── individual_noteheads_creator.py
│   ├── staff_barlines_extractor.py
│   └── ornament_symbols_extractor.py    # NEW: Extract ornament symbols
├── Audio Separators/           # MIDI and audio processing (3 scripts)
│   ├── midi_note_separator.py
│   ├── midi_to_audio_renderer_fast.py
│   └── audio_to_keyframes_fast.py
└── README.md                   # This file
```

## 🎼 Symbolic Separators

### Purpose
Transform MusicXML and SVG data into individual visual elements ready for After Effects animation, maintaining pixel-perfect coordinate accuracy.

### Scripts

#### 1. `truly_universal_noteheads_extractor.py`
**Purpose**: Extract noteheads from MusicXML with precise SVG coordinates
```bash
python "Brain/App/Symbolic Separators/truly_universal_noteheads_extractor.py" "Brain/Base/SS 9.musicxml"
```
- **Input**: MusicXML file with note definitions
- **Output**: Individual notehead SVG files in `outputs/svg/noteheads/`
- **Coordinate System**: Universal transformation (X_SCALE: 3.206518, X_OFFSET: 564.93)
- **Staff Positioning**: Dynamic Y positioning based on staff count

#### 2. `truly_universal_noteheads_subtractor.py`
**Purpose**: Remove noteheads from full SVG while preserving all other elements
```bash
python "Brain/App/Symbolic Separators/truly_universal_noteheads_subtractor.py" "Brain/Base/SS 9.musicxml" "Brain/Base/SS 9 full.svg"
```
- **Input**: MusicXML + complete SVG score
- **Output**: Clean background SVG without noteheads in `outputs/svg/`
- **Preservation**: Staff lines, barlines, clefs, time signatures, text

#### 3. `xml_based_instrument_separator.py`
**Purpose**: Create individual SVG files per instrument/part
```bash
python "Brain/App/Symbolic Separators/xml_based_instrument_separator.py" "Brain/Base/SS 9.musicxml" "Brain/Base/SS 9 full.svg" "outputs/svg/instruments"
```
- **Input**: MusicXML + SVG + output directory
- **Output**: Separate SVG files per instrument (Flûte_P1.svg, Violon_P2.svg)
- **Features**: Maintains part-specific visual elements and layout

#### 4. `individual_noteheads_creator.py`
**Purpose**: Generate one SVG file per notehead for After Effects layer animation
```bash
python "Brain/App/Symbolic Separators/individual_noteheads_creator.py" "Brain/Base/SS 9.musicxml"
```
- **Input**: MusicXML with note definitions
- **Output**: Individual SVG files per note in `outputs/svg/noteheads/`
- **Naming**: `notehead_P1_A4_M4.svg` (Part_Pitch_Measure)

#### 5. `staff_barlines_extractor.py`
**Purpose**: Extract staff lines and barlines for background elements
```bash
python "Brain/App/Symbolic Separators/staff_barlines_extractor.py" "Brain/Base/SS 9.musicxml" "Brain/Base/SS 9 full.svg"
```
- **Input**: MusicXML + SVG
- **Output**: Staff/barline SVG in `outputs/svg/staff_barlines/`
- **Elements**: Staff lines (stroke-width: 2.25), barlines (stroke-width: 5)

#### 6. `ornament_symbols_extractor.py` **NEW**
**Purpose**: Extract ornament symbols (trills, mordents, accents) as individual SVG files
```bash
python "Brain/App/Symbolic Separators/ornament_symbols_extractor.py" "Brain/Base/Trill/Saint-Saens Trio No 2.svg"
```
- **Input**: SVG file with ornament symbols
- **Output**: Individual ornament SVG files in `outputs/svg/ornaments/`
- **Detected Symbols**: Trills (U+F0D9), Mordents (U+F04D), Accents (U+F06A), Staccato (U+F04A)
- **Format**: `{ornament_type}_{index:03d}_U+{unicode:04X}.svg`
- **Example Output**: `trill_start_000_U+F0D9.svg`, `mordent_000_U+F04D.svg`

## 🎵 Audio Separators

### Purpose
Transform MIDI data into audio files and After Effects keyframe data, maintaining temporal synchronization with visual elements.

### Scripts

#### 1. `midi_note_separator.py` (Foundation with Pedal + Ornament Support)
**Purpose**: Split MIDI files into individual note files with Universal ID preservation, sustain pedal, and ornament compatibility
```bash
# With Universal ID registry (orchestrator mode)
python "Brain/App/Audio Separators/midi_note_separator.py" "Brain/Base/Saint-Saens Trio No 2.mid" --registry "universal_output/universal_notes_registry.json"

# Standalone mode (legacy compatibility)
python "Brain/App/Audio Separators/midi_note_separator.py" "Brain/Base/Saint-Saens Trio No 2.mid"
```
- **Input**: Complete MIDI file + Universal ID registry (orchestrator provides automatically)
- **Output**: Individual MIDI files per note in `outputs/midi/`
- **Naming Conventions**:
  - Standard notes: `note_000_Flûte_A4_vel76_5502.mid` (4-char UUID prefix)
  - Ornament expansions: `note_002_Flûte_F#4_vel75__exp_000.mid` (8-char ornament suffix)
- **Foundation**: Required for all subsequent audio processing
- **Registry Integration**: Loads Note Coordinator's registry to map MIDI notes to XML Universal IDs
- **UUID Recovery**: Matches MIDI notes to registry via pitch+track lookup for source Universal ID retrieval
- **Dual ID System**:
  - **Standard UUIDs**: Uses first 4 characters (`universal_id[:4]`)
  - **Ornament IDs**: Uses last 8 characters (`universal_id[-8:]`) to preserve `exp_000` suffix
  - Automatic detection via `universal_id.startswith('orn_')` check
- **Pedal Detection**: Automatic CC 64 (sustain pedal) detection and file extension
  - Notes starting during active pedal: CC 64 ON synthesized at file start
  - Notes with pedal release after note ends: File duration extended to pedal OFF
  - Channel-specific processing: Pedal events only affect same-channel notes
- **Ornament Compatibility**: Handles ornament expansion notes (trills, mordents, grace notes) that lack xml_data
  - Graceful handling of registry entries without xml_data field
  - Full Universal ID preservation: `orn_trill_001_exp_005` → `_exp_005` suffix
  - Ornament expansions processed normally through MIDI→Audio→Keyframe pipeline

#### 2. `midi_to_audio_renderer_fast.py` (High-Quality Audio Rendering + Registry Integration)
**Purpose**: Convert MIDI notes to audio using 247MB SGM-V2.01 soundfont with Universal ID preservation
```bash
# With Universal ID registry (orchestrator mode)
python "Brain/App/Audio Separators/midi_to_audio_renderer_fast.py" "outputs/midi" --registry "universal_output/universal_notes_registry.json"

# Standalone mode (legacy compatibility)
python "Brain/App/Audio Separators/midi_to_audio_renderer_fast.py" "outputs/midi"
```
- **Soundfont**: High-quality 247MB SGM-V2.01 for realistic instruments (located in `soundfonts/SGM_V2_final.sf2`)
- **Mode**: Parallel processing, 22kHz sample rate, 6 workers
- **Quality**: Realistic violin and flute sounds (resolved: violin no longer sounds like noise, flute no longer synthetic)
- **Output**: WAV files organized by instrument in `outputs/audio/`
- **Registry Integration**: Uses UniversalIDRegistry class for robust UUID lookup and preservation
- **UUID Propagation**: Extracts 4-char UUID from MIDI filenames and preserves in audio filenames
- **Enhanced Error Handling**: Confidence-based matching with graceful fallbacks
- **Performance**: ~1 second total for 6 files

#### 3. `audio_to_keyframes_fast.py` (60Hz Amplitude-Only Keyframes + Universal ID Preservation)
**Purpose**: Generate simplified 60Hz amplitude-only keyframes with full Universal ID preservation
```bash
# With Universal ID registry (orchestrator mode)
python "Brain/App/Audio Separators/audio_to_keyframes_fast.py" "outputs/audio" --registry "universal_output/universal_notes_registry.json"

# Standalone mode (legacy compatibility)
python "Brain/App/Audio Separators/audio_to_keyframes_fast.py" "outputs/audio"
```
- **Output**: Only amplitude over time (0-100 normalized) at true 60 data points/second
- **Format**: `[frame, amplitude_value]` pairs with sequential frame indexing (0,1,2,3...)
- **Frame Rate**: 60 FPS for YouTube compatibility (upgraded from 30 FPS)
- **Universal ID Preservation**: Full UUIDs embedded in keyframe JSON metadata (both standard and ornament)
- **Enhanced Metadata**: Data integrity tracking with confidence scoring and registry validation
- **Registry Integration**: Expands partial IDs to full Universal IDs via registry lookup
  - Standard UUIDs: `5502` → `5502a647-7bca-4d81-93e5-3fa5562c4caf`
  - Ornament IDs: `exp_000` → `orn_trill_001_exp_000`
- **Dual Pattern Recognition**:
  - UUID pattern: `[a-f0-9]{4}` (hex characters)
  - Ornament pattern: `exp_\d{3}` (expansion index)
- **Simplified**: Removed over-engineered scale, opacity, hue, position properties
- **Performance**: ~0.5-1 second per file, eliminates keyframe conflicts
- **Clean**: Perfect for direct After Effects amplitude animation with bulletproof synchronization

## 🔄 Pipeline Integration

### Orchestrator Coordination
All scripts are coordinated by the Universal ID Pipeline Orchestrator (`Brain/orchestrator/universal_orchestrator.py`):

```bash
# Complete pipeline execution
python -m Brain.orchestrator.universal_orchestrator \
    "Brain/Base/SS 9.musicxml" \
    "Brain/Base/Saint-Saens Trio No 2.mid" \
    --svg "Brain/Base/SS 9 full.svg" \
    --mode sequential
```

### Processing Order
1. **Symbolic Pipeline** (5 stages): MusicXML/SVG → Individual visual elements
2. **Audio Pipeline** (3 stages): MIDI → Individual notes → Audio → Keyframes

### Universal ID System
- Each note maintains a Universal ID throughout all processing stages
- Enables synchronization between visual coordinates and audio timing
- Preserves relationships: `note_000_Flûte_A4_vel76.{mid,wav,keyframes.json}`

## 🎨 Output Organization

### SVG Outputs (`outputs/svg/`)
```
svg/
├── instruments/          # Per-instrument SVG files
├── noteheads/           # Individual notehead SVGs for animation
├── staff_barlines/      # Background staff and barline elements
└── annotated/           # SVGs with timing labels (from Note Coordinator)
```

### Audio Outputs (`outputs/audio/`)
```
audio/
├── Flûte/              # Flute audio files (.wav)
├── Violon/             # Violin audio files (.wav)
└── [Instrument]/       # Organized by instrument name
```

### JSON Outputs (`outputs/json/`)
```
json/
├── keyframes/          # After Effects keyframe data
├── coordination/       # Universal ID registry and metadata
└── manifests/          # Pipeline execution manifests
```

## ⚙️ Technical Specifications

### Coordinate System
- **X Transformation**: `svg_x = xml_x * 3.206518 + 564.93`
- **Y Positioning**: Staff-based with 380px separation
- **Staff Layout**: Dynamic positioning based on instrument count

### Audio Specifications
- **Standard Mode**: 44kHz sample rate, sequential processing
- **Fast Mode**: 22kHz sample rate, 6 parallel workers
- **Keyframe Rate**: 60 FPS for YouTube compatibility (upgraded from 30 FPS)
- **Format**: WAV files, simplified JSON keyframe data (amplitude-only)

### File Naming Conventions
- **MIDI**: `note_XXX_Instrument_Pitch_velYY.mid`
- **Audio**: `note_XXX_Instrument_Pitch_velYY.wav`
- **Keyframes**: `note_XXX_Instrument_Pitch_velYY_keyframes.json`
- **SVG**: `notehead_PartID_Pitch_MeasureN.svg`

## 🚀 Usage Examples

### Individual Script Execution
```bash
# Extract noteheads
python "Brain/App/Symbolic Separators/truly_universal_noteheads_extractor.py" "Brain/Base/SS 9.musicxml"

# Separate MIDI notes
python "Brain/App/Audio Separators/midi_note_separator.py" "Brain/Base/Saint-Saens Trio No 2.mid"

# Render audio (fast mode)
python "Brain/App/Audio Separators/midi_to_audio_renderer_fast.py" "outputs/midi"

# Generate keyframes
python "Brain/App/Audio Separators/audio_to_keyframes_fast.py" "outputs/audio"
```

### Complete Workflow
```bash
# 1. Symbolic processing (5 scripts)
python "Brain/App/Symbolic Separators/truly_universal_noteheads_extractor.py" "Brain/Base/SS 9.musicxml"
python "Brain/App/Symbolic Separators/truly_universal_noteheads_subtractor.py" "Brain/Base/SS 9.musicxml" "Brain/Base/SS 9 full.svg"
python "Brain/App/Symbolic Separators/xml_based_instrument_separator.py" "Brain/Base/SS 9.musicxml" "Brain/Base/SS 9 full.svg" "outputs/svg/instruments"
python "Brain/App/Symbolic Separators/individual_noteheads_creator.py" "Brain/Base/SS 9.musicxml"
python "Brain/App/Symbolic Separators/staff_barlines_extractor.py" "Brain/Base/SS 9.musicxml" "Brain/Base/SS 9 full.svg"

# 2. Audio processing (3 scripts)
python "Brain/App/Audio Separators/midi_note_separator.py" "Brain/Base/Saint-Saens Trio No 2.mid"
python "Brain/App/Audio Separators/midi_to_audio_renderer_fast.py" "outputs/midi"
python "Brain/App/Audio Separators/audio_to_keyframes_fast.py" "outputs/audio"
```

## 📊 Performance Characteristics

### Symbolic Pipeline Performance
- **Noteheads Extraction**: ~0.1s (pixel-perfect coordinate calculation)
- **Noteheads Subtraction**: ~0.1s (SVG element removal)
- **Instrument Separation**: ~0.1s (per-instrument SVG creation)
- **Individual Creation**: ~0.1s (individual notehead SVGs)
- **Staff/Barlines**: ~0.1s (background element extraction)

### Audio Pipeline Performance
- **MIDI Separation**: ~0.1s (foundation for audio processing, +~10ms pedal detection overhead)
- **Audio Rendering**: 0.7-1s (fast mode with SGM-V2.01 soundfont)
- **Keyframe Generation**: 0.5-1s (60Hz amplitude-only, sequential frame indexing)

### Scalability
- **Note Count**: Linear scaling with number of notes
- **Parallel Processing**: Fast modes utilize 6 worker processes
- **Memory Usage**: Optimized for large musical scores
- **File I/O**: Efficient batch processing patterns

## 🔗 Integration Points

### After Effects Import
- SVG files: Vector graphics for precise positioning
- Audio files: Synchronized waveform analysis
- Keyframes: Automated animation properties

### Enhanced Universal ID System

**Registry-Based Architecture** (Post-Architecture Refactor):
- **Robust Data Access**: Standardized registry lookup replacing fragile filename extraction
- **Full UUID Preservation**: Complete 36-character UUIDs throughout pipeline (eliminates collision risk)
- **Confidence-Based Matching**: Exact (1.0), fuzzy (0.9), fallback (0.8) strategies for reliable note identification
- **Enhanced Metadata**: Data integrity tracking with registry validation and confidence scoring
- **Frame-Accurate Synchronization**: Bulletproof relationships between visual coordinates and audio timing
- **Complex Musical Support**: Handles tied notes, sustain pedal, ornaments, and multi-instrument synchronization

**Ornament Universal ID Architecture**:
- **Semantic IDs**: `orn_{type}_{parent}_exp_{index}` (e.g., `orn_trill_001_exp_005`)
- **Dual ID System**: Standard UUIDs (4-char prefix) + Ornament IDs (8-char suffix)
- **Filename Examples**:
  - Standard: `note_000_Flûte_A4_vel76_5502.wav` (UUID: `5502a647-7bca...`)
  - Ornament: `note_002_Flûte_F#4_vel75__exp_000.wav` (ID: `orn_mordent_001_exp_000`)
- **Registry Expansion**: Partial `exp_000` → Full `orn_trill_001_exp_000` via lookup
- **Complete Traceability**: Registry → MIDI → Audio → Keyframes with full ID preservation

### Orchestrator Coordination
- Sequential execution for reliability
- Parallel execution for performance
- Error handling and retry mechanisms
- Progress tracking and logging

## ⚙️ Soundfont Requirements

### SGM-V2.01 Soundfont Setup
- **File**: `soundfonts/SGM_V2_final.sf2` (247MB)
- **Download**: Must be obtained separately due to file size
- **Fallback**: System FluidSynth paths available as backup
- **Organization**: All soundfonts stored in `soundfonts/` directory
- **Git**: *.sf2 files excluded from version control

## 🚀 Recent Performance Optimizations (September 2025)

### Universal ID Architecture Refactor (MAJOR ENHANCEMENT)
- **Critical Issue Resolved**: Eliminated fragile "backdoor" UUID extraction from filenames
- **Architecture Transformation**: Registry-based access replacing collision-prone 4-character truncation
- **Collision Risk Elimination**: 65,536 combinations → 2^128 combinations (mathematically collision-resistant)
- **Data Integrity**: Complete audit trail from Note Coordinator to final After Effects keyframes
- **Registry Integration**: All scripts now accept `--registry` parameter with standardized access patterns
- **Confidence Scoring**: Hierarchical matching strategies with graceful fallbacks
- **Performance Impact**: <10% overhead for bulletproof synchronization guarantees

### 60Hz Keyframe Generation
- **Before**: 30 FPS with ~43 data points/second
- **After**: True 60 data points/second (60.2 Hz) for YouTube compatibility
- **Implementation**: Dynamic hop_length calculation (sr/60 = 367 samples)
- **Result**: Consecutive frame numbers (0,1,2,3...) with perfect temporal resolution

### Audio Quality Breakthrough
- **Soundfont Upgrade**: SGM-V2.01 (247MB) replaces FluidR3_GM
- **Quality Improvements**: Violin no longer sounds like noise, flute no longer synthetic
- **Organization**: Soundfonts moved to `soundfonts/` directory
- **File Management**: *.sf2 files excluded from git due to size

### Simplified Keyframe Output with Enhanced Metadata
- **Removed**: Over-engineered scale, opacity, hue, position_x properties
- **Focus**: Amplitude-only output (0-100 normalized) for clean AE integration
- **Enhanced**: Full Universal ID preservation with data integrity tracking
- **Format**: Simple `[frame, amplitude_value]` pairs with comprehensive metadata
- **Benefit**: Eliminates complexity while ensuring bulletproof synchronization

### Codebase Cleanup
- **Scripts Reduced**: Audio pipeline now has 3 scripts (down from 5)
- **Duplicates Removed**: Eliminated audio_to_keyframes.py and midi_to_audio_renderer.py
- **Consistency**: All references updated to use *_fast.py versions exclusively
- **Registry Integration**: Standardized --registry parameter across all scripts

## 📄 License

Part of the Sib2Ae project - Music notation to After Effects synchronization pipeline.

## 🎯 Version

**Status**: Production Ready
**Last Updated**: October 8, 2025
**Pipeline Compatibility**: Universal ID Pipeline Orchestrator 1.2.0

### Recent Updates
- **v1.7.1**: Ornament Universal ID preservation (October 8, 2025) **CRITICAL FIX**
  - **Complete UUID Chain**: Ornament expansions now preserve full Universal IDs through entire pipeline
  - **MIDI Separator**: Uses last 8 chars (`exp_000`) for ornament IDs vs first 4 for standard UUIDs
  - **Audio Renderer**: Preserves ornament suffixes through .mid → .wav transformation
  - **Keyframe Generator**: Recognizes `exp_\d{3}` pattern and expands to full ornament ID
  - **Registry Utils**: Enhanced filename parsing supports both UUID and ornament patterns
  - **Full Traceability**: `exp_000` → `orn_trill_001_exp_000` via registry expansion
  - **Test Verification**: Mordent (2 expansions) and Trill (6 expansions) fully validated
- **v1.7.0**: Ornament compatibility for Audio Separators (October 8, 2025)
  - **MIDI Separator**: Graceful handling of ornament expansion notes without xml_data
  - **Audio Renderer**: Compatible with grace notes, trills, mordents from ornament detection
  - **Keyframe Generator**: Processes ornament audio files with full Universal ID preservation
  - **Track-Specific**: Registry utils updated to prevent cross-instrument interference
  - **Complete Pipeline**: Ornaments flow seamlessly through MIDI→Audio→Keyframe stages
- **v1.6.0**: Targeted Universal ID integration for individual_noteheads_creator.py (September 30, 2025)
  - **Architectural Fix**: Registry integration ONLY for scripts requiring audio-visual synchronization
  - **Critical Path**: individual_noteheads_creator.py now generates UUID-suffixed filenames
  - **100% Confidence Matching**: XML-based UUID lookup (part_id + pitch + measure)
  - **Perfect Synchronization**: `notehead_002_P1_G4_M5_13b9.svg` ↔ `note_001_Flûte_G4_vel76_13b9.wav`
  - **Correct Architecture**: 4 structural Symbolic scripts remain legacy (no unnecessary registry overhead)
- **v1.5.0**: Sustain pedal (CC 64) detection and processing implemented (MAJOR ENHANCEMENT)
  - **Automatic Pedal Detection**: Built-in CC 64 event scanning during MIDI analysis
  - **File Duration Extension**: Individual MIDI files extended to pedal release times
  - **Pedal Context Injection**: CC 64 ON/OFF events added to preserve sustain state
  - **Channel-Specific Processing**: Pedal events only affect notes on same MIDI channel
  - **Edge Case Handling**: Comprehensive logic for all pedal timing scenarios
  - **Zero Breaking Changes**: Fully backward compatible with existing pipeline
  - **Test Coverage**: 5 comprehensive test cases validating all pedal logic
- **v1.5.0**: Universal ID Architecture Refactor (ARCHITECTURAL BREAKTHROUGH)
  - **Major Architectural Enhancement**: Complete elimination of fragile "backdoor" UUID extraction patterns
  - **Registry Utilities System**: New `registry_utils.py` (344 lines) with `UniversalIDRegistry` class
  - **Full UUID Preservation**: 36-character UUIDs replace collision-prone 4-character truncation
  - **Confidence-Based Matching**: Exact (1.0), fuzzy (0.9), fallback (0.8) strategies with graceful error handling
  - **Standardized Access Patterns**: All scripts use unified `--registry` parameter with robust data lookup
  - **Data Integrity Tracking**: Enhanced metadata with registry validation and confidence scoring
  - **Performance Optimization**: O(1) UUID lookup via pre-computed indices with minimal overhead
  - **Production Reliability**: Bulletproof synchronization eliminating 65,536 collision risk
- **v1.4.0**: Universal ID preservation implemented (CRITICAL ENHANCEMENT)
  - **Core Issue**: Scripts created sequential IDs (000, 001, 002) disconnected from Note Coordinator's Universal IDs
  - **Root Cause**: MIDI separator, audio renderer, and keyframe generator operated independently without registry awareness
  - **Integration Fix**: Scripts now load Note Coordinator's registry to map MIDI notes to original XML Universal IDs
  - **ID Retrieval**: MIDI notes matched to registry entries via pitch+track lookup to recover source Universal IDs
  - **Registry Parsing Logic**: JSON registry deserialization with lookup table construction for efficient note matching
  - **Multi-Tier Matching**: Hierarchical lookup system prioritizing exact pitch+track matches over pitch-only fallbacks
  - **UUID Extraction Algorithm**: Regex-based filename parsing to extract and preserve 4-character UUID suffixes
  - **Cross-Pipeline Propagation**: Filename transformation preservation through MIDI→Audio→Keyframe conversion chain
  - **Metadata Integration**: Note attribute extraction from filenames with UUID embedding in output JSON structures
  - **Confidence-Based Selection**: Weighted scoring system preventing duplicate ID assignment across pipeline stages
  - **Conditional Registry Integration**: Parameter injection logic based on orchestrator configuration flags
  - **Graceful Fallback**: Sequential ID generation when registry unavailable with transparent mode switching
- **v1.3.0**: 60Hz keyframe generation for YouTube compatibility
- **v1.2.0**: SGM-V2.01 soundfont integration for realistic audio
- **v1.1.0**: Simplified amplitude-only keyframe output
- **v1.0.0**: Codebase cleanup with fast-only versions

---

🎼 **Ready to transform your musical notation into synchronized After Effects animations with ornament detection and sustain pedal expression!**