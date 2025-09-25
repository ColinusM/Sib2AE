# CLAUDE.md

Sib2Ae: Music notation to After Effects synchronization pipeline

## Overview
Converts MusicXML/MIDI/SVG to synchronized After Effects animations using individual tools: Symbolic Separators (SVG processing) + Audio Separators (MIDI processing) + Note Coordinator (MIDI-XML-SVG matching).

## Setup
```bash
uv sync
```

## GUI Interface
**Modular graphical interface for running pipeline scripts:**

```bash
# Launch the GUI (recommended)
python3 launch_gui.py
```

**GUI Features:**
- **Symbolic Pipeline Tab**: Run 5 symbolic processing scripts with file browsers
- **Audio Pipeline Tab**: Execute 4 audio rendering and keyframe generation scripts
- **Matching Tab**: MIDI-XML-SVG coordination with annotated SVG output
- **Real-time output**: View script output directly in GUI

**GUI Architecture:**
- **Main File**: `gui/sib2ae_gui.py` - Modular architecture (140 lines)
- **Tabs**: `gui/symbolic_tab.py`, `gui/audio_tab.py`, `gui/matching_tab.py`
- **Core**: `gui/settings.py`, `gui/script_runner.py`
- **Settings**: `gui_settings.json` - Auto-saved preferences

## Data Structure
```
PRPs-agentic-eng/
├── Base/                              # INPUT FILES
│   ├── SS 9.musicxml                  # Source MusicXML score
│   ├── SS 9 full.svg                  # Complete SVG score
│   └── Saint-Saens Trio No 2.mid     # Source MIDI file
├── Audio/                             # OUTPUT: Generated audio files
│   ├── Flûte/                         # Audio files by instrument
│   ├── Violon/
│   └── Keyframes/                     # JSON keyframe data for After Effects
├── instruments_output/                # OUTPUT: Separated SVGs by instrument
│   ├── Flûte_P1.svg
│   └── Violon_P2.svg
└── universal_output/                  # OUTPUT: Coordination metadata
    ├── coordination_metadata.json
    ├── midi_pipeline_manifest.json
    ├── svg_pipeline_manifest.json
    └── universal_notes_registry.json

# Additional project folders:
├── docs/                              # Technical documentation
├── Implementation Summaries/          # Detailed implementation docs
├── scripts/                           # Utility and analysis scripts
└── gui/                              # Modular GUI components
```

## Core Pipelines

### Symbolic Pipeline
**Individual tools for SVG processing:**

```bash
# 1. Extract noteheads from MusicXML with pixel-perfect coordinates
python "PRPs-agentic-eng/App/Symbolic Separators/truly_universal_noteheads_extractor.py" "PRPs-agentic-eng/Base/SS 9.musicxml"

# 2. Remove noteheads from full SVG while preserving other elements
python "PRPs-agentic-eng/App/Symbolic Separators/truly_universal_noteheads_subtractor.py" "PRPs-agentic-eng/Base/SS 9.musicxml" "PRPs-agentic-eng/Base/SS 9 full.svg"

# 3. Create individual SVG files per instrument
python "PRPs-agentic-eng/App/Symbolic Separators/xml_based_instrument_separator.py" "PRPs-agentic-eng/Base/SS 9.musicxml" "PRPs-agentic-eng/Base/SS 9 full.svg" "instruments_output"

# 4. Create one SVG file per notehead for After Effects animation
python "PRPs-agentic-eng/App/Symbolic Separators/individual_noteheads_creator.py" "PRPs-agentic-eng/Base/SS 9.musicxml"

# 5. Extract staff lines and barlines for background elements
python "PRPs-agentic-eng/App/Symbolic Separators/staff_barlines_extractor.py" "PRPs-agentic-eng/Base/SS 9.musicxml" "PRPs-agentic-eng/Base/SS 9 full.svg"
```

### Audio Pipeline
**Individual tools for MIDI-to-audio processing:**

