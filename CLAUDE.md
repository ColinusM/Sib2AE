# CLAUDE.md

Sib2Ae: Music notation to After Effects synchronization pipeline

## Overview
A comprehensive orchestration system that transforms MusicXML/MIDI/SVG to synchronized After Effects animations. Features the Universal ID Pipeline Orchestrator for coordinated execution of Symbolic Separators (SVG processing) + Audio Separators (MIDI processing) + Note Coordinator (Universal ID registry creation), maintaining synchronization relationships throughout all processing stages.

## Setup
```bash
uv sync
```

## GUI Interface
**Modular graphical interface for running pipeline scripts:**

```bash
# Launch the GUI (recommended)
python3 gui/launch_gui.py
```

**GUI Features:**
- **Symbolic Pipeline Tab**: Run 5 symbolic processing scripts with file browsers
- **Audio Pipeline Tab**: Execute 3 audio rendering and keyframe generation scripts
- **Matching Tab**: MIDI-XML-SVG coordination with annotated SVG output
- **Real-time output**: View script output directly in GUI

**GUI Architecture:**
- **Main File**: `gui/sib2ae_gui.py` - Modular architecture (140 lines)
- **Tabs**: `gui/symbolic_tab.py`, `gui/audio_tab.py`, `gui/matching_tab.py`
- **Core**: `gui/settings.py`, `gui/script_runner.py`
- **Settings**: `gui_settings.json` - Auto-saved preferences

## Architecture

### Core Structure
```
Brain/                                 # CORE PIPELINE SYSTEM
├── Base/                              # SOURCE SCORES (organized by articulation/export type)
│   ├── Acciatura/                     # SOURCE: Grace note (acciaccatura) test case
│   │   ├── Saint-Saens Trio No 2.musicxml
│   │   ├── Saint-Saens Trio No 2.svg
│   │   └── Saint-Saens Trio No 2.mid
│  
├── App/                               # Individual processing tools (9 scripts)
│   ├── Symbolic Separators/           # 6 SVG/MusicXML processing scripts
│   └── Audio Separators/              # 3 MIDI/audio processing scripts
└── orchestrator/                      # Universal ID Pipeline Orchestrator (17 modules, 8469 lines)
    ├── universal_orchestrator.py       # Master pipeline coordinator
    ├── note_coordinator.py             # Universal ID registry creation
    ├── ornament_coordinator.py         # Ornament detection coordinator (NEW)
    ├── ornament_xml_parser.py          # XML ornament tag parser (NEW)
    ├── ornament_svg_parser.py          # SVG ornament symbol detector (NEW)
    ├── ornament_symbol_creator.py      # Ornament SVG generator (NEW)
    ├── orphan_midi_detector.py         # Orphan MIDI note detector (NEW)
    ├── tied_note_processor.py          # Tied note relationship processing
    ├── xml_temporal_parser.py          # MusicXML temporal parsing utilities
    ├── midi_matcher.py                 # MIDI note matching utilities
    ├── pipeline_stage.py               # Pipeline stage definitions
    ├── universal_registry.py           # Universal ID tracking system
    ├── registry_utils.py               # Standardized registry access utilities
    ├── smart_log_aggregator.py         # Intelligent output aggregation (NEW)
    ├── manifest_manager.py             # Atomic manifest operations
    ├── progress_tracker.py             # Real-time progress tracking
    ├── error_handlers.py               # Circuit breaker and retry mechanisms
    └── __init__.py                     # Package exports

gui/                                   # MODULAR GUI SYSTEM
├── launch_gui.py                      # Python GUI launcher
├── launch_gui.sh                      # Shell GUI launcher
├── sib2ae_gui.py                      # Main GUI application
├── symbolic_tab.py                    # Symbolic pipeline interface
├── audio_tab.py                       # Audio pipeline interface
├── matching_tab.py                    # Note coordination interface
├── settings.py                        # GUI settings management
├── script_runner.py                   # Script execution handler
└── gui_settings.json                  # Auto-saved preferences

outputs/                               # ORGANIZED OUTPUT STRUCTURE
├── svg/                               # Visual elements for After Effects
│   ├── instruments/                   # Per-instrument SVG files
│   ├── noteheads/                     # Individual notehead animations
│   ├── staff_barlines/                # Background elements
│   └── annotated/                     # SVGs with timing labels
├── audio/                             # Audio files organized by instrument
│   ├── Flûte/                         # Flute audio files (.wav)
│   └── Violon/                        # Violin audio files (.wav)
├── json/                              # Metadata and animation data
│   ├── keyframes/                     # After Effects keyframe data
│   ├── coordination/                  # Universal ID registry
│   └── manifests/                     # Pipeline execution tracking
└── midi/                              # Individual MIDI note files

universal_output/                      # ORCHESTRATOR COORDINATION HUB
├── universal_notes_registry.json      # Complete Universal ID database
├── coordination_metadata.json         # Master coordination statistics
├── midi_pipeline_manifest.json        # Audio processing tracking
├── svg_pipeline_manifest.json         # Visual processing tracking
├── tied_note_assignments.json         # Tied note relationships
├── logs/                              # Execution logs and progress tracking
└── shell_output/                      # Smart verbose logging with intelligent aggregation
    └── execution_output.log           # Rich execution logs with pattern recognition
```

