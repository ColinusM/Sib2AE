# Sib2Ae Developer Onboarding Guide

Welcome to the **Sibelius to After Effects (Sib2Ae) Universal Converter** project! This comprehensive guide will get you up and running as a contributor to this innovative musical notation processing pipeline.

## 1. Project Overview

### Project Name & Purpose
**Sib2Ae (Sibelius to After Effects)** - A dual-pipeline system that converts musical notation from Sibelius exports into After Effects-compatible assets for music visualization and animation.

### Main Functionality
- **SVG Processing Pipeline**: Extracts, separates, and processes musical notation from MusicXML/SVG exports
- **Audio Processing Pipeline**: Converts MIDI files to synchronized audio and keyframe data for After Effects
- **Universal Coordinate System**: Pixel-perfect accuracy across any musical score format

### Tech Stack
- **Language**: Python 3.12+
- **Core Libraries**: 
  - `xml.etree.ElementTree` - XML/SVG processing
  - `svgelements` - SVG manipulation and coordinate transformation
  - `mido` - MIDI file processing
  - `librosa` - Audio analysis and feature extraction
  - `numpy` - Numerical operations
- **External Dependencies**:
  - **FluidSynth** - MIDI to audio synthesis
  - **System soundfonts** - Audio rendering
- **Development Tools**:
  - `uv` - Package management and virtual environments
  - `pytest` - Testing framework
  - **PRP (Product Requirement Prompt)** methodology for AI-assisted development

### Architecture Pattern
**Dual-Pipeline Processing Architecture**:
- **SVG Pipeline**: MusicXML-first coordinate extraction → SVG manipulation → Asset separation
- **Audio Pipeline**: MIDI analysis → Audio synthesis → Feature extraction → Keyframe generation
- **Master Orchestrator**: Automated pipeline execution with organized output structure

### Key Dependencies & Purposes
```toml
[project.dependencies]
svgelements = ">=1.9.0"     # SVG processing and coordinate transformation
cairosvg = ">=2.7.0"        # SVG rendering capabilities
pydantic = ">=2.0.0"        # Data validation for structured processing
click = ">=8.0.0"           # Command-line interface framework
pytest = ">=7.0.0"          # Testing framework
pillow = ">=10.0.0"         # Image processing utilities
```

**External Audio Dependencies** (install separately):
- `mido` - MIDI file manipulation
- `librosa` - Audio analysis and spectral features
- `soundfile` - Audio I/O operations
- `numpy` - Mathematical operations for signal processing

## 2. Repository Structure

### Top-Level Directory Organization

```
PRPs-agentic-eng/
├── Separators/                     # 🎼 SVG Processing Pipeline
│   ├── truly_universal_noteheads_extractor.py    # Extract noteheads from MusicXML
│   ├── truly_universal_noteheads_subtractor.py   # Remove noteheads from SVG
│   ├── xml_based_instrument_separator.py         # Separate instruments
│   ├── sib2ae_master_pipeline.py                 # Master orchestrator
│   └── individual_noteheads_creator.py           # Individual notehead files
├── Audio Separators/               # 🔊 Audio Processing Pipeline
│   ├── midi_note_separator.py                    # Split MIDI into notes
│   ├── midi_to_audio_renderer.py                 # Standard MIDI→Audio
│   ├── midi_to_audio_renderer_fast.py            # Optimized MIDI→Audio
│   ├── audio_to_keyframes.py                     # Standard keyframes
│   └── audio_to_keyframes_fast.py                # Optimized keyframes
├── staff_barlines_extractor.py    # 📐 Extract staff/barlines framework
├── Base/                          # 📁 Input Files & Test Data
│   ├── SS 9.musicxml                             # MusicXML score data
│   ├── SS 9 full.svg                             # Complete SVG export
│   └── Saint-Saens Trio No 2.mid                 # MIDI source file
├── Audio/                         # 🎵 Audio Output Directory
│   ├── [Instrument]/                             # Audio files by instrument
│   └── Keyframes/                                # After Effects JSON files
├── Symbolic Separators/           # 🎯 Processed SVG Output
│   └── [Instrument]/                             # Separated instrument files
├── PRPs/                          # 🚀 Development Methodology
│   ├── templates/                                # PRP development templates
│   ├── scripts/                                  # PRP execution scripts
│   └── ai_docs/                                  # AI engineering documentation
├── Implementation Summaries/       # 📋 Feature Documentation
├── claude_md_files/               # ⚙️  Framework Templates
├── CLAUDE.md                      # 🔧 Project Guidelines
├── pyproject.toml                 # 📦 Dependencies & Config
└── README.md                      # 📖 Project Documentation
```