```bash
# 1. Split MIDI into individual note files (foundation)
python "PRPs-agentic-eng/App/Audio Separators/midi_note_separator.py" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2.mid"

# 2. Convert to audio - FAST version (parallel, 22kHz, 6 workers)
python "PRPs-agentic-eng/App/Audio Separators/midi_to_audio_renderer_fast.py" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2_individual_notes"

# 3. Generate keyframes - FAST version (reduced density, essential properties)
python "PRPs-agentic-eng/App/Audio Separators/audio_to_keyframes_fast.py" "PRPs-agentic-eng/Audio"

# Alternative: Standard audio rendering (sequential, 44kHz, higher quality)
python "PRPs-agentic-eng/App/Audio Separators/midi_to_audio_renderer.py" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2_individual_notes"

# Alternative: Standard keyframes (full analysis, comprehensive)
python "PRPs-agentic-eng/App/Audio Separators/audio_to_keyframes.py" "PRPs-agentic-eng/Audio"
```

### Note Coordination
**MIDI-XML-SVG matching tool:**

```bash
# Note Coordinator - Creates Universal ID registry linking all data sources
python "PRPs-agentic-eng/note_coordinator.py" "PRPs-agentic-eng/Base/SS 9.musicxml" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2.mid" "universal_output"
```

**Features:**
- Universal ID system linking XML, MIDI, and SVG data
- 66.7% match rate (6/9 notes - normal due to tied notes)
- Outputs coordination metadata and manifests
- Creates annotated SVGs with MIDI timing labels

## Working Directory
**Important:** Run all commands from: `/Users/colinmignot/Claude Code/Sib2Ae/`

## Output Locations
- **`PRPs-agentic-eng/Audio/`** - Audio files organized by instrument + keyframes
- **`PRPs-agentic-eng/instruments_output/`** - Individual SVG files per instrument
- **`universal_output/`** - Coordination metadata from Note Coordinator
- **`output/`** - Annotated SVG files with timing labels

## Technical Details
- **Coordinate System**: Staff 0: Y 950-1100, Staff 1: Y 1250-1500, Staff 2: Y 1650-1800, Staff 3: Y 2050-2200
- **Helsinki Special Std**: Notehead codes `\u0046` (hollow), `\u0066` (filled)
- **SVG Elements**: Staff lines stroke-width="2.25", Barlines stroke-width="5"
- **Processing**: `xml.etree.ElementTree` for XML/SVG, MusicXML as source of truth
- **Audio**: FluidSynth + librosa, 30 FPS timing for After Effects

## Project Documentation
- **`docs/`** - Technical documentation and API references
- **`Implementation Summaries/`** - Detailed implementation documentation for each component
- **`scripts/`** - Utility scripts and analysis tools (matching comparison, etc.)

## Script Details

### Symbolic Separators (PRPs-agentic-eng/App/Symbolic Separators/)
1. **`truly_universal_noteheads_extractor.py`** - Pixel-perfect coordinate transformation from MusicXML to SVG noteheads
2. **`truly_universal_noteheads_subtractor.py`** - Removes noteheads from full SVG while preserving other elements
3. **`xml_based_instrument_separator.py`** - Creates individual SVG files per instrument (supports up to 4 staves)
4. **`individual_noteheads_creator.py`** - Creates one SVG file per notehead for After Effects animation
5. **`staff_barlines_extractor.py`** - Extracts staff lines and barlines for background elements

### Audio Separators (PRPs-agentic-eng/App/Audio Separators/)
1. **`midi_note_separator.py`** - Splits MIDI files into individual note files (foundation script)
2. **`midi_to_audio_renderer_fast.py`** - Parallel audio renderer (6 workers, 22kHz, fast)
3. **`audio_to_keyframes_fast.py`** - Parallel keyframe generator (reduced density, essential properties)
4. **`midi_to_audio_renderer.py`** - Standard audio renderer (sequential, 44kHz, higher quality)
5. **`audio_to_keyframes.py`** - Standard keyframe generator (full analysis, comprehensive)

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

## After Effects Import
**Import tools located in**: `PRPs-agentic-eng/Extensions/` and `PRPs-agentic-eng/Scripts/`

- **CEP Extension** (`Sib2Ae-Importer/`) - Professional dockable panel with HTML5 interface
- **ExtendScript** (`Sib2Ae_Importer.jsx`) - Rapid testing script, no installation required

**Import Process**: Select pipeline output folders → Choose import options (SVG/audio/JSON) → Creates organized After Effects composition

## Dependencies
- **Core**: svgelements, pydantic, click, pytest
- **Audio**: mido, librosa, soundfile, fluidsynth (`brew install fluidsynth`)
- **After Effects**: CEP 12, ExtendScript support