## Pipeline Execution

### Universal ID Pipeline Orchestrator (Recommended)
**Complete automated pipeline execution with Universal ID preservation and Smart Verbose Logging:**

```bash
# RECOMMENDED: Smart Verbose Mode - Zero console pollution, rich file logs, automatic cleanup
python -m Brain.orchestrator.universal_orchestrator \
    "Brain/Base/SS 9.musicxml" \
    "Brain/Base/Saint-Saens Trio No 2.mid" \
    --svg "Brain/Base/SS 9 full.svg" \
    --mode sequential --quiet > /dev/null 2>&1

# Preserve previous results (disable automatic cleanup)
python -m Brain.orchestrator.universal_orchestrator \
    "Brain/Base/SS 9.musicxml" \
    "Brain/Base/Saint-Saens Trio No 2.mid" \
    --svg "Brain/Base/SS 9 full.svg" \
    --mode sequential --no-cleanup --quiet > /dev/null 2>&1

# Full pipeline with verbose console output (for debugging)
python -m Brain.orchestrator.universal_orchestrator \
    "Brain/Base/SS 9.musicxml" \
    "Brain/Base/Saint-Saens Trio No 2.mid" \
    --svg "Brain/Base/SS 9 full.svg" \
    --mode sequential

# Audio-only pipeline (without SVG processing)
python -m Brain.orchestrator.universal_orchestrator \
    "Brain/Base/SS 9.musicxml" \
    "Brain/Base/Saint-Saens Trio No 2.mid" \
    --mode sequential --quiet > /dev/null 2>&1
```

**Orchestrator Features:**
- **Ornament Detection**: Automatic detection of trills, mordents, grace notes (acciaccatura/appoggiatura)
  - 3-way coordination: XML tags + SVG symbols + orphan MIDI clustering
  - Enabled by default (use `--disable-ornaments` to turn off)
- **Automatic Output Cleanup**: Clears previous pipeline results for clean execution (use `--no-cleanup` to preserve)
- **Smart Verbose Logging**: Intelligent aggregation with pattern recognition and anomaly detection
- **Zero Console Pollution**: Rich file logs without Claude Code context contamination
- **Universal ID Preservation**: Maintains unique identifiers across all pipeline stages (including ornaments)
- **Registry Architecture**: Standardized Universal ID access via registry utilities
- **Atomic Operations**: Safe manifest updates with backup and recovery
- **Circuit Breaker Pattern**: Robust error handling and failure recovery
- **Real-time Progress Tracking**: Universal ID-level granularity progress reporting
- **Pipeline Coordination**: Sequential and parallel execution modes

### Individual Script Execution
For development and testing, scripts can be run individually:

#### Symbolic Pipeline (6 stages)
```bash
# 1. Extract noteheads from MusicXML with pixel-perfect coordinates
python "Brain/App/Symbolic Separators/truly_universal_noteheads_extractor.py" "Brain/Base/SS 9.musicxml"

# 2. Remove noteheads from full SVG while preserving other elements
python "Brain/App/Symbolic Separators/truly_universal_noteheads_subtractor.py" "Brain/Base/SS 9.musicxml" "Brain/Base/SS 9 full.svg"

# 3. Create individual SVG files per instrument
python "Brain/App/Symbolic Separators/xml_based_instrument_separator.py" "Brain/Base/SS 9.musicxml" "Brain/Base/SS 9 full.svg" "outputs/svg/instruments"

# 4. Create one SVG file per notehead for After Effects animation
python "Brain/App/Symbolic Separators/individual_noteheads_creator.py" "Brain/Base/SS 9.musicxml"

# 5. Extract staff lines and barlines for background elements
python "Brain/App/Symbolic Separators/staff_barlines_extractor.py" "Brain/Base/SS 9.musicxml" "Brain/Base/SS 9 full.svg"

# 6. Extract ornament symbols (trills, mordents, accents) as individual SVG files
python "Brain/App/Symbolic Separators/ornament_symbols_extractor.py" "Brain/Base/Trill/Saint-Saens Trio No 2.svg"
```

