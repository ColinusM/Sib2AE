# Sib2Ae Quick Start Guide

Get up and running with the Sibelius to After Effects converter in under 10 minutes.

## ⚡ Prerequisites

- **Python 3.12+**
- **uv package manager**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **FluidSynth** (for audio): `brew install fluidsynth` (macOS)

## 🚀 Setup (2 minutes)

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

### Extract Noteheads
```bash
python Separators/truly_universal_noteheads_extractor.py "Base/SS 9.musicxml"
```
**Output**: `Base/SS 9_noteheads_universal.svg`

### Remove Noteheads from Score
```bash
python Separators/truly_universal_noteheads_subtractor.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"
```
**Output**: `Base/SS 9_without_noteheads.svg`

### Separate Instruments
```bash
python Separators/xml_based_instrument_separator.py "Base/SS 9.musicxml" "Base/SS 9 full.svg" "output"
```
**Output**: `Symbolic Separators/[Instrument]/` directories

### Complete SVG Pipeline (Recommended)
```bash
python Separators/sib2ae_master_pipeline.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"
```
**Output**: Complete organized output structure

## 🔊 Audio Processing Pipeline

### Split MIDI into Individual Notes
```bash
python "Audio Separators/midi_note_separator.py" "Base/Saint-Saens Trio No 2.mid"
```
**Output**: `Base/Saint-Saens Trio No 2_individual_notes/`

### Convert to Audio (Fast)
```bash
python "Audio Separators/midi_to_audio_renderer_fast.py" "Base/Saint-Saens Trio No 2_individual_notes"
```
**Output**: `Audio/[Instrument]/` WAV files

### Generate After Effects Keyframes (Fast)
```bash
python "Audio Separators/audio_to_keyframes_fast.py" "Audio"
```
**Output**: `Audio/Keyframes/[Instrument]/` JSON files

## ✅ Verification

### Check SVG Output
```bash
# Open in browser to verify rendering
open "Symbolic Separators/Flute/Flute_noteheads_only.svg"
```

### Check Audio Output
```bash
# List generated audio files
ls -la "Audio/Flute/"
ls -la "Audio/Keyframes/Flute/"
```

### Test in After Effects
1. Import SVG files as composition layers
2. Import JSON keyframes using expressions
3. Verify synchronized animation

## 🎯 Common Workflows

### Process Your Own Files
1. Export from Sibelius: **File → Export → MusicXML** and **File → Export → SVG**
2. Place files in `Base/` directory
3. Run pipelines with your filenames:
   ```bash
   python Separators/sib2ae_master_pipeline.py "Base/YourScore.musicxml" "Base/YourScore.svg"
   ```

### Performance Processing
Use fast variants for large scores:
```bash
python "Audio Separators/midi_to_audio_renderer_fast.py" "path/to/notes"  # 18% faster
python "Audio Separators/audio_to_keyframes_fast.py" "Audio"              # 8x faster
```

## 🔧 Troubleshooting

### FluidSynth Not Found
```bash
# macOS
brew install fluidsynth

# Verify
which fluidsynth
```

### Audio Dependencies Missing
```bash
pip install mido librosa soundfile numpy
python -c "import mido, librosa; print('Audio deps OK')"
```

### SVG Not Rendering
- Check that XML namespaces are preserved in output
- Verify coordinates are within expected ranges (Y: 950-2200)

## 📖 Next Steps

- **Full Documentation**: See `ONBOARDING.md` for comprehensive guide
- **Development**: Use PRP methodology in `PRPs/` for new features
- **Customization**: Modify coordinate mappings in extractor scripts

## ⚡ One-Command Complete Processing

```bash
# Process both SVG and audio in sequence
python Separators/sib2ae_master_pipeline.py "Base/SS 9.musicxml" "Base/SS 9 full.svg" && \
python "Audio Separators/midi_note_separator.py" "Base/Saint-Saens Trio No 2.mid" && \
python "Audio Separators/midi_to_audio_renderer_fast.py" "Base/Saint-Saens Trio No 2_individual_notes" && \
python "Audio Separators/audio_to_keyframes_fast.py" "Audio"
```

**Result**: Complete After Effects-ready asset package with pixel-perfect musical notation and synchronized audio keyframes.

---

🎼 **You're ready to convert musical notation to After Effects assets!** 🎬