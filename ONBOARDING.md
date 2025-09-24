# Sib2Ae Developer Onboarding Guide

Welcome to **Sib2Ae** (Sibelius to After Effects), a comprehensive music notation to animation synchronization pipeline. This guide will get you up to speed with the codebase, architecture, and development workflow.

## 🎼 1. Project Overview

### Purpose
Sib2Ae converts musical notation from Sibelius exports into pixel-perfect After Effects animations with synchronized audio. It bridges the gap between musical composition and visual animation.

### Main Functionality
- **Dual-Pipeline Processing**: Separate pipelines for visual (SVG) and audio (MIDI) processing
- **Universal Coordinate System**: Pixel-perfect transformation from MusicXML to SVG coordinates
- **Note Synchronization**: Links visual noteheads to audio waveforms via Universal IDs
- **After Effects Integration**: Direct import tools for seamless workflow

### Tech Stack
- **Languages**: Python 3.12+, JavaScript (ExtendScript), HTML/CSS (CEP Extensions)
- **Core Libraries**:
  - SVG Processing: `svgelements`, `xml.etree.ElementTree`
  - Audio Processing: `mido`, `librosa`, `soundfile`, `fluidsynth`
  - GUI: `tkinter`, `webview` (pywebview)
  - Data: `pydantic`, `json`, `pathlib`
- **External Dependencies**: FluidSynth (audio synthesis)
- **Target Platform**: After Effects (via ExtendScript and CEP extensions)

### Architecture Pattern
**Pipeline Architecture** with three main components:
1. **Symbolic Separators**: MusicXML/SVG processing pipeline
2. **Audio Separators**: MIDI/audio processing pipeline
3. **Synchronizers**: Coordination between visual and audio elements

## 📁 2. Repository Structure

```
/
├── sib2ae_gui.py              # Main GUI application (31KB)
├── launch_gui.sh              # GUI launcher script
├── svg_viewer_webview.py      # Advanced SVG viewer (48KB)
├── CLAUDE.md                  # Development guidelines and commands
├── gui_settings.json          # GUI preferences (auto-saved)
│
├── PRPs-agentic-eng/          # Main pipeline directory
│   ├── pyproject.toml         # Package configuration
│   ├── note_coordinator.py    # Universal note coordination (current system)
│   │
│   ├── App/                   # Core pipeline scripts
│   │   ├── Symbolic Separators/     # SVG processing tools
│   │   │   ├── sib2ae_master_pipeline.py        # Master orchestrator
│   │   │   ├── truly_universal_noteheads_extractor.py
│   │   │   ├── truly_universal_noteheads_subtractor.py
│   │   │   ├── xml_based_instrument_separator.py
│   │   │   ├── individual_noteheads_creator.py
│   │   │   └── staff_barlines_extractor.py
│   │   │
│   │   ├── Audio Separators/        # Audio processing tools
│   │   │   ├── midi_note_separator.py
│   │   │   ├── midi_to_audio_renderer.py / _fast.py
│   │   │   └── audio_to_keyframes.py / _fast.py
│   │   │
│   │   └── Synchronizer 19-26-28-342/  # Advanced sync system (backup)
│   │       ├── context_gatherer.py
│   │       ├── synchronization_coordinator.py
│   │       └── utils/               # Advanced synchronization utilities
│   │           ├── midi_matcher.py
│   │           ├── tied_note_processor.py
│   │           ├── master_midi_extractor.py
│   │           └── xml_temporal_parser.py
│   │
│   ├── Base/                  # Input data files
│   │   ├── SS 9.musicxml      # Source MusicXML
│   │   ├── SS 9 full.svg      # Complete SVG score
│   │   └── Saint-Saens Trio No 2.mid  # Source MIDI
│   │
│   ├── Audio/                 # Generated audio outputs
│   │   ├── [Instrument]/      # Audio files by instrument
│   │   └── Keyframes/         # JSON keyframe data for AE
│   │
│   ├── Extensions/            # After Effects integration
│   │   └── Sib2Ae-Importer/   # CEP extension (professional tool)
│   │       ├── client/main.js
│   │       ├── jsx/main.jsx
│   │       └── CSXS/manifest.xml
│   │
│   ├── Scripts/               # After Effects scripts
│   │   └── Sib2Ae_Importer.jsx  # ExtendScript importer (rapid testing)
│   │
│   └── docs/                  # Documentation and debug knowledge
│       ├── music-debug-knowledge.md  # Auto-updated debug knowledge
│       └── claude-code-subagents-reference.md
│
└── bravura-master/            # Font resources (external dependency)
```

