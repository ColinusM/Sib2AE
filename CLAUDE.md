# CLAUDE.md

Sib2Ae: Music notation to After Effects synchronization pipeline

## Overview
Converts MusicXML/MIDI/SVG to synchronized After Effects animations. Two pipelines: Symbolic Separators (SVG processing) + Audio Separators (MIDI processing) + Synchronizer (coordination).

## Setup
```bash
uv sync
```

## GUI Interface
**Easy-to-use graphical interface for running all pipeline scripts:**

```bash
# Launch the GUI (recommended)
python3 sib2ae_gui.py
# OR using shell script
./launch_gui.sh
```

**GUI Features:**
- **Symbolic Pipeline Tab**: Run all symbolic processing scripts with file browsers
- **Audio Pipeline Tab**: Execute audio rendering and keyframe generation
- **Master Pipeline Tab**: One-click complete workflow execution
- **Output Log Tab**: Real-time script output and progress monitoring
- **Quick Actions**: Open output directories, check dependencies, view generated files

**GUI Configuration:**
- **Main File**: `/Users/colinmignot/Claude Code/Sib2Ae/sib2ae_gui.py`
- **Settings**: `gui_settings.json` - Window position/preferences auto-saved
- **Launch Script**: `launch_gui.sh` - Python availability check
- **Always On Top**: Stays visible for workflow efficiency

## Data Structure
```
PRPs-agentic-eng/
├── Base/                              # Input data files
│   ├── SS 9.musicxml                  # Source MusicXML score
│   ├── SS 9 full.svg                  # Complete SVG score (43KB)
│   ├── Saint-Saens Trio No 2.mid     # Source MIDI file
│   └── Saint-Saens Trio No 2_individual_notes/  # Generated MIDI notes
│       ├── note_000_Flûte_A4_vel76.mid
│       ├── note_001_Flûte_G4_vel76.mid
│       ├── note_002_Violon_B3_vel65.mid
│       └── ... (6 total notes)
├── Audio/                             # Generated audio files
│   ├── Flûte/
│   │   ├── note_000_Flûte_A4_vel76.wav  # ~1MB each
│   │   └── note_001_Flûte_G4_vel76.wav
│   ├── Violon/
│   │   ├── note_002_Violon_B3_vel65.wav
│   │   ├── note_003_Violon_A3_vel66.wav
│   │   ├── note_004_Violon_C4_vel65.wav
│   │   └── note_005_Violon_B3_vel64.wav
│   └── Keyframes/                     # JSON keyframe data
├── instruments_output/                # Separated SVGs by instrument
│   ├── Flûte_P1.svg                  # ~37KB
│   └── Violon_P2.svg                 # ~38KB
└── universal_output/                  # Coordination metadata
    ├── coordination_metadata.json
    ├── midi_pipeline_manifest.json
    ├── svg_pipeline_manifest.json
    └── universal_notes_registry.json
```

## Core Pipelines

### Symbolic Pipeline
```bash
# Master pipeline (orchestrates all symbolic processing) - RECOMMENDED
python "PRPs-agentic-eng/App/Symbolic Separators/sib2ae_master_pipeline.py" "SS 9" "symbolic_output"
# Creates complete instrument-focused folder structure with all processed files

# OR run individual tools:

# Extract noteheads from MusicXML with pixel-perfect coordinate transformation
python "PRPs-agentic-eng/App/Symbolic Separators/truly_universal_noteheads_extractor.py" "PRPs-agentic-eng/Base/SS 9.musicxml"

# Remove noteheads from full SVG while preserving all other musical elements
python "PRPs-agentic-eng/App/Symbolic Separators/truly_universal_noteheads_subtractor.py" "PRPs-agentic-eng/Base/SS 9.musicxml" "PRPs-agentic-eng/Base/SS 9 full.svg"

# Create individual SVG files per instrument using universal Y-coordinate staff mapping
python "PRPs-agentic-eng/App/Symbolic Separators/xml_based_instrument_separator.py" "PRPs-agentic-eng/Base/SS 9.musicxml" "PRPs-agentic-eng/Base/SS 9 full.svg" "instruments_output"

# Create one SVG file per notehead for After Effects animation
python "PRPs-agentic-eng/App/Symbolic Separators/individual_noteheads_creator.py" "PRPs-agentic-eng/Base/SS 9.musicxml"

# Extract only staff lines and barlines for background elements (optional)
python "PRPs-agentic-eng/App/Symbolic Separators/staff_barlines_extractor.py" "PRPs-agentic-eng/Base/SS 9.musicxml" "PRPs-agentic-eng/Base/SS 9 full.svg"
```

