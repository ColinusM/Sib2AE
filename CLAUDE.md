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
# Launch the GUI
python3 sib2ae_gui.py
# OR
./launch_gui.sh
```

**GUI Features:**
- **Symbolic Pipeline Tab**: Run all symbolic processing scripts with file browsers
- **Audio Pipeline Tab**: Execute audio rendering and keyframe generation
- **Master Pipeline Tab**: One-click complete workflow execution
- **Output Log Tab**: Real-time script output and progress monitoring
- **Quick Actions**: Open output directories, check dependencies, view generated files

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
```bash
# Coordinate XML-MIDI-SVG timing
python "PRPs-agentic-eng/Synchronizer/context_gatherer.py" "PRPs-agentic-eng/Base/SS 9.musicxml" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2.mid"

# Full synchronization (outputs to universal_output/)
python "PRPs-agentic-eng/Synchronizer/synchronization_coordinator.py"
```

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

## Status: All Scripts Useful
Every script serves a production purpose:
- **Primary workflow**: Master pipeline + fast audio versions
- **Quality options**: Standard audio renderers for quality vs speed trade-offs
- **Specialized tools**: Staff extractor for specific background element needs

## Dependencies
Core: svgelements, pydantic, click, pytest
Audio: mido, librosa, soundfile, fluidsynth (brew install)