### Key Directory Purposes

- **`/`**: GUI application and project management
- **`PRPs-agentic-eng/App/`**: Core pipeline scripts organized by function
- **`PRPs-agentic-eng/Base/`**: Input files (MusicXML, SVG, MIDI)
- **`PRPs-agentic-eng/Audio/`**: Generated audio and keyframe outputs
- **`PRPs-agentic-eng/Extensions/`**: After Effects integration tools
- **`PRPs-agentic-eng/docs/`**: Documentation and debug knowledge base

## 🚀 3. Getting Started

### Prerequisites
- **Python 3.12+** - Core runtime
- **uv package manager** - Dependency management: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **FluidSynth** - Audio synthesis:
  - macOS: `brew install fluidsynth`
  - Linux: `sudo apt-get install fluidsynth`
  - Windows: Download from FluidSynth website

### Environment Setup

```bash
# 1. Clone repository
git clone [repository-url]
cd Sib2Ae

# 2. Setup Python environment
uv sync

# 3. Install additional audio dependencies
pip install mido librosa soundfile numpy

# 4. Verify installation
python -c "import xml.etree.ElementTree, svgelements, mido, librosa; print('✅ All dependencies OK')"

# 5. Test GUI
python3 sib2ae_gui.py
```

### Running the Project

#### Option 1: GUI (Recommended for Users)
```bash
# Launch GUI directly
python3 sib2ae_gui.py

# OR use launcher script
./launch_gui.sh
```

#### Option 2: Command Line (For Development)
```bash
# Working directory: Always run from project root
cd /path/to/Sib2Ae

# Run symbolic pipeline
python "PRPs-agentic-eng/App/Symbolic Separators/sib2ae_master_pipeline.py" "SS 9" "symbolic_output"

# Run audio pipeline
python "PRPs-agentic-eng/App/Audio Separators/midi_note_separator.py" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2.mid"
python "PRPs-agentic-eng/App/Audio Separators/midi_to_audio_renderer_fast.py" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2_individual_notes"
```

### Running Tests
```bash
cd PRPs-agentic-eng
python -m pytest  # Basic test runner
# Note: Limited test coverage currently - primarily integration testing via GUI
```

### Build Process
```bash
# No traditional build process - Python scripts run directly
# Package management via uv:
uv sync  # Install/update dependencies
```

## 🔧 4. Key Components

### Entry Points

#### Primary Entry Points
1. **`sib2ae_gui.py`** (31KB) - Main GUI application
   - Graphical interface for all pipeline operations
   - Real-time output monitoring
   - File browser integration
   - Always-on-top workflow efficiency

2. **`PRPs-agentic-eng/App/Symbolic Separators/sib2ae_master_pipeline.py`** - Symbolic processing orchestrator
   - Runs complete 4-tool SVG pipeline
   - Creates organized output structure
   - Error handling and progress reporting

3. **`PRPs-agentic-eng/note_coordinator.py`** - Universal synchronization system
   - Links MusicXML, MIDI, and SVG data
   - Creates Universal ID system
   - Simplified coordination approach

#### Secondary Entry Points
- Individual pipeline scripts for granular control
- After Effects scripts for direct import
- Debug and testing utilities

### Core Business Logic

#### Symbolic Processing (`PRPs-agentic-eng/App/Symbolic Separators/`)
- **`truly_universal_noteheads_extractor.py`** - Pixel-perfect XML→SVG coordinate transformation
- **`truly_universal_noteheads_subtractor.py`** - Remove noteheads while preserving musical structure
- **`xml_based_instrument_separator.py`** - Universal Y-coordinate staff mapping
- **`individual_noteheads_creator.py`** - One SVG per notehead for animation

