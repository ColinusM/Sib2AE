# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Sibelius to After Effects (Sib2Ae) converter** that extracts and processes musical notation from SVG exports. The project implements a comprehensive pipeline from MusicXML/MIDI to After Effects-compatible assets.

### Dual Processing Pipelines

**1. SVG Processing Pipeline (Separators/):**
- **Noteheads Extractor** (`truly_universal_noteheads_extractor.py`) - Extracts noteheads from MusicXML
- **Noteheads Subtractor** (`truly_universal_noteheads_subtractor.py`) - Removes noteheads from full SVG 
- **Instrument Separator** (`xml_based_instrument_separator.py`) - Separates instruments into individual SVG files
- **Staff/Barlines Extractor** (`staff_barlines_extractor.py`) - Extracts structural framework (staff lines + barlines)

**2. Audio Processing Pipeline (Audio Separators/):**
- **MIDI Note Separator** (`midi_note_separator.py`) - Splits MIDI into individual note files
- **MIDI to Audio Renderer** (`midi_to_audio_renderer.py` / `midi_to_audio_renderer_fast.py`) - Converts MIDI to WAV audio
- **Audio to Keyframes** (`audio_to_keyframes.py` / `audio_to_keyframes_fast.py`) - Generates After Effects keyframe data

**Key Principles:**
- **MusicXML-First Approach**: Always analyze MusicXML before processing SVG
- **Universal Coordinate System**: Pixel-perfect accuracy across any musical score
- **Performance Optimization**: Fast versions available with parallel processing (8x speed improvement)
- **After Effects Integration**: JSON keyframe format compatible with AE expressions

## Development Commands

### Setup
```bash
# Install dependencies
uv sync
```

### SVG Processing Pipeline (Separators/)
```bash
# Extract noteheads only
python Separators/truly_universal_noteheads_extractor.py "Base/SS 9.musicxml"

# Remove noteheads from full score  
python Separators/truly_universal_noteheads_subtractor.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"

# Separate instruments
python Separators/xml_based_instrument_separator.py "Base/SS 9.musicxml" "Base/SS 9 full.svg" "output_dir"

# Extract staff lines and barlines
python staff_barlines_extractor.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"

# Full workflow: Extract → Separate
python Separators/truly_universal_noteheads_extractor.py "Base/SS 9.musicxml"
python Separators/xml_based_instrument_separator.py "Base/SS 9.musicxml" "Base/SS 9_noteheads_universal.svg" "noteheads_separated"
```

### Audio Processing Pipeline (Audio Separators/)
```bash
# Split MIDI into individual notes
python "Audio Separators/midi_note_separator.py" "Base/Saint-Saens Trio No 2.mid"

# Convert MIDI notes to audio (standard)
python "Audio Separators/midi_to_audio_renderer.py" "Base/Saint-Saens Trio No 2_individual_notes"

# Convert MIDI notes to audio (fast - 18% faster)
python "Audio Separators/midi_to_audio_renderer_fast.py" "Base/Saint-Saens Trio No 2_individual_notes"

# Generate After Effects keyframes (standard)
python "Audio Separators/audio_to_keyframes.py" "Audio"

# Generate After Effects keyframes (fast - 8x faster)
python "Audio Separators/audio_to_keyframes_fast.py" "Audio"

# Complete MIDI-to-AE workflow
python "Audio Separators/midi_note_separator.py" "Base/Saint-Saens Trio No 2.mid"
python "Audio Separators/midi_to_audio_renderer_fast.py" "Base/Saint-Saens Trio No 2_individual_notes"
python "Audio Separators/audio_to_keyframes_fast.py" "Audio"
```

### Performance Testing
```bash
# Time comparison between standard and fast versions
time python "Audio Separators/midi_to_audio_renderer.py" "Base/Saint-Saens Trio No 2_individual_notes"
time python "Audio Separators/midi_to_audio_renderer_fast.py" "Base/Saint-Saens Trio No 2_individual_notes"

time python "Audio Separators/audio_to_keyframes.py" "Audio"
time python "Audio Separators/audio_to_keyframes_fast.py" "Audio"
```