#### Audio Pipeline (3 stages)
```bash
# 1. Split MIDI into individual note files (foundation)
python "Brain/App/Audio Separators/midi_note_separator.py" "Brain/Base/Saint-Saens Trio No 2.mid"

# 2. Convert to audio - High-quality 247MB SGM-V2.01 soundfont (parallel, realistic instruments)
python "Brain/App/Audio Separators/midi_to_audio_renderer_fast.py" "outputs/midi"

# 3. Generate keyframes - Amplitude-only (clean AE integration, no over-engineering)
python "Brain/App/Audio Separators/audio_to_keyframes_fast.py" "outputs/audio"
```

#### Note Coordination
```bash
# Create Universal ID registry linking all data sources
python "Brain/orchestrator/note_coordinator.py" "Brain/Base/SS 9.musicxml" "Brain/Base/Saint-Saens Trio No 2.mid" "universal_output"
```

## Working Directory
**Important:** Run all commands from: `/Users/colinmignot/Claude Code/Sib2Ae/`

## Quick Verification Commands
```bash
# Verify pipeline completion
find outputs/ -name "*.wav" | wc -l          # Count audio files
find outputs/ -name "*.svg" | wc -l          # Count SVG files
find outputs/ -name "*keyframes*.json" | wc -l # Count keyframes

# Check orchestrator coordination
ls -la universal_output/                     # Coordination hub
ls -la outputs/                              # Main outputs

# Monitor smart verbose logs (recommended)
tail -f universal_output/shell_output/execution_output.log

# Monitor basic progress logs
tail -f universal_output/logs/progress.log | grep "Stage completed"
```

## Universal ID System
**Core synchronization principle:** Audio waveforms are NOT matched to noteheads after creation. Instead, both visual coordinates and audio keyframes are derived from the same source note with a Universal ID that preserves relationships throughout the pipeline.

**Universal ID Bridge Example:**
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

## Technical Specifications

### Coordinate System
- **X Transformation**: `svg_x = xml_x * 3.206518 + 564.93`
- **Y Positioning**: Staff-based with 380px separation between staves
- **Staff Layout**: Dynamic positioning based on instrument count
- **Helsinki Special Std**: Notehead codes `\u0046` (hollow), `\u0066` (filled)

### Audio Specifications
- **Standard Mode**: 44kHz sample rate, sequential processing, high quality
- **Fast Mode**: 22kHz sample rate, 6 parallel workers, optimized for development
- **Keyframe Rate**: 60 FPS for YouTube compatibility (upgraded from 30 FPS)
- **Format**: WAV files, simplified JSON keyframe data (amplitude-only)
- **Audio Engine**: FluidSynth + librosa processing
- **Soundfont**: SGM-V2.01 (247MB) located in `soundfonts/SGM_V2_final.sf2`

### File Naming Conventions
- **MIDI**: `note_XXX_Instrument_Pitch_velYY.mid`
- **Audio**: `note_XXX_Instrument_Pitch_velYY.wav`
- **Keyframes**: `note_XXX_Instrument_Pitch_velYY_keyframes.json`
- **SVG**: `notehead_PartID_Pitch_MeasureN.svg`

### Processing Framework
- **XML/SVG**: `xml.etree.ElementTree` for parsing, MusicXML as source of truth
- **SVG Elements**: Staff lines (stroke-width: 2.25), Barlines (stroke-width: 5)
- **Universal ID**: UUID4 format for unique note identification
- **Error Handling**: Circuit breaker patterns with exponential backoff retry

## Performance Characteristics

### Pipeline Execution Times
- **Symbolic Pipeline**: ~0.5s total (5 stages, pixel-perfect coordinate processing)
- **Audio Pipeline**: 0.7-1s (fast mode with SGM-V2.01 soundfont)
- **Note Coordination**: ~0.1s (Universal ID registry creation)
- **Complete Pipeline**: ~6-8s total execution time

