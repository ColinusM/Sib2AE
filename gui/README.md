# Sib2Ae GUI

A modular graphical interface for the Sib2Ae music notation to After Effects synchronization pipeline, providing intuitive access to symbolic processing, audio rendering, and MIDI-XML-SVG coordination workflows.

## 🎯 Overview

The Sib2Ae GUI provides a user-friendly interface for executing the complete Sib2Ae pipeline through three specialized tabs:

- **Symbolic Pipeline Tab**: Process MusicXML and SVG files for notation separation
- **Audio Pipeline Tab**: Convert MIDI to audio files and After Effects keyframes
- **Matching Tab**: Coordinate MIDI-XML-SVG data with Universal ID system

**Key Features:**
- File browser integration for all input files
- Real-time script output display
- Modular tab-based architecture
- Auto-saved settings and preferences
- Progress tracking and error handling

## 📦 Package Structure

```
gui/
├── __init__.py                 # Package initialization
├── sib2ae_gui.py              # Main GUI application (140 lines)
├── symbolic_tab.py            # Symbolic pipeline interface
├── audio_tab.py               # Audio pipeline interface
├── matching_tab.py            # MIDI-XML-SVG coordination interface
├── settings.py                # Settings management and persistence
├── script_runner.py           # Subprocess execution with output capture
└── README.md                  # This file
```

## 🚀 Quick Start

### Launch GUI

```bash
# From project root directory
python3 launch_gui.py
```

### Requirements

- **Python 3.8+** with tkinter support
- **Sib2Ae pipeline dependencies** (see main CLAUDE.md)
- **Working directory**: `/Users/colinmignot/Claude Code/Sib2Ae/`

### Default Input Files

The GUI automatically loads these default files if available:
- **MusicXML**: `PRPs-agentic-eng/Base/SS 9.musicxml`
- **SVG**: `PRPs-agentic-eng/Base/SS 9 full.svg`
- **MIDI**: `PRPs-agentic-eng/Base/Saint-Saens Trio No 2.mid`

## 🏗️ Core Components

### 1. Main Application (`sib2ae_gui.py`)

The main GUI coordinator with modular tab architecture:

```python
from gui.sib2ae_gui import main

# Launch GUI
main()
```

**Features:**
- Tabbed interface with three specialized pipelines
- Auto-saved window geometry and preferences
- File existence checking with visual indicators
- Real-time output log with scrollable text area

### 2. Symbolic Pipeline Tab (`symbolic_tab.py`)

Handles SVG and MusicXML processing workflows:

**Available Scripts:**
1. **Noteheads Extraction** - Extract noteheads with pixel-perfect coordinates
2. **Noteheads Subtraction** - Remove noteheads while preserving other elements
3. **Instrument Separation** - Create individual SVG files per instrument
4. **Individual Noteheads Creation** - Generate one SVG per notehead for After Effects
5. **Staff Barlines Extraction** - Extract staff lines and barlines for backgrounds

**UI Elements:**
- File browsers for MusicXML and SVG inputs
- Output directory selection
- One-click execution buttons for each script
- Real-time progress and output display

### 3. Audio Pipeline Tab (`audio_tab.py`)

Manages MIDI-to-audio conversion and keyframe generation:

**Available Scripts:**
1. **MIDI Note Separation** - Split MIDI into individual note files
2. **Audio Rendering (Fast)** - Parallel audio conversion (22kHz, 6 workers)
3. **Audio Rendering (Standard)** - Sequential high-quality conversion (44kHz)
4. **Keyframe Generation (Fast)** - Essential properties for After Effects
5. **Keyframe Generation (Standard)** - Comprehensive audio analysis

**UI Elements:**
- MIDI file browser and validation
- Directory selectors for intermediate and output files
- Mode selection (Fast vs Standard rendering)
- Batch execution options

### 4. Matching Tab (`matching_tab.py`)

Coordinates MIDI-XML-SVG data with Universal ID system:

**Functionality:**
- **Note Coordinator Execution** - Creates Universal ID registry
- **Match Results Display** - Shows coordination statistics
- **Annotated SVG Generation** - Creates timing-labeled notation
- **Universal ID Validation** - Ensures data integrity across pipeline

**UI Elements:**
- Three-file input selection (XML, MIDI, SVG)
- Coordination metadata display
- Match rate statistics (typical: 66.7% due to tied notes)
- Output directory selection with automatic file detection

### 5. Settings Management (`settings.py`)

Persistent configuration and preferences:

```python
from gui.settings import GUISettings

settings = GUISettings()
# Auto-loads from gui_settings.json
# Auto-saves on application close
```

**Managed Settings:**
- Window geometry (size and position)
- Default file paths for all input types
- Output directory preferences
- UI state preservation

**Configuration File**: `gui_settings.json` (auto-generated)

### 6. Script Runner (`script_runner.py`)

Subprocess execution with real-time output capture:

**Features:**
- Non-blocking subprocess execution
- Real-time stdout/stderr capture
- Error handling and status reporting
- Thread-safe output redirection to GUI

## 🎼 Pipeline Integration

### Symbolic Processing Workflow

1. **Load Files**: Select MusicXML and SVG using file browsers
2. **Configure Output**: Choose destination directory
3. **Execute Scripts**: Run individual separators or batch process
4. **Monitor Progress**: View real-time output in log area
5. **Verify Results**: Check generated SVG files in output directory

### Audio Processing Workflow

1. **Select MIDI**: Choose source MIDI file
2. **Choose Mode**: Fast (22kHz, parallel) or Standard (44kHz, sequential)
3. **Set Directories**: Configure intermediate and final output paths
4. **Execute Pipeline**: Run note separation → audio rendering → keyframe generation
5. **Review Output**: Audio files organized by instrument + JSON keyframes