### Code Organization Patterns

**SVG Processing (`Separators/`)**:
- **Extractors**: Tools that pull specific elements from source files
- **Subtractors**: Tools that remove elements while preserving structure
- **Separators**: Tools that split content into organized outputs
- **Creators**: Tools that generate individual asset files

**Audio Processing (`Audio Separators/`)**:
- **Separators**: MIDI note extraction and organization
- **Renderers**: MIDI to audio conversion (standard + optimized)
- **Analyzers**: Audio feature extraction for keyframes

**Unique Organizational Patterns**:
- **Dual Pipeline Structure**: Parallel SVG and Audio processing paths
- **Fast/Standard Variants**: Performance-optimized versions with 8x speed improvements
- **Universal Coordinate System**: Consistent pixel positioning across all tools
- **MusicXML-First Approach**: Always analyze XML structure before SVG processing

## 3. Getting Started

### Prerequisites

**Required Software & Versions**:
- **Python 3.12+** (verified with `python --version`)
- **uv package manager** - Install via: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **FluidSynth** (for audio processing):
  - **macOS**: `brew install fluidsynth`
  - **Linux**: `sudo apt-get install fluidsynth`
  - **Windows**: Download from FluidSynth website

**System Requirements**:
- System soundfonts (automatically detected)
- Minimum 4GB RAM for large scores
- 1GB free disk space for audio processing

### Environment Setup Commands

```bash
# 1. Clone the repository
git clone https://github.com/Wirasm/PRPs-agentic-eng.git
cd PRPs-agentic-eng

# 2. Set up Python environment
uv sync

# 3. Verify core dependencies
python -c "import xml.etree.ElementTree, svgelements; print('SVG dependencies OK')"

# 4. Install audio processing dependencies (separate step)
pip install mido librosa soundfile numpy

# 5. Verify audio dependencies
python -c "import mido, librosa; print('Audio dependencies OK')"

# 6. Test FluidSynth installation
which fluidsynth  # Should show path to FluidSynth binary
```

### Configuration Files

**No configuration files need to be created** - the project uses convention-based configuration:
- Input files go in `Base/` directory
- Output automatically organized by instrument and processing type
- Coordinate mappings are empirically determined and embedded in code

### Running the Project Locally

#### SVG Processing Pipeline
```bash
# Extract noteheads from MusicXML
python Separators/truly_universal_noteheads_extractor.py "Base/SS 9.musicxml"

# Remove noteheads from full score
python Separators/truly_universal_noteheads_subtractor.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"

# Separate instruments
python Separators/xml_based_instrument_separator.py "Base/SS 9.musicxml" "Base/SS 9 full.svg" "output_dir"

# Complete pipeline (recommended)
python Separators/sib2ae_master_pipeline.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"
```

#### Audio Processing Pipeline
```bash
# Split MIDI into individual notes
python "Audio Separators/midi_note_separator.py" "Base/Saint-Saens Trio No 2.mid"

# Convert to audio (fast version recommended)
python "Audio Separators/midi_to_audio_renderer_fast.py" "Base/Saint-Saens Trio No 2_individual_notes"

# Generate keyframes (fast version recommended)
python "Audio Separators/audio_to_keyframes_fast.py" "Audio"
```

### Running Tests

```bash
# Run test suite (if implemented)
uv run pytest

# Manual validation steps
# 1. Open generated SVG files in browser
# 2. Check Audio/ directory for WAV files
# 3. Import JSON keyframes into After Effects
```

### Building for Production

**No build step required** - Python scripts run directly. For deployment:

1. **Package with dependencies**: `uv export --format requirements-txt`
2. **Docker deployment**: Copy scripts + install FluidSynth in container
3. **CI/CD**: Use PRP runner in headless mode for automated processing