### Recent Optimizations (September 2025)
- **60Hz Keyframes**: True 60 data points/second for YouTube compatibility
- **Audio Quality**: SGM-V2.01 soundfont eliminates synthetic/noise artifacts
- **Simplified Output**: Amplitude-only keyframes for clean After Effects integration
- **Sequential Frames**: Eliminates keyframe conflicts with consecutive frame indexing

### Scalability
- **Note Count**: Linear scaling with number of musical notes
- **Parallel Processing**: Fast modes utilize 6 worker processes
- **Memory Usage**: Optimized for large musical scores
- **File I/O**: Efficient batch processing patterns
- **Universal ID Tracking**: Maintains relationships across 100+ notes

### Output Generation
- **SVG Files**: 10-15 files (instruments, noteheads, staff elements)
- **Audio Files**: 1 per MIDI-matched note (6-10 typical)
- **Keyframe Files**: 60 FPS data, ~160 keyframes per 2.7s audio file
- **Coordination Files**: Universal ID registry and manifests
- **Soundfont Files**: High-quality SGM-V2.01 (247MB, stored in `soundfonts/`)

## After Effects Integration

### Import Tools
- **CEP Extension** (`Brain/Extensions/Sib2Ae-Importer/`) - Professional dockable panel with HTML5 interface
- **ExtendScript** (`Brain/Scripts/Sib2Ae_Importer.jsx`) - Rapid testing script, no installation required

### Import Process
1. **Select Output Folders**: Point to `outputs/` and `universal_output/`
2. **Choose Import Options**: SVG (visual elements), Audio (waveforms), JSON (keyframes)
3. **Automated Composition**: Creates organized After Effects project with synchronized layers

### Integration Points
- **SVG Files**: Vector graphics with precise positioning for animation layers
- **Audio Files**: Synchronized waveforms for timing reference and analysis
- **Keyframe Data**: Automated animation properties (amplitude-only, 60 FPS)
- **Universal ID System**: Maintains frame-accurate synchronization relationships

## Documentation

### Comprehensive Guides
- **`Brain/orchestrator/README.md`** - Universal ID Pipeline Orchestrator with Ornament Detection
  - 17 modules including ornament detection system (ornament_coordinator, XML/SVG parsers, orphan detector)
  - Complete API reference and configuration options
  - Ornament detection: grace notes, trills, mordents with 3-way coordination
  - Smart logging and automatic output cleanup
  - Circuit breaker patterns and error handling

- **`Brain/App/README.md`** - Symbolic and Audio Separators with Ornament Compatibility
  - 8 scripts (5 symbolic, 3 audio) with ornament expansion support
  - Detailed script usage and command examples
  - Pedal detection (CC 64) and ornament processing
  - Performance characteristics and technical specifications

### Quick Reference
- **`gui/`** - Modular GUI system with tabbed interface
- **`docs/`** - Technical documentation and API references
- **`scripts/`** - Utility scripts and analysis tools

## Dependencies
- **Core**: svgelements, pydantic, click, pytest
- **Audio**: mido, librosa, soundfile, fluidsynth (`brew install fluidsynth`)
- **GUI**: tkinter (built-in Python), threading
- **Orchestrator**: tqdm (progress bars), pathlib, dataclasses
- **After Effects**: CEP 12, ExtendScript support
- **Soundfont**: SGM-V2.01 (247MB, must be downloaded separately)

## Soundfont Setup
- **Required File**: `soundfonts/SGM_V2_final.sf2` (247MB)
- **Download**: Must be obtained separately due to file size
- **Fallback**: System FluidSynth paths available as backup
- **Organization**: All soundfonts stored in `soundfonts/` directory

## Claude Code Usage Notes
- **CRITICAL**: Always use `--quiet > /dev/null 2>&1` for zero console pollution with rich file logs
- **Smart Logging**: Execution logs saved to `universal_output/shell_output/execution_output.log`
- **Verification**: Use quick commands (`find outputs/ -name "*.wav" | wc -l`) to check completion
- **Monitoring**: Monitor `universal_output/shell_output/execution_output.log` for intelligent summaries
- **Module Execution**: Prefer `python -m Brain.orchestrator.universal_orchestrator` syntax
- **Audio Quality**: Ensure SGM-V2.01 soundfont is present in `soundfonts/` for realistic instrument sounds
- **Keyframe Rate**: Pipeline now generates 60 FPS keyframes for YouTube compatibility

---

🎼 **Ready to transform your musical notation into synchronized After Effects animations with ornament detection, sustain pedal, and Universal ID precision!**