#### Audio Processing (`PRPs-agentic-eng/App/Audio Separators/`)
- **`midi_note_separator.py`** - Individual note file creation from MIDI
- **`midi_to_audio_renderer_fast.py`** - Parallel audio synthesis (22kHz, 6 workers)
- **`audio_to_keyframes_fast.py`** - After Effects keyframe generation with optimized density

#### Synchronization Systems
1. **Current**: `note_coordinator.py` - Unified approach for most use cases
2. **Advanced**: `App/Synchronizer 19-26-28-342/` - Complex scenarios (tied notes, unquantized MIDI)

### Database/Data Models

#### Universal ID System
```python
@dataclass
class UniversalNote:
    universal_id: str          # UUID linking all formats
    xml_data: XMLNote         # MusicXML structure
    midi_data: MIDINote       # MIDI timing/velocity
    svg_coordinates: Tuple    # Visual positioning
    audio_filename: str       # Generated audio file
    keyframes_filename: str   # AE keyframe data
```

#### Coordinate System
- **Staff 0**: Y 950-1100 (base: 1037)
- **Staff 1**: Y 1250-1500 (base: 1417)
- **Staff 2**: Y 1650-1800 (base: 1797)
- **Staff 3**: Y 2050-2200 (base: 2177)

### API Endpoints/Routes
N/A - Desktop application with file-based processing

### Configuration Management
- **`gui_settings.json`** - GUI window position/preferences (auto-saved)
- **`PRPs-agentic-eng/pyproject.toml`** - Package dependencies and metadata
- **File paths**: All configured via CLAUDE.md for consistency

### Authentication/Authorization
N/A - Local desktop application

## 🛠️ 5. Development Workflow

### Git Workflow
- **Main Branch**: `main` (production-ready code)
- **Feature Branches**: Not currently used (single-developer project)
- **Commit Style**: Descriptive commits with clear functionality changes

Example recent commits:
```
931ddb9 Fix element matching logic to distinguish between notes properly
6a3e273 Add advanced SVG analysis window with interactive element inspection
2ad05e0 Replace Tkinter SVG viewer with pywebview for Chrome-quality rendering
```

### Creating a New Feature

#### 1. Feature Planning
- **Must use specialized agents** for Sib2Ae work:
  - `sib2ae-sync-orchestrator`: Default agent for implementation
  - `sib2ae-pipeline-debugger`: Auto-triggers on failures
- **Read debug knowledge**: Always check `docs/music-debug-knowledge.md` first

#### 2. Implementation Steps
```bash
# 1. Understand existing patterns
# Read CLAUDE.md for current workflows and file locations

# 2. Follow naming conventions
# All scripts use descriptive names with functionality clear
# Example: truly_universal_noteheads_extractor.py

# 3. Maintain pipeline structure
# Symbolic processing: App/Symbolic Separators/
# Audio processing: App/Audio Separators/
# Synchronization: App/Synchronizer 19-26-28-342/ or root note_coordinator.py

# 4. Test via GUI
python3 sib2ae_gui.py
# Use GUI tabs to test individual pipeline components
```

### Testing Strategy

#### Manual Testing (Primary)
- **GUI Testing**: Use `sib2ae_gui.py` for end-to-end workflow validation
- **Pipeline Testing**: Run individual scripts with sample data
- **Integration Testing**: Complete workflow from MusicXML → After Effects

#### Automated Testing (Limited)
- **Unit Tests**: `PRPs-agentic-eng/App/Synchronizer 19-26-28-342/utils/test_midi_matcher.py`
- **Integration Tests**: Not currently implemented
- **Test Data**: Saint-Saëns Trio No. 2 sample files in `Base/`

#### Test Commands
```bash
cd PRPs-agentic-eng
python -m pytest  # Run existing unit tests
python "App/Synchronizer 19-26-28-342/utils/test_midi_matcher.py"  # Specific component test
```

### Code Style/Linting
- **Style**: Follows Python PEP 8 conventions
- **Linting**: Uses `ruff` (cache in `.ruff_cache/`)
- **Type Checking**: Uses `mypy` (cache in `.mypy_cache/`)
- **Documentation**: Comprehensive docstrings for all major functions

