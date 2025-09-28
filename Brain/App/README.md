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
├── Symbolic Separators/        # SVG and MusicXML processing (5 scripts)
│   ├── truly_universal_noteheads_extractor.py
│   ├── truly_universal_noteheads_subtractor.py
│   ├── xml_based_instrument_separator.py
│   ├── individual_noteheads_creator.py
│   └── staff_barlines_extractor.py
├── Audio Separators/           # MIDI and audio processing (5 scripts)
│   ├── midi_note_separator.py
│   ├── midi_to_audio_renderer.py
│   ├── midi_to_audio_renderer_fast.py
│   ├── audio_to_keyframes.py
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

## 🎵 Audio Separators

### Purpose
Transform MIDI data into audio files and After Effects keyframe data, maintaining temporal synchronization with visual elements.

### Scripts

#### 1. `midi_note_separator.py` (Foundation)
**Purpose**: Split MIDI files into individual note files
```bash
python "Brain/App/Audio Separators/midi_note_separator.py" "Brain/Base/Saint-Saens Trio No 2.mid"
```
- **Input**: Complete MIDI file
- **Output**: Individual MIDI files per note in `outputs/midi/`
- **Naming**: `note_000_Flûte_A4_vel76.mid`
- **Foundation**: Required for all subsequent audio processing

#### 2. `midi_to_audio_renderer.py` (Standard Quality)
**Purpose**: Convert MIDI notes to high-quality audio files
```bash
python "Brain/App/Audio Separators/midi_to_audio_renderer.py" "outputs/midi"
```
- **Mode**: Sequential processing, 44kHz sample rate
- **Quality**: High-quality audio for final production
- **Output**: WAV files organized by instrument in `outputs/audio/`
- **Performance**: ~3-5 seconds per file

#### 3. `midi_to_audio_renderer_fast.py` (Fast Mode)
**Purpose**: Parallel audio rendering with optimized performance
```bash
python "Brain/App/Audio Separators/midi_to_audio_renderer_fast.py" "outputs/midi"
```
- **Mode**: Parallel processing, 22kHz sample rate, 6 workers
- **Quality**: Optimized for development and testing
- **Performance**: ~1 second total for 6 files
- **Use Case**: Development workflows, rapid iteration

#### 4. `audio_to_keyframes.py` (Comprehensive Analysis)
**Purpose**: Generate detailed After Effects keyframe data from audio
```bash
python "Brain/App/Audio Separators/audio_to_keyframes.py" "outputs/audio"
```
- **Analysis**: Full spectral analysis, comprehensive properties
- **Keyframes**: 72 keyframes per file (30 FPS, detailed)
- **Properties**: Amplitude, frequency, spectral centroid, RMS
- **Performance**: ~2-3 seconds per file

#### 5. `audio_to_keyframes_fast.py` (Essential Properties)
**Purpose**: Generate essential keyframe data with reduced processing time
```bash
python "Brain/App/Audio Separators/audio_to_keyframes_fast.py" "outputs/audio"
```
- **Analysis**: Essential properties only, reduced density
- **Keyframes**: Optimized keyframe count, essential animation data
- **Performance**: ~0.5-1 second per file
- **Use Case**: Development workflows, basic animation needs

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
- **Keyframe Rate**: 30 FPS for After Effects compatibility
- **Format**: WAV files, JSON keyframe data

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
- **MIDI Separation**: ~0.1s (foundation for audio processing)
- **Audio Rendering**: 0.7-1s (fast mode), 3-5s (standard mode)
- **Keyframe Generation**: 1-2s (fast mode), 2-3s (standard mode)

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

### Universal ID System
- Maintains relationships across all output formats
- Enables frame-accurate synchronization
- Supports complex musical timing relationships

### Orchestrator Coordination
- Sequential execution for reliability
- Parallel execution for performance
- Error handling and retry mechanisms
- Progress tracking and logging

## 📄 License

Part of the Sib2Ae project - Music notation to After Effects synchronization pipeline.

## 🎯 Version

**Status**: Production Ready
**Last Updated**: September 2025
**Pipeline Compatibility**: Universal ID Pipeline Orchestrator 1.0.0

---

🎼 **Ready to transform your musical notation into synchronized After Effects animations!**