### Audio Pipeline
```bash
# Split MIDI into individual note files (foundation for audio pipeline)
python "PRPs-agentic-eng/App/Audio Separators/midi_note_separator.py" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2.mid"

# Convert to audio (FAST - parallel processing, 22kHz, 6 workers) - RECOMMENDED
python "PRPs-agentic-eng/App/Audio Separators/midi_to_audio_renderer_fast.py" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2_individual_notes"

# Generate keyframes (FAST - parallel processing, reduced density) - RECOMMENDED
python "PRPs-agentic-eng/App/Audio Separators/audio_to_keyframes_fast.py" "PRPs-agentic-eng/Audio"

# Alternative: Standard audio rendering (sequential, 44kHz, higher quality)
python "PRPs-agentic-eng/App/Audio Separators/midi_to_audio_renderer.py" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2_individual_notes"

# Alternative: Standard keyframes (full analysis, more comprehensive)
python "PRPs-agentic-eng/App/Audio Separators/audio_to_keyframes.py" "PRPs-agentic-eng/Audio"
```

### Synchronization Pipeline

**Current System (Simplified):**
```bash
# Universal note coordination (recommended for most use cases)
python "PRPs-agentic-eng/note_coordinator.py" "PRPs-agentic-eng/Base/SS 9.musicxml" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2.mid" "universal_output"
```

**Advanced System (Backup Components):**
Located in: `PRPs-agentic-eng/App/Synchronizer 19-26-28-342/`

```bash
# 1. Context Gatherer - Master timing extraction & XML-MIDI-SVG relationships
python "PRPs-agentic-eng/App/Synchronizer 19-26-28-342/context_gatherer.py" "Base/SS 9.musicxml" "Base/Saint-Saens Trio No 2.mid" "Base/SS 9 full.svg"

# 2. Synchronization Coordinator - Master pipeline orchestrator
python "PRPs-agentic-eng/App/Synchronizer 19-26-28-342/synchronization_coordinator.py"
```

**Advanced System Features:**
- **Context Gatherer**: Master MIDI timing preservation, tied note handling (3:1 relationships), confidence scoring
- **MIDI Matcher**: Tolerance-based matching (100ms), multi-factor scoring, unquantized MIDI support
- **Tied Note Processor**: Visual-temporal mismatch handling, proportional timing calculation
- **Master MIDI Extractor**: Authoritative timing reference preservation, tempo maps
- **Synchronization Coordinator**: Sequential/parallel execution modes, performance optimization

## Working Directory
**Important:** Run all commands from the project root directory: `/Users/colinmignot/Claude Code/Sib2Ae/`

## Output Directories
- **`PRPs-agentic-eng/Audio/`** - Audio files organized by instrument
- **`PRPs-agentic-eng/instruments_output/`** - Individual SVG files per instrument
- **`PRPs-agentic-eng/universal_output/`** - Synchronization coordination files
- **`symbolic_output/`** - Master pipeline output (when using sib2ae_master_pipeline.py)

## Key Technical Details

### Coordinate System
- Staff 0: Y 950-1100, Staff 1: Y 1250-1500, Staff 2: Y 1650-1800, Staff 3: Y 2050-2200
- Notehead codes: `\u0046` (hollow), `\u0066` (filled)
- Staff lines: stroke-width="2.25", Barlines: stroke-width="5"

### Requirements
- Use `xml.etree.ElementTree` for XML/SVG processing
- MusicXML is source of truth for relationships  
- 30 FPS timing for After Effects
- FluidSynth + librosa for audio processing

## Agent Integration

**MUST USE specialized agents for ALL Sib2Ae work:**

### sib2ae-sync-orchestrator
Default agent for ALL music notation/pipeline implementation work. Always reads debug knowledge before starting any task.

### sib2ae-pipeline-debugger  
Auto-triggers on build/run failures. Updates debug knowledge base after successful fixes.

**Workflow:** Any Sib2Ae Task → sib2ae-sync-orchestrator → Testing → Failure → sib2ae-pipeline-debugger → Fix + Learn → Continue

**Knowledge Base:** `/docs/music-debug-knowledge.md`

## File Descriptions

### Symbolic Separators (All files useful - Modified July 27, 2024)

