# Sib2Ae Quick Start Guide

Get the Sibelius to After Effects converter running in under 10 minutes.

## ⚡ Prerequisites (2 minutes)

```bash
# Install Python 3.12+ (check version)
python3 --version  # Must be 3.12+

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install FluidSynth for audio processing
# macOS:
brew install fluidsynth

# Linux:
sudo apt-get install fluidsynth

# Verify FluidSynth
which fluidsynth  # Should show path
```

## 🚀 Setup (3 minutes)

```bash
# 1. Clone and enter project
git clone [repository-url]
cd Sib2Ae

# 2. Install dependencies
uv sync
pip install mido librosa soundfile numpy

# 3. Verify installation
python -c "import xml.etree.ElementTree, svgelements, mido, librosa; print('✅ All dependencies OK')"
```

## 🎵 First Run (3 minutes)

### Option 1: GUI (Recommended)
```bash
# Launch graphical interface
python3 sib2ae_gui.py

# OR use launcher script
./launch_gui.sh
```

**GUI Features:**
- **Symbolic Pipeline Tab**: Process MusicXML → SVG
- **Audio Pipeline Tab**: Process MIDI → Audio files
- **Master Pipeline Tab**: Complete workflow
- **Output Log Tab**: Real-time progress monitoring

### Option 2: Command Line
```bash
# Complete symbolic pipeline (SVG processing)
python "PRPs-agentic-eng/App/Symbolic Separators/sib2ae_master_pipeline.py" "SS 9" "symbolic_output"

# Complete audio pipeline
python "PRPs-agentic-eng/App/Audio Separators/midi_note_separator.py" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2.mid"
python "PRPs-agentic-eng/App/Audio Separators/midi_to_audio_renderer_fast.py" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2_individual_notes"
```

## ✅ Verify Success (2 minutes)

Check these output directories:

```bash
# Symbolic processing outputs
ls PRPs-agentic-eng/instruments_output/  # Should show Flûte_P1.svg, Violon_P2.svg

# Audio processing outputs
ls PRPs-agentic-eng/Audio/Flûte/         # Should show .wav files
ls PRPs-agentic-eng/Audio/Keyframes/     # Should show JSON keyframe files

# Synchronization data
ls PRPs-agentic-eng/universal_output/    # Should show coordination JSON files
```

**Expected Results:**
- ✅ 2 instrument SVG files (Flûte, Violon)
- ✅ 6 audio files (2 flute + 4 violin notes)
- ✅ 6 keyframe JSON files for After Effects
- ✅ Universal coordination metadata

## 🎬 Import to After Effects (Optional)

### Method 1: ExtendScript (Quick Test)
1. Open After Effects
2. **File → Scripts → Run Script File**
3. Select `PRPs-agentic-eng/Scripts/Sib2Ae_Importer.jsx`
4. Choose your output folder and import

### Method 2: CEP Extension (Professional)
1. Copy `PRPs-agentic-eng/Extensions/Sib2Ae-Importer/` to AE extensions folder
2. Enable debug mode: `defaults write com.adobe.CSXS.12 PlayerDebugMode 1`
3. Restart After Effects
4. **Window → Extensions → Sib2Ae Importer**

## 🆘 Common Issues

### FluidSynth Not Found
```bash
# macOS fix
brew install fluidsynth
export PATH="/opt/homebrew/bin:$PATH"

# Test
which fluidsynth  # Should show path
```

### Audio Dependencies Missing
```bash
pip install mido librosa soundfile numpy
python -c "import mido, librosa; print('Audio libraries OK')"
```

### Wrong Working Directory
```bash
# Always run from project root
cd /path/to/Sib2Ae  # NOT inside PRPs-agentic-eng/
python3 sib2ae_gui.py  # ✅ Correct
```

## 📚 Next Steps

- **Full Documentation**: Read `ONBOARDING.md` for comprehensive developer guide
- **Development Guidelines**: Check `CLAUDE.md` for commands and workflows
- **Sample Data**: Explore `PRPs-agentic-eng/Base/` for test files
- **GUI Features**: Use the GUI tabs to explore different pipeline stages

**You're ready to start converting music notation to After Effects animations!** 🎼→🎬