### PR Process
- **Current**: Direct commits to main (single developer)
- **Future**: Standard GitHub PR workflow when team expands

### CI/CD Pipeline
- **Current**: Manual testing and deployment
- **Build Artifacts**: None (Python scripts run directly)
- **Deployment**: Users clone repository and run locally

## 🏗️ 6. Architecture Decisions

### Design Patterns

#### Pipeline Pattern
**Why**: Musical processing naturally follows sequential transformation steps
- Input → Processing → Output stages clearly defined
- Each component can be run independently for debugging
- Parallel processing where beneficial (fast audio rendering)

#### Universal ID Bridge Pattern
**Why**: Critical for maintaining relationships across different file formats (XML, MIDI, SVG, audio)
```python
# Instead of post-processing matching, establish relationships upfront
universal_id = "2584802d-2469-4e45-8cf0-ff934e1032d7"
# Links: notehead visual + MIDI timing + audio waveform + keyframe data
```

#### File-Based Coordination
**Why**: Enables debugging, partial processing, and clear data lineage
- Each processing step creates intermediate files
- Clear naming conventions maintain relationships
- `note_000_Flûte_A4_vel76.mid → .wav → _keyframes.json`

### State Management
- **File-based**: All state persisted to JSON files in organized directories
- **No database**: Simplifies deployment and debugging
- **Manifest files**: Track pipeline execution and relationships

### Error Handling Strategy
- **Graceful Degradation**: Continue processing other notes if one fails
- **Detailed Logging**: Console output with progress indicators and error details
- **Debug Knowledge Base**: Auto-updated failure documentation in `docs/music-debug-knowledge.md`

### Logging and Monitoring
- **Console Output**: Real-time progress with emoji indicators (🔄 ✅ ❌)
- **GUI Log Tab**: Comprehensive output capture in GUI interface
- **Debug Files**: JSON outputs for troubleshooting coordination issues

### Security Measures
- **Local Processing**: No network requests or external API calls
- **File Permissions**: Standard filesystem permissions
- **Input Validation**: XML/MIDI parsing with error handling

### Performance Optimizations

#### Parallel Processing
- **Fast Audio Rendering**: 6-worker parallel processing
- **Reduced Sample Rates**: 22kHz for fast processing vs 44kHz for quality
- **Keyframe Optimization**: 72 keyframes per file vs 1000+ for full analysis

#### Caching
- **No persistent cache**: Each run processes from source files
- **Intermediate Files**: Act as natural caching between pipeline stages

## 📋 7. Common Tasks

### Adding a New API Endpoint
N/A - Desktop application without API endpoints

### Creating a New Database Model
N/A - File-based data storage using Python dataclasses and JSON serialization

### Adding a New Test
```python
# Example: Add test to existing test file
# File: PRPs-agentic-eng/App/Synchronizer 19-26-28-342/utils/test_midi_matcher.py

def test_new_matching_algorithm():
    """Test description"""
    # Setup test data
    xml_notes = [...]  # Sample XMLNote objects
    midi_notes = [...] # Sample MIDINote objects

    # Run algorithm
    matches = midi_matcher.match_notes(xml_notes, midi_notes)

    # Assertions
    assert len(matches) == expected_count
    assert matches[0].confidence > 0.8
```

### Debugging Common Issues

#### SVG Coordinate Issues
```bash
# 1. Check coordinate transformation
python "App/Symbolic Separators/truly_universal_noteheads_extractor.py" "Base/SS 9.musicxml"

# 2. Verify output in SVG viewer
python3 sib2ae_gui.py  # Use SVG viewer tab
```

#### Audio Processing Failures
```bash
# 1. Test FluidSynth installation
which fluidsynth

# 2. Check MIDI file validity
python -c "import mido; print(mido.MidiFile('path/to/file.mid'))"

# 3. Use standard (non-fast) renderer for debugging
python "App/Audio Separators/midi_to_audio_renderer.py" "input_folder"
```

#### Synchronization Problems
```bash
# 1. Use simple coordination system first
python "note_coordinator.py" "Base/SS 9.musicxml" "Base/Saint-Saens Trio No 2.mid" "test_output"

# 2. Check debug knowledge base
cat "docs/music-debug-knowledge.md"

# 3. For complex cases, use advanced system
python "App/Synchronizer 19-26-28-342/context_gatherer.py" [args]
```