## 4. Key Components

### Entry Points

**SVG Pipeline Entry Points**:
- `Separators/sib2ae_master_pipeline.py` - **Main entry point** for complete SVG processing
- `Separators/truly_universal_noteheads_extractor.py` - Standalone notehead extraction
- `staff_barlines_extractor.py` - Standalone staff/barlines extraction

**Audio Pipeline Entry Points**:
- `Audio Separators/midi_note_separator.py` - **Start here** for audio processing
- `Audio Separators/midi_to_audio_renderer_fast.py` - Optimized audio generation
- `Audio Separators/audio_to_keyframes_fast.py` - Optimized keyframe generation

### Core Business Logic Locations

**Universal Coordinate System** (`Separators/truly_universal_noteheads_extractor.py:12-20`):
```python
# Extract scaling information for universal coordinate conversion
scaling = root.find('defaults/scaling')
if scaling is not None:
    tenths = float(scaling.find('tenths').text)
    mm = float(scaling.find('millimeters').text)
    scaling_factor = mm / tenths
else:
    scaling_factor = 0.15  # Default scaling
```

**Staff Position Mappings** (hardcoded empirical values):
- Staff 0 (Upper): Y 950-1100 (base: 1037)
- Staff 1 (Lower): Y 1250-1500 (base: 1417)
- Staff 2 (Third): Y 1650-1800 (base: 1797)
- Staff 3 (Fourth): Y 2050-2200 (base: 2177)

**Notehead Recognition** (`Separators/truly_universal_noteheads_extractor.py:70-85`):
- Helsinki Special Std font mapping
- Code 70: `\u0046` (hollow noteheads)
- Code 102: `\u0066` (filled noteheads)

### Database Models/Schemas

**No traditional database** - Data structures are:
- **MusicXML**: Hierarchical XML with `<part>` → `<measure>` → `<note>` structure
- **SVG**: XML with `<g>` groups containing coordinate-positioned elements
- **MIDI**: Binary format processed through `mido` library
- **JSON Keyframes**: After Effects compatible `[frame_number, value]` arrays

### API Endpoints/Routes

**No web API** - Command-line interface only. Key "endpoints" are:

**SVG Processing Functions**:
- `extract_xml_notes()` - MusicXML → note coordinates
- `generate_svg_content()` - Coordinates → SVG elements
- `separate_instruments()` - Full SVG → per-instrument SVGs

**Audio Processing Functions**:
- `analyze_midi_structure()` - MIDI → note events
- `render_midi_to_audio()` - MIDI → WAV files
- `analyze_audio_features()` - WAV → keyframe data

### Configuration Management

**Convention-based configuration**:
- File paths: All relative to project root
- Output directories: Auto-created based on input filenames
- Coordinate mappings: Empirically determined constants
- Audio settings: Embedded in processing scripts (22kHz sample rate, 30 FPS keyframes)

### Authentication/Authorization

**Not applicable** - Local file processing tool with no network access or user management.

## 5. Development Workflow

### Git Branch Naming Conventions

Based on PRP methodology:
- `feature/[prp-name]` - New feature development
- `fix/[issue-description]` - Bug fixes
- `refactor/[component-name]` - Code improvements
- `docs/[update-type]` - Documentation updates

### Creating a New Feature

1. **Use PRP methodology**:
   ```bash
   # Create a PRP (Product Requirement Prompt)
   cp PRPs/templates/prp_base.md PRPs/my-feature.md
   
   # Or use Claude Code command
   /create-base-prp implement [feature description]
   ```

2. **Execute PRP**:
   ```bash
   # Interactive development
   uv run PRPs/scripts/prp_runner.py --prp my-feature --interactive
   
   # Or use Claude Code
   /execute-base-prp PRPs/my-feature.md
   ```

3. **Manual implementation**:
   ```bash
   # Create feature branch
   git checkout -b feature/my-feature
   
   # Implement following existing patterns
   # Test with sample files in Base/
   # Validate output structure
   ```

### Testing Requirements

