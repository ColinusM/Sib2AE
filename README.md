# Sibelius to After Effects (Sib2Ae) Universal Converter

**Complete MusicXML to After Effects Pipeline** - Transform musical notation into pixel-perfect animations with synchronized audio.

## 🎼 What This Project Does

This project implements a **dual-pipeline system** for converting Sibelius exports into After Effects-ready assets:

### SVG Processing Pipeline
1. **📝 Noteheads Extractor** - Extracts all noteheads from MusicXML into clean SVG
2. **✂️ Noteheads Subtractor** - Removes noteheads from full score SVG  
3. **🎯 Instrument Separator** - Separates instruments into individual SVG files
4. **📐 Staff/Barlines Extractor** - Extracts structural framework (staff lines and barlines)

### Audio Processing Pipeline
1. **🎵 MIDI Note Separator** - Splits MIDI into individual note files
2. **🔊 Audio Renderer** - Converts MIDI notes to WAV audio files
3. **⚡ Keyframes Generator** - Creates After Effects keyframe data from audio analysis

**Key Innovation:** MusicXML-first approach with universal coordinate transformation for perfect accuracy across any musical score.

## 📋 Prerequisites

- **Python 3.12+**
- **uv package manager**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **FluidSynth** (for audio processing):
  - **macOS**: `brew install fluidsynth`
  - **Linux**: `sudo apt-get install fluidsynth`

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/Wirasm/PRPs-agentic-eng.git
cd PRPs-agentic-eng
uv sync

# Install audio dependencies
pip install mido librosa soundfile numpy

# Verify installation
python -c "import xml.etree.ElementTree, svgelements, mido, librosa; print('✅ All dependencies OK')"
```

## 🎼 SVG Processing Pipeline

```bash
# Extract noteheads from MusicXML
python Separators/truly_universal_noteheads_extractor.py "Base/SS 9.musicxml"

# Remove noteheads from full score
python Separators/truly_universal_noteheads_subtractor.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"

# Separate instruments into individual files
python Separators/xml_based_instrument_separator.py "Base/SS 9.musicxml" "Base/SS 9 full.svg" "output"

# Extract staff lines and barlines
python staff_barlines_extractor.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"

# Complete SVG pipeline (recommended)
python Separators/sib2ae_master_pipeline.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"
```

## 🔊 Audio Processing Pipeline

```bash
# Split MIDI into individual notes
python "Audio Separators/midi_note_separator.py" "Base/Saint-Saens Trio No 2.mid"

# Convert MIDI notes to audio (fast version)
python "Audio Separators/midi_to_audio_renderer_fast.py" "Base/Saint-Saens Trio No 2_individual_notes"

# Generate After Effects keyframes (fast version)
python "Audio Separators/audio_to_keyframes_fast.py" "Audio"
```

## ✅ Proven Results

**Test Case: Saint-Saëns Trio No. 2** 
- ✅ Extracted 9 noteheads (3 flute, 6 violin) with pixel-perfect coordinates
- ✅ Separated 2 instruments with proper XML structure maintained
- ✅ Extracted 10 staff lines + 13 barlines (11 regular + 2 thick end barlines)
- ✅ Universal coordinate system works across any MusicXML/SVG combination

## 🏗️ Architecture

### Universal Coordinate System
- **Staff 0** (Upper): Y 950-1100 (base: 1037)
- **Staff 1** (Lower): Y 1250-1500 (base: 1417) 
- **Staff 2** (Third): Y 1650-1800 (base: 1797)
- **Staff 3** (Fourth): Y 2050-2200 (base: 2177)

### Core Tools
- `truly_universal_noteheads_extractor.py` - MusicXML → Noteheads SVG
- `truly_universal_noteheads_subtractor.py` - Full SVG - Noteheads → Clean SVG
- `xml_based_instrument_separator.py` - Any SVG → Per-instrument SVGs
- `staff_barlines_extractor.py` - Full SVG → Staff lines + Barlines SVG

## 📁 Output Structure

After processing, you'll find organized outputs:

```
Symbolic Separators/           # SVG Processing Results
├── Flute/
│   ├── Flute_full.svg                    # Complete instrument score
│   ├── Flute_noteheads_only.svg          # Just the noteheads
│   ├── Flute_without_noteheads.svg       # Score minus noteheads
│   └── individual_noteheads/             # One file per notehead
│       ├── notehead_000_P1_A4_M4.svg
│       └── notehead_001_P1_A4_M5.svg
└── Violon/
    └── [Similar structure]

Audio/                         # Audio Processing Results
├── Flute/
│   ├── note_000_Flûte_A4_vel76.wav      # Individual note audio
│   └── note_001_Flûte_G4_vel76.wav
├── Violon/
│   └── [Similar audio files]
└── Keyframes/                            # After Effects JSON data
    ├── Flute/
    │   └── note_000_Flûte_A4_vel76_keyframes.json
    └── Violon/
        └── [Similar keyframe files]
```

## 🎯 Complete Workflow Example

```bash
# Process complete Saint-Saëns Trio No. 2 (both pipelines)
python Separators/sib2ae_master_pipeline.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"
python "Audio Separators/midi_note_separator.py" "Base/Saint-Saens Trio No 2.mid"
python "Audio Separators/midi_to_audio_renderer_fast.py" "Base/Saint-Saens Trio No 2_individual_notes"
python "Audio Separators/audio_to_keyframes_fast.py" "Audio"
```

**Result**: Complete After Effects project with separated visual elements and synchronized audio keyframes.

## 🔧 Troubleshooting

**FluidSynth not found**:
```bash
# macOS
brew install fluidsynth
which fluidsynth  # Should show path
```

**Audio dependencies missing**:
```bash
pip install mido librosa soundfile numpy
python -c "import mido, librosa; print('Audio OK')"
```

**SVG files not rendering**: Check that XML namespaces are preserved in output files.

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Essential 10-minute setup guide
- **[ONBOARDING.md](ONBOARDING.md)** - Comprehensive developer onboarding
- **[CLAUDE.md](CLAUDE.md)** - Development guidelines and commands
- **[PRPs/README.md](PRPs/README.md)** - PRP methodology documentation

## 🚀 Development & Contribution

This project uses the **Product Requirement Prompt (PRP)** methodology for AI-assisted development. 

**For Contributors**:
1. See **[ONBOARDING.md](ONBOARDING.md)** for complete setup and contribution guide
2. Use PRP templates in `PRPs/templates/` for feature development
3. Follow development workflow in `CLAUDE.md`

**For PRP Methodology**:
- See `PRPs/README.md` for complete PRP documentation
- Use `/create-base-prp` and `/execute-base-prp` Claude Code commands
- Access PRP templates and AI documentation in `PRPs/` directory

## ☕ Support This Work

**Found value in these resources?**

👉 **Buy me a coffee:** https://coff.ee/wirasm

### 🎯 Transform Your Team with AI Engineering Workshops

👉 **Book a workshop:** https://www.rasmuswiding.com/

- Learn the PRP methodology used by top engineering teams
- Hands-on training with Claude Code and real codebases
- From beginner to advanced AI engineering workshops

Contact: rasmus@widinglabs.com