### Testing & Validation
```bash
# Run tests (if implemented)
uv run pytest

# Validate SVG output (manual)
# Open generated SVG files in browser to verify structure

# Validate audio output
# Check generated WAV files in Audio/ directory organized by instrument

# Validate keyframes
# Import JSON files from Audio/Keyframes/ into After Effects
```

## Universal Coordinate System

### Staff Position Mappings
- **Staff 0** (Upper): Y 950-1100 (base: 1037) 
- **Staff 1** (Lower): Y 1250-1500 (base: 1417)
- **Staff 2** (Third): Y 1650-1800 (base: 1797)
- **Staff 3** (Fourth): Y 2050-2200 (base: 2177)

### Helsinki Special Std Notehead Codes
- **Code 70**: `\u0046` (hollow notehead - half/whole notes)
- **Code 102**: `\u0066` (full notehead - quarter/eighth/sixteenth notes)

### Staff/Barlines Structure Recognition
- **Staff lines**: stroke-width="2.25", full-width horizontal lines (>3000 pixels)
- **Ledger lines**: stroke-width="3.75", short horizontal lines (<3000 pixels) - EXCLUDED
- **Regular barlines**: stroke-width="5", vertical lines connecting staves
- **Thick end barlines**: stroke-width="16", final double barline effect

## File Structure

```
/
├── Base/                                      # Input files
│   ├── SS 9.musicxml                         # MusicXML score data
│   ├── SS 9 full.svg                         # Complete SVG score
│   ├── SS 9_noteheads_universal.svg          # Extracted noteheads
│   └── Saint-Saens Trio No 2.mid             # MIDI source file
├── Separators/                               # SVG Processing Pipeline
│   ├── truly_universal_noteheads_extractor.py    # Extract noteheads from MusicXML
│   ├── truly_universal_noteheads_subtractor.py   # Remove noteheads from SVG
│   ├── xml_based_instrument_separator.py         # Separate instruments
│   ├── sib2ae_master_pipeline.py                 # Master pipeline orchestrator
│   └── individual_noteheads_creator.py           # Create individual notehead files
├── Audio Separators/                         # Audio Processing Pipeline
│   ├── midi_note_separator.py                    # Split MIDI into individual notes
│   ├── midi_to_audio_renderer.py                 # Convert MIDI to audio (standard)
│   ├── midi_to_audio_renderer_fast.py            # Convert MIDI to audio (optimized)
│   ├── audio_to_keyframes.py                     # Generate AE keyframes (standard)
│   └── audio_to_keyframes_fast.py                # Generate AE keyframes (optimized)
├── Audio/                                    # Audio output directory
│   ├── [Instrument]/                             # Audio files by instrument
│   └── Keyframes/                                # After Effects keyframe JSON files
├── staff_barlines_extractor.py              # Extract staff/barlines framework
├── PRPs/                                     # PRP methodology and templates
│   ├── templates/                                # PRP templates for feature development
│   ├── scripts/prp_runner.py                     # PRP execution script
│   └── ai_docs/                                  # AI engineering documentation
└── pyproject.toml                           # Python dependencies and project config
```

## Audio Processing Architecture

### MIDI-to-After Effects Pipeline Flow
1. **MIDI Analysis**: Extract note events with timing, pitch, velocity, and instrument data
2. **Note Separation**: Create individual MIDI files for each note with proper naming convention
3. **Audio Synthesis**: Convert MIDI notes to WAV audio using FluidSynth with system soundfonts
4. **Audio Analysis**: Extract amplitude, spectral features, onset detection, and tempo data
5. **Keyframe Generation**: Create After Effects-compatible JSON with 30 FPS timing and normalized values