**Manual Testing Process**:
1. **SVG Validation**: Open generated SVG files in browser - should render correctly
2. **Audio Validation**: Check generated WAV files play correctly
3. **Coordinate Accuracy**: Verify pixel-perfect positioning in After Effects
4. **Structure Preservation**: Ensure XML namespaces and hierarchy maintained

**Automated Testing** (when implemented):
```bash
uv run pytest tests/test_svg_parser.py -v
```

### Code Style/Linting Rules

**Follow existing patterns**:
- Use `xml.etree.ElementTree` for all XML processing (never regex or string manipulation)
- Preserve XML namespaces (ns0:svg, ns0:g) in output
- Include descriptive print statements for debugging
- Handle errors gracefully with informative messages
- Use type hints for function parameters

### PR Process and Review Guidelines

1. **Before creating PR**:
   ```bash
   # Test with provided sample files
   python Separators/sib2ae_master_pipeline.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"
   
   # Verify audio pipeline
   python "Audio Separators/midi_note_separator.py" "Base/Saint-Saens Trio No 2.mid"
   ```

2. **PR requirements**:
   - Test results with sample data
   - Generated output files (SVG, audio, JSON)
   - Description of coordinate accuracy improvements
   - Performance impact (if applicable)

### CI/CD Pipeline Overview

**Current**: Manual testing with sample files
**Future**: Automated pipeline using PRP runner in headless mode:
```yaml
# GitHub Actions example
- name: Execute PRP
  run: |
    uv run PRPs/scripts/prp_runner.py \
      --prp implement-feature \
      --output-format json > result.json
```

## 6. Architecture Decisions

### Design Patterns Used

**Universal Coordinate System Pattern**:
- **Why**: Sibelius exports vary in coordinate systems across different scores
- **How**: Extract scaling from MusicXML, apply universal transformation
- **Result**: Pixel-perfect accuracy across any input file

**MusicXML-First Processing Pattern**:
- **Why**: SVG alone lacks structural information about musical elements
- **How**: Always parse MusicXML first to understand note locations and types
- **Result**: Accurate extraction even with complex notation

**Dual Pipeline Architecture**:
- **Why**: SVG and audio processing serve different use cases but need coordination
- **How**: Separate pipelines with shared coordinate system and naming conventions
- **Result**: Clean separation of concerns with synchronized output

### State Management Approach

**Stateless Processing**: Each tool is stateless and can be run independently
- Input: File paths
- Processing: Pure functions with no persistent state
- Output: Generated files with consistent naming

**Coordinate State**: Universal coordinate mappings shared across all tools
- Staff positions empirically determined
- Scaling factors extracted from MusicXML
- Consistent pixel positioning maintained throughout pipeline

### Error Handling Strategy

**Graceful Degradation**:
```python
# Example from noteheads extractor
try:
    scaling_factor = mm / tenths
except:
    scaling_factor = 0.15  # Fallback to default
```

**Informative Error Messages**:
- XML structure validation before processing
- File existence checks with helpful suggestions
- Coordinate boundary validation with debugging info

### Logging and Monitoring Setup

**Print-based Logging** with structured output:
```python
print(f"🎼 Processing: {input_file}")
print(f"✅ Extracted {len(notes)} noteheads")
print(f"📁 Output: {output_file}")
```

**Progress Indicators**: Emoji-based status reporting for pipeline stages

### Security Measures

**File System Security**:
- All file operations relative to project directory
- Input validation for XML structure
- No network access or external API calls

**Code Security**:
- No eval() or exec() usage
- XML parsing with standard library (not vulnerable parsers)
- No shell injection risks in subprocess calls

### Performance Optimizations

**Fast Variants** (8x speed improvement):
- `midi_to_audio_renderer_fast.py` - Parallel processing with ProcessPoolExecutor
- `audio_to_keyframes_fast.py` - Reduced sample rates and streamlined analysis
- Optimized FluidSynth parameters for faster synthesis

**Memory Efficiency**:
- Process files individually rather than loading all into memory
- Stream audio processing for large files
- Efficient SVG element manipulation

## 7. Common Tasks

### How to Add a New API Endpoint
**Not applicable** - Command-line tool only. To add new CLI functionality:

1. Create new Python script following naming pattern: `[action]_[target].py`
2. Follow existing argument parsing pattern:
   ```python
   if __name__ == "__main__":
       if len(sys.argv) != 3:
           print("Usage: python script.py input.xml output.svg")
           sys.exit(1)
       
       input_file = sys.argv[1]
       output_file = sys.argv[2]
   ```

### How to Create a New Database Model
**Not applicable** - File-based processing. To add new data structures:

1. Use Python dataclasses or TypedDict for structured data:
   ```python
   from typing import TypedDict
   
   class NoteData(TypedDict):
       x: float
       y: float
       pitch: str
       octave: int
       duration: str
   ```

### How to Add a New Test

1. Create test file in `tests/` directory:
   ```python
   # tests/test_new_feature.py
   import pytest
   from Separators.new_feature import process_function
   
   def test_process_function():
       result = process_function("Base/SS 9.musicxml")
       assert len(result) > 0
       assert result[0]['x'] > 0
   ```

2. Run with: `uv run pytest tests/test_new_feature.py -v`

### How to Debug Common Issues

**SVG Rendering Problems**:
```bash
# Check XML structure preservation
python -c "
import xml.etree.ElementTree as ET
tree = ET.parse('output.svg')
print(tree.getroot().tag)  # Should be {http://www.w3.org/2000/svg}svg
"
```

**Coordinate Accuracy Issues**:
```bash
# Compare MusicXML vs SVG coordinates
python Separators/truly_universal_noteheads_extractor.py "Base/SS 9.musicxml" --debug
```

**Audio Processing Failures**:
```bash
# Test FluidSynth directly
fluidsynth -T wav -F output.wav /System/Library/Components/CoreAudio.component/Contents/Resources/gs_instruments.dls input.mid
```

### How to Update Dependencies

```bash
# Update Python dependencies
uv sync --upgrade

# Update audio processing dependencies
pip install --upgrade mido librosa soundfile

# Verify compatibility
python -c "import mido, librosa, svgelements; print('All dependencies OK')"
```

## 8. Potential Gotchas

### Non-obvious Configurations

**Universal Coordinate System**: Staff positions are hardcoded based on empirical measurements from Saint-Saëns Trio No. 2. May need adjustment for different score layouts.

**Helsinki Special Std Font**: Notehead recognition relies on specific Unicode mappings (Code 70/102). Different fonts will require new mappings.

**XML Namespace Handling**: SVG files must preserve namespaces (`ns0:svg`, `ns0:g`) or After Effects import will fail.

### Required Environment Variables

**None required** - all configuration is convention-based. However, audio processing depends on:
- FluidSynth installation in system PATH
- System soundfonts in expected locations

### External Service Dependencies

**FluidSynth + System Soundfonts**:
- **macOS**: `/System/Library/Components/CoreAudio.component/Contents/Resources/`
- **Linux**: `/usr/share/sounds/sf2/`
- **Windows**: Varies by installation

### Known Issues or Workarounds

**Large Score Performance**:
- Files with >1000 notes may take several minutes to process
- **Workaround**: Use fast variants (`*_fast.py`) for better performance

**Complex Notation Elements**:
- Grace notes, trills, and extended techniques not yet supported
- **Workaround**: Process only standard noteheads for now

**SVG Coordinate Precision**:
- Some Sibelius exports have floating-point precision issues
- **Workaround**: Round coordinates to 2 decimal places for stability

### Performance Bottlenecks

**Audio Rendering**: Standard MIDI-to-audio conversion is CPU intensive
- **Solution**: Use `midi_to_audio_renderer_fast.py` with parallel processing

**SVG Element Parsing**: Large SVG files with thousands of elements
- **Solution**: Filter by element type early in processing pipeline

### Areas of Technical Debt

**Hardcoded Staff Positions**: Should be automatically detected from MusicXML layout
**Limited Font Support**: Only Helsinki Special Std currently supported
**No Error Recovery**: Pipeline stops on first error rather than continuing with warnings

## 9. Documentation and Resources

### Existing Documentation

**Project Documentation**:
- `README.md` - Project overview and quick start guide
- `CLAUDE.md` - Comprehensive development guidelines and command reference

**Implementation Summaries** (`Implementation Summaries/`):
- `SIB2AE-COMPLETE-IMPLEMENTATION.md` - Complete pipeline documentation
- `INSTRUMENT-SEPARATOR-IMPLEMENTATION.md` - Instrument separation details
- `Audio Render Faster.md` - Performance optimization documentation

### API Documentation

**No formal API docs** - Use `--help` flag and docstrings:
```bash
python Separators/truly_universal_noteheads_extractor.py --help
```

### Database Schemas

**File Format Documentation**:
- **MusicXML**: W3C standard format - see musicxml.com
- **SVG**: W3C standard - see w3.org/Graphics/SVG
- **MIDI**: Standard MIDI format - processed via `mido` library

### Deployment Guides

**Local Development**: See section 3 (Getting Started)
**Production Deployment**: Copy scripts + install dependencies on target system

### Team Conventions

**PRP Methodology**: Use Product Requirement Prompts for feature development
**AI-Assisted Development**: Use Claude Code commands in `.claude/commands/`
**File Naming**: Follow `[action]_[target]_[variant].py` pattern

## 10. Next Steps - Onboarding Checklist

### ✅ Environment Setup
- [ ] Clone repository and navigate to project directory
- [ ] Install Python 3.12+ and verify installation
- [ ] Install `uv` package manager
- [ ] Run `uv sync` to set up Python environment
- [ ] Install FluidSynth for audio processing
- [ ] Install audio dependencies: `pip install mido librosa soundfile numpy`

### ✅ Verification Tests
- [ ] Test SVG dependencies: `python -c "import xml.etree.ElementTree, svgelements; print('SVG OK')"`
- [ ] Test audio dependencies: `python -c "import mido, librosa; print('Audio OK')"`
- [ ] Verify FluidSynth: `which fluidsynth`
- [ ] Check sample files exist in `Base/` directory

### ✅ First Successful Run
- [ ] Run SVG pipeline: `python Separators/sib2ae_master_pipeline.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"`
- [ ] Verify output in `Symbolic Separators/` directory
- [ ] Open generated SVG files in browser to confirm rendering
- [ ] Run audio pipeline: `python "Audio Separators/midi_note_separator.py" "Base/Saint-Saens Trio No 2.mid"`
- [ ] Check generated audio files in `Audio/` directory

### ✅ Make a Test Change
- [ ] Modify print statement in `Separators/truly_universal_noteheads_extractor.py` line 7
- [ ] Re-run extraction to see change in output
- [ ] Understand how MusicXML coordinates map to SVG positions

### ✅ Run Test Suite
- [ ] Execute `uv run pytest` (if tests exist)
- [ ] Manual validation: open all generated SVG files
- [ ] Play generated audio files to verify quality

### ✅ Understand Main User Flow
- [ ] **Input**: MusicXML + SVG files from Sibelius export
- [ ] **SVG Processing**: Extract → Separate → Organize musical elements
- [ ] **Audio Processing**: MIDI → Individual notes → Audio → Keyframes
- [ ] **Output**: After Effects-ready assets (SVG + Audio + JSON keyframes)

### ✅ Identify Contribution Area
Choose your focus area:
- [ ] **SVG Processing**: Improve coordinate accuracy, add new notation support
- [ ] **Audio Processing**: Enhance feature extraction, optimize performance
- [ ] **Pipeline Integration**: Better error handling, automated workflows
- [ ] **Documentation**: Improve guides, add API documentation
- [ ] **Testing**: Add automated tests, validation scripts

### 🚀 Ready to Contribute!

You're now ready to contribute to Sib2Ae! Consider starting with:

1. **Small Enhancement**: Add a new print statement or improve error messages
2. **Bug Fix**: Investigate any coordinate accuracy issues with your own scores
3. **Performance**: Profile and optimize one of the slower processing stages
4. **Documentation**: Add examples or improve this onboarding guide

**Next recommended reading**: `CLAUDE.md` for detailed development guidelines and command reference.

**Questions?** Check existing issues or create new ones for discussion. The PRP methodology in `PRPs/` provides structured templates for planning larger features.

Welcome to the team! 🎼🎬