### Updating Dependencies
```bash
# Update all dependencies
uv sync --upgrade

# Add new dependency
uv add library-name

# Update pyproject.toml manually for version constraints
```

## ⚠️ 8. Potential Gotchas

### Non-obvious Configurations

#### Working Directory Requirements
- **Critical**: All commands must run from project root (`/Users/colinmignot/Claude Code/Sib2Ae/`)
- **Why**: Relative paths in scripts assume project root as working directory
- **Fix**: Always `cd` to project root before running any scripts

#### FluidSynth Path Issues
```bash
# Common issue: FluidSynth not in PATH
which fluidsynth  # Should show path like /opt/homebrew/bin/fluidsynth

# Fix on macOS if not found:
brew install fluidsynth
export PATH="/opt/homebrew/bin:$PATH"  # Add to shell profile
```

### Required Environment Variables
- **None required** - All paths configured in CLAUDE.md and scripts
- **Optional**: Set `PYTHONPATH` if importing modules fails

### External Service Dependencies

#### FluidSynth (Critical)
- **Required for**: All audio processing
- **Installation varies by platform**
- **Common failure**: Not in system PATH
- **Testing**: `fluidsynth --version` should work

#### Font Dependencies
- **Helsinki Special Std**: For MusicXML notehead recognition
- **Bravura**: Music font included in `bravura-master/` directory
- **Platform specific**: Font installation may vary

### Known Issues and Workarounds

#### GUI Always-On-Top on Some Platforms
```python
# In sib2ae_gui.py, line 45
self.root.attributes('-topmost', True)  # May cause focus issues
# Workaround: Toggle with button in GUI or modify code
```

#### Large SVG Files Performance
- **Issue**: 43KB+ SVG files slow processing
- **Workaround**: Use fast processing versions where available
- **Not affected**: Individual notehead files are much smaller

#### Audio Processing Timeouts
- **Fast version**: 10-second timeouts
- **Standard version**: 30-second timeouts
- **Workaround**: Use standard version for complex MIDI files

### Performance Bottlenecks

#### Sequential Processing
- **Symbolic pipeline**: Currently sequential
- **Impact**: Processing time scales with number of notes/instruments
- **Mitigation**: Master pipeline optimizes order of operations

#### Memory Usage with Large Files
- **SVG processing**: Loads entire file into memory
- **Audio analysis**: librosa loads full audio files
- **Mitigation**: Process in batches for very large scores

### Areas of Technical Debt

#### Limited Test Coverage
- **Current**: One unit test file, primarily manual testing
- **Risk**: Regressions in complex coordinate transformations
- **Priority**: Add automated tests for core algorithms

#### Configuration Management
- **Current**: Hard-coded paths in multiple files
- **Risk**: Changes require updates across multiple scripts
- **Priority**: Centralized configuration system

#### Error Handling
- **Current**: Basic exception handling in scripts
- **Risk**: Unclear error messages for users
- **Priority**: Comprehensive error reporting system

## 📚 9. Documentation and Resources

### Existing Documentation
- **`CLAUDE.md`** (16KB) - Comprehensive development guide and command reference
- **`README.md`** - Project overview and setup instructions
- **`QUICKSTART.md`** - Essential 10-minute setup guide
- **`PRPs-agentic-eng/README.md`** - Pipeline-specific documentation
- **`docs/music-debug-knowledge.md`** - Auto-updated debug knowledge base

### API Documentation
N/A - Desktop application without external APIs

### Database Schemas
```python
# Core data structures (Python dataclasses)
@dataclass
class XMLNote:
    part_id: str
    note_name: str
    octave: int
    measure: int
    staff: int
    svg_x: float
    svg_y: float

@dataclass
class MIDINote:
    start_time_seconds: float
    duration_seconds: float
    pitch: int
    velocity: int
    channel: int

# Universal coordination
@dataclass
class UniversalNote:
    universal_id: str
    xml_data: XMLNote
    midi_data: MIDINote
    audio_filename: str
    keyframes_filename: str
```