### Performance Optimizations
- **Parallel Processing**: `ProcessPoolExecutor` for concurrent audio rendering and analysis
- **Reduced Sample Rates**: 22kHz vs 44kHz for faster processing without quality loss
- **Streamlined Analysis**: Essential features only (amplitude, brightness, roughness, MFCCs)
- **Optimized FluidSynth**: Simplified command parameters and audio driver settings

### After Effects Integration
- **Keyframe Format**: `[frame_number, value]` arrays for each property
- **Properties**: `scale`, `opacity`, `hue`, `position_x`, `onset_markers`
- **Timing**: 30 FPS with frame-accurate synchronization
- **Values**: Normalized 0-100 range for easy expression mapping

## Critical Implementation Details

### XML Processing Requirements
- Use `xml.etree.ElementTree` for proper XML/SVG structure preservation
- Never use text-based line processing for SVG manipulation
- Maintain XML namespaces (ns0:svg, ns0:g) in output files

### Coordinate Handling
- MusicXML coordinates are relative to measures
- SVG coordinates are absolute pixel positions
- Use empirically determined staff ranges for instrument separation
- Filter out small Y values (< 100) to avoid opacity conflicts

### Error Prevention
- Validate MusicXML structure before processing
- Check for `<part-list>` with `<score-part>` elements
- Ensure all tools maintain pixel-perfect coordinate accuracy
- Always verify output SVG files render correctly
- Verify FluidSynth installation and soundfont availability for audio processing
- Check audio file generation before running keyframe extraction

### Audio Processing Requirements
- **FluidSynth**: Required for MIDI-to-audio conversion with system soundfonts
- **librosa**: Required for audio analysis and feature extraction 
- **mido**: Required for MIDI file manipulation and note extraction
- **Parallel Processing**: Use `ProcessPoolExecutor` for optimal performance
- **File Organization**: Maintain instrument-based folder structure in Audio/ directory

## Dependencies and Setup

### Core Dependencies (pyproject.toml)
```toml
dependencies = [
    "svgelements>=1.9.0",     # SVG processing and manipulation
    "cairosvg>=2.7.0",        # SVG rendering and conversion  
    "pydantic>=2.0.0",        # Data validation and serialization
    "click>=8.0.0",           # Command-line interface
    "pytest>=7.0.0",          # Testing framework
    "pillow>=10.0.0"          # Image processing
]
```

### Audio Processing Dependencies (install separately)
```bash
# Install audio processing dependencies
pip install mido librosa soundfile numpy

# macOS: Install FluidSynth via Homebrew
brew install fluidsynth

# Verify system soundfont (used automatically)
ls /System/Library/Components/CoreAudio.component/Contents/Resources/
```

## Documentation & Onboarding

This project provides comprehensive documentation for developers and users:

### New Developer Resources
- **ONBOARDING.md** - Complete developer onboarding guide with setup, architecture, and contribution workflow
- **QUICKSTART.md** - Essential 10-minute setup guide for immediate productivity
- **README.md** - Project overview with both SVG and audio pipelines

### Developer Guidelines
These files provide structured guidance for different aspects of working with this project:

1. **ONBOARDING.md** - Use this for:
   - Understanding the complete project architecture
   - Setting up development environment
   - Learning the dual-pipeline system (SVG + Audio)
   - Contributing to the project
   - Troubleshooting common issues

2. **QUICKSTART.md** - Use this for:
   - Getting running in under 10 minutes
   - Essential command examples
   - Basic verification steps
   - Common workflow patterns

3. **README.md** - Use this for:
   - Project overview and capabilities
   - Prerequisites and installation
   - Complete pipeline examples
   - Output structure understanding

## PRP Integration

This project uses the **Product Requirement Prompt (PRP)** methodology. Use `/create-base-prp` and `/execute-base-prp` commands for feature development.

**PRP Directory:** `/PRPs/`
**Templates:** Use `prp_base.md` for comprehensive feature development
**Runner:** `python PRPs/scripts/prp_runner.py --prp [feature-name] --interactive`