### Coordination Workflow

1. **Input Trio**: Select MusicXML, MIDI, and SVG files
2. **Run Coordinator**: Execute Universal ID registry creation
3. **View Statistics**: Check match rates and coordination metadata
4. **Generate Annotated SVG**: Create timing-labeled notation
5. **Validate Registry**: Ensure Universal ID integrity

## ⚙️ Configuration

### GUI Settings

The GUI automatically manages settings in `gui_settings.json`:

```json
{
  "window_width": 1000,
  "window_height": 700,
  "window_x": 100,
  "window_y": 100,
  "default_musicxml": "PRPs-agentic-eng/Base/SS 9.musicxml",
  "default_svg": "PRPs-agentic-eng/Base/SS 9 full.svg",
  "default_midi": "PRPs-agentic-eng/Base/Saint-Saens Trio No 2.mid",
  "project_root": "/Users/colinmignot/Claude Code/Sib2Ae"
}
```

### File Path Management

The GUI automatically handles:
- **Relative path resolution** from project root
- **File existence validation** with visual indicators
- **Directory creation** for output paths
- **Cross-platform path normalization**

## 🎯 Usage Examples

### Basic Symbolic Processing

1. Launch GUI: `python3 launch_gui.py`
2. Navigate to **Symbolic Pipeline** tab
3. Verify MusicXML and SVG files are loaded
4. Click **"Extract Noteheads"** to start processing
5. Monitor output log for progress and completion
6. Check `instruments_output/` for generated SVG files

### Complete Audio Pipeline

1. Switch to **Audio Pipeline** tab
2. Select MIDI file using file browser
3. Choose **Fast** mode for rapid processing
4. Click **"Separate MIDI Notes"** (foundation step)
5. Click **"Render Audio (Fast)"** for parallel conversion
6. Click **"Generate Keyframes (Fast)"** for After Effects data
7. Review `PRPs-agentic-eng/Audio/` for organized output

### Universal ID Coordination

1. Open **Matching** tab
2. Ensure all three files (XML, MIDI, SVG) are selected
3. Click **"Run Note Coordinator"**
4. Review match statistics in output area
5. Check `universal_output/` for coordination metadata
6. View `output/` for annotated SVG with timing labels

## 📊 Output Organization

### Generated Files by Tab

**Symbolic Pipeline Output:**
- `instruments_output/` - Individual SVG files per instrument
- Individual notehead SVG files for After Effects animation
- Staff lines and barlines SVGs for background elements

**Audio Pipeline Output:**
- `PRPs-agentic-eng/Audio/Flûte/` - Flute audio files
- `PRPs-agentic-eng/Audio/Violon/` - Violin audio files
- `PRPs-agentic-eng/Audio/Keyframes/` - JSON keyframe data

**Matching Output:**
- `universal_output/universal_notes_registry.json` - Universal ID database
- `universal_output/coordination_metadata.json` - Match statistics
- `output/` - Annotated SVG files with MIDI timing labels

## 🔧 Technical Details

### Threading Architecture

- **Main Thread**: GUI event loop and user interaction
- **Worker Threads**: Subprocess execution for script running
- **Output Capture**: Real-time stdout/stderr redirection
- **Thread-Safe Logging**: Queue-based message passing to GUI

### Error Handling

- **File Validation**: Pre-execution checks for required inputs
- **Subprocess Monitoring**: Real-time error capture and display
- **Graceful Degradation**: Continue operation when non-critical scripts fail
- **User Feedback**: Clear error messages and resolution guidance

### Performance Considerations

- **Non-Blocking Execution**: GUI remains responsive during processing
- **Parallel Audio Rendering**: 6-worker parallel processing for speed
- **Memory Management**: Efficient subprocess lifecycle management
- **Output Buffering**: Optimized text display for large log outputs

## 🚀 Integration with Universal Orchestrator

The GUI provides manual control over the same pipeline stages automated by the Universal ID Pipeline Orchestrator:

**Shared Components:**
- Same underlying Python scripts
- Identical file input/output patterns
- Compatible Universal ID system
- Consistent error handling approaches

**Complementary Usage:**
- **GUI**: Interactive exploration and testing
- **Orchestrator**: Automated production pipeline execution
- **Both**: Universal ID preservation and validation

## 📚 API Integration

### Launching from Python

```python
import tkinter as tk
from gui.sib2ae_gui import Sib2AeSimpleGUI

# Create and run GUI
root = tk.Tk()
app = Sib2AeSimpleGUI(root)
root.mainloop()
```

### Programmatic Script Execution

```python
from gui.script_runner import ScriptRunner

def log_callback(message):
    print(f"Script output: {message}")

runner = ScriptRunner(log_callback)
runner.run_script("path/to/script.py", ["arg1", "arg2"])
```

## 🤝 Contributing

### Development Setup

```bash
# Install GUI dependencies (usually included with Python)
python3 -c "import tkinter; print('tkinter available')"

# Launch in development mode
python3 launch_gui.py
```

### Adding New Scripts

1. Update appropriate tab file (`symbolic_tab.py`, `audio_tab.py`, `matching_tab.py`)
2. Add button and callback method
3. Configure file path variables if needed
4. Test execution and output capture
5. Update this README documentation

### UI Customization

- **Tab Layout**: Modify individual tab files for interface changes
- **Settings**: Update `settings.py` for new configuration options
- **Themes**: Enhance tkinter styling in main GUI file
- **File Browsers**: Extend file selection capabilities as needed

## 📄 License

Part of the Sib2Ae project - Music notation to After Effects synchronization pipeline.

## 🎯 Version

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: September 2025

---

🎼 **Ready to orchestrate your Sib2Ae pipeline with an intuitive graphical interface!**