### Deployment Guides
- **Local Setup**: Covered in Getting Started section
- **After Effects Integration**: `Extensions/Sib2Ae-Importer/README.md`
- **No server deployment** - desktop application only

### Team Conventions
- **File Naming**: Descriptive names with functionality clear
- **Code Style**: Python PEP 8, comprehensive docstrings
- **Directory Structure**: Pipeline-based organization
- **Agent Integration**: Use specialized agents for all Sib2Ae work

### Style Guides
- **Python**: PEP 8 with detailed docstrings
- **JavaScript**: Standard JS for After Effects scripts
- **File Organization**: Pipeline-based with clear separation of concerns

## ✅ 10. Onboarding Checklist

### Environment Setup
- [ ] **Install Python 3.12+** - `python3 --version` should show 3.12 or higher
- [ ] **Install uv package manager** - `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [ ] **Install FluidSynth** - `brew install fluidsynth` (macOS) or platform equivalent
- [ ] **Clone repository** - `git clone [repository-url]`
- [ ] **Setup dependencies** - `uv sync && pip install mido librosa soundfile numpy`
- [ ] **Verify installation** - Run dependency check command

### Project Familiarization
- [ ] **Read CLAUDE.md** - Understand development guidelines and commands
- [ ] **Explore repository structure** - Navigate through key directories
- [ ] **Review sample data** - Examine files in `PRPs-agentic-eng/Base/`
- [ ] **Understand Universal ID system** - Review `note_coordinator.py`

### First Successful Run
- [ ] **Launch GUI** - `python3 sib2ae_gui.py` should open without errors
- [ ] **Run symbolic pipeline** - Process sample MusicXML → SVG
- [ ] **Run audio pipeline** - Process sample MIDI → audio files
- [ ] **View outputs** - Examine generated files in output directories

### Make a Test Change
- [ ] **Identify area of interest** - Choose symbolic, audio, or synchronization component
- [ ] **Read relevant scripts** - Understand current implementation
- [ ] **Make small modification** - Add logging or change parameter
- [ ] **Test change** - Verify modification works as expected

### Understanding Main Workflow
- [ ] **Follow data flow** - MusicXML → SVG extraction → Audio generation → Synchronization
- [ ] **Understand coordinate system** - Staff positioning and Y-coordinate mapping
- [ ] **Trace Universal ID** - How notes link across formats
- [ ] **Review After Effects integration** - Import tools and workflow

### Development Environment
- [ ] **Configure IDE** - Setup Python environment with project root
- [ ] **Understand git workflow** - Current branching strategy
- [ ] **Run existing tests** - `python -m pytest` in PRPs-agentic-eng directory
- [ ] **Review debug knowledge** - Read `docs/music-debug-knowledge.md`

### Team Integration
- [ ] **Understand agent system** - Must use sib2ae-sync-orchestrator and sib2ae-pipeline-debugger
- [ ] **Review development patterns** - Pipeline organization and file naming conventions
- [ ] **Identify contribution area** - Choose focus area (symbolic, audio, sync, GUI, or AE integration)

### Next Steps
- [ ] **Choose first contribution** - Start with small improvement or bug fix
- [ ] **Set up development workflow** - Regular testing and debug knowledge updates
- [ ] **Connect with project goals** - Understand roadmap and priorities

## 🎯 Success Metrics

You're successfully onboarded when you can:

1. **Run the complete pipeline** from MusicXML input to After Effects-ready output
2. **Understand the Universal ID system** and how it maintains relationships across formats
3. **Use the GUI effectively** for testing and development
4. **Make a meaningful code contribution** that processes correctly with the sample data
5. **Debug pipeline issues** using the debug knowledge base and specialized agents

## 🆘 Getting Help

- **Documentation**: Start with `CLAUDE.md` for comprehensive command reference
- **Debug Issues**: Check `docs/music-debug-knowledge.md` for known solutions
- **Agent Support**: Use `sib2ae-sync-orchestrator` for development tasks
- **Sample Data**: Test with Saint-Saëns Trio No. 2 files in `PRPs-agentic-eng/Base/`

Welcome to the Sib2Ae development team! 🎵