#### **ESSENTIAL PRODUCTION SCRIPTS:**
- **`sib2ae_master_pipeline.py`** (10KB) - Master orchestrator for entire symbolic workflow. Runs all 4 tools in sequence and creates instrument-focused folder structure for After Effects.
- **`truly_universal_noteheads_extractor.py`** (8.8KB) - Pixel-perfect coordinate transformation from MusicXML to SVG noteheads. Universal MusicXML compatibility with Helsinki Special Std font support.
- **`truly_universal_noteheads_subtractor.py`** (8.3KB) - Removes noteheads from full SVG with pinpoint accuracy while preserving all other musical elements.
- **`xml_based_instrument_separator.py`** (9.2KB) - Creates individual SVG files per instrument using universal Y-coordinate staff mapping (supports up to 4 staves).
- **`individual_noteheads_creator.py`** (8.8KB) - Creates one SVG file per notehead with exact coordinates, perfect for After Effects animation.

#### **SPECIALIZED/OPTIONAL:**
- **`staff_barlines_extractor.py`** (11.4KB) - Extracts only staff lines and barlines from full SVG, useful for background elements and structural analysis.

### Audio Separators (All files useful - Modified July 27, 2024)

#### **ESSENTIAL PRODUCTION SCRIPTS:**
- **`midi_note_separator.py`** (7.3KB) - Splits MIDI files into individual note files. Foundation script for the entire audio pipeline.

#### **FAST VERSIONS (RECOMMENDED):**
- **`midi_to_audio_renderer_fast.py`** (8.6KB) - Parallel processing audio renderer (6 workers, 22kHz sample rate, 10s timeouts). 2x faster than standard version.
- **`audio_to_keyframes_fast.py`** (11.1KB) - Parallel keyframe generator with reduced density. Creates 72 keyframes per file vs 1000+. Essential properties only (scale, opacity, hue, position_x).

#### **STANDARD VERSIONS (BACKUP/QUALITY):**
- **`midi_to_audio_renderer.py`** (8KB) - Standard sequential audio renderer (44kHz sample rate, 30s timeouts). Higher quality but slower.
- **`audio_to_keyframes.py`** (12.3KB) - Full feature analysis keyframe generator. More comprehensive analysis but slower processing.

## Synchronization Systems Comparison

### Current System: `note_coordinator.py`
**Location**: `PRPs-agentic-eng/note_coordinator.py`

**Features:**
- Unified, single-file approach for all coordination
- Universal ID system linking XML, MIDI, and SVG data
- Basic pitch + enharmonic matching
- Simple coordinate transformation
- Outputs to `universal_output/` with JSON manifests

**Usage**: Recommended for most use cases due to simplicity

### Advanced System: Multi-Component Synchronizer
**Location**: `PRPs-agentic-eng/App/Synchronizer 19-26-28-342/`

**Components:**
1. **Context Gatherer** (`context_gatherer.py`) - Master timing extraction & relationship analysis
2. **MIDI Matcher** (`utils/midi_matcher.py`) - Tolerance-based matching with confidence scoring
3. **Tied Note Processor** (`utils/tied_note_processor.py`) - Handles 3:1 notehead-to-MIDI relationships
4. **Master MIDI Extractor** (`utils/master_midi_extractor.py`) - Authoritative timing preservation
5. **Synchronization Coordinator** (`synchronization_coordinator.py`) - Pipeline orchestrator

**Advanced Features:**
- **Tied Note Handling**: Manages 3 visual noteheads → 1 MIDI note relationships
- **Master Timing Preservation**: Extracts authoritative reference from original MIDI before processing
- **Tolerance-Based Matching**: Configurable 100ms tolerance with multi-factor confidence scoring
- **Performance Modes**: Sequential vs parallel execution
- **Comprehensive Analysis**: Visual-temporal mismatch handling, tempo maps, accuracy metrics

**Usage**: For complex scores with tied notes, unquantized MIDI, or when maximum accuracy is required

### Core Synchronization Principle

**Critical Insight**: Both systems use the same fundamental approach:

**Audio waveforms are NOT matched to noteheads after creation** - instead, both the visual notehead coordinates and audio keyframes are **derived from the same source note** with a **Universal ID** that preserves relationships throughout the pipeline.

**The Universal ID Bridge:**
```json
{
  "universal_id": "2584802d-2469-4e45-8cf0-ff934e1032d7",
  "xml_data": {"part_id": "P1", "note_name": "A4", "svg_x": 3178, "svg_y": 1049},
  "midi_data": {"start_time_seconds": 7.5, "velocity": 76},
  "audio_filename": "note_000_Flûte_A4_vel76.wav",
  "keyframes_filename": "note_000_Flûte_A4_vel76_keyframes.json"
}
```

**File Chain Preservation:**
```
note_000_Flûte_A4_vel76.mid → .wav → _keyframes.json
```

**Result**: **Pixel-perfect synchronization** because:
1. Visual coordinates from MusicXML → SVG transformation
2. Audio waveform from same MIDI note → audio analysis
3. Both linked by consistent naming + Universal ID
4. Timing preserved through master MIDI reference

### Architecture Comparison

| Feature | Current System | Advanced System |
|---------|---------------|-----------------|
| **Complexity** | Single unified file | 5-component architecture |
| **Tied Notes** | Basic handling | Advanced 3:1 relationship management |
| **Timing** | Simple transformation | Master timing preservation + tempo maps |
| **Matching** | Pitch + enharmonic | Tolerance-based + confidence scoring |
| **Performance** | Sequential | Parallel execution modes |
| **Output** | Universal registry | Master synchronization JSON |
| **MIDI Handling** | Basic | Unquantized MIDI support |
| **File Size** | 21KB | 120KB+ total |

## Status: All Scripts Useful
Every script serves a production purpose:
- **Primary workflow**: Master pipeline + fast audio versions
- **Quality options**: Standard audio renderers for quality vs speed trade-offs
- **Specialized tools**: Staff extractor for specific background element needs
- **Synchronization options**: Simple coordination vs advanced multi-component system

## After Effects Import Tools

### CEP Extension (Professional)
**Location**: `PRPs-agentic-eng/Extensions/Sib2Ae-Importer/`

**Installation**:
```bash
# Copy to CEP extensions directory
# macOS: /Library/Application Support/Adobe/CEP/extensions/
# Windows: C:\Program Files (x86)\Common Files\Adobe\CEP\extensions\

# Enable debug mode
defaults write com.adobe.CSXS.12 PlayerDebugMode 1  # macOS
# Windows: Set registry HKEY_CURRENT_USER\Software\Adobe\CSXS.12 "PlayerDebugMode"="1"

# Restart After Effects
# Access via: Window > Extensions > Sib2Ae Importer
```

**Features**:
- Modern HTML5/CSS3 interface
- Real-time file preview
- Selective import options (SVG/audio/JSON)
- Dockable panel integration
- Theme matching with After Effects
- Progress tracking and status logging

### ExtendScript (Rapid Testing)
**Location**: `PRPs-agentic-eng/Scripts/Sib2Ae_Importer.jsx`

**Usage**:
```bash
# No installation required - run directly:
# File > Scripts > Run Script File... > Select Sib2Ae_Importer.jsx
# OR copy to AE Scripts folder for menu access

# MAJOR ADVANTAGE: No restart required!
# Edit script → Run immediately → Perfect for development
```

**Features**:
- ScriptUI interface with file preview
- Recursive folder scanning
- Auto-composition creation
- Immediate testing workflow
- Single file distribution

### Import Workflow
Both tools import pipeline results:

```bash
# 1. Run pipeline to generate outputs
python "PRPs-agentic-eng/App/Symbolic Separators/sib2ae_master_pipeline.py" "SS 9" "symbolic_output"
python "PRPs-agentic-eng/App/Audio Separators/midi_to_audio_renderer_fast.py" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2_individual_notes"

# 2. Import to After Effects
# Via Extension: Window > Extensions > Sib2Ae Importer
# Via Script: File > Scripts > Run Script File > Sib2Ae_Importer.jsx

# 3. Select pipeline output folder
# 4. Choose import options (SVG/audio/JSON)
# 5. Import creates organized composition
```

**Supported Imports**:
- **SVG Files**: `instruments_output/*.svg` → AE layers
- **Audio Files**: `Audio/*/*.wav` → AE audio layers
- **JSON Files**: `Audio/Keyframes/*.json` → Keyframe data processing
- **Auto-Organization**: Creates composition with properly named layers

### Development Choice
- **CEP Extension**: Professional end-user tool, rich UI, dockable panels
- **ExtendScript**: Rapid development/testing, no restart needed, instant iteration

## Dependencies
Core: svgelements, pydantic, click, pytest
Audio: mido, librosa, soundfile, fluidsynth (brew install)
After Effects: CEP 12, ExtendScript support