# Universal ID Pipeline Orchestrator

A comprehensive orchestration system for the Sib2Ae pipeline, maintaining Universal ID integrity throughout all processing stages from MusicXML/MIDI input to synchronized After Effects-ready output.

## 🎯 Overview

The Universal ID Pipeline Orchestrator coordinates the complete Sib2Ae pipeline execution with:

- **Universal ID Preservation**: Maintains unique identifiers across all pipeline stages
- **Atomic Operations**: Safe manifest updates with backup and recovery
- **Circuit Breaker Pattern**: Robust error handling and failure recovery
- **Real-time Progress Tracking**: Universal ID-level granularity progress reporting
- **Pipeline Coordination**: Sequential and parallel execution modes

## 📦 Package Structure

```
orchestrator/
├── __init__.py                 # Package exports and version info
├── pipeline_stage.py          # Pipeline stage definitions and factory functions
├── universal_registry.py      # Universal ID tracking and filename transformations
├── manifest_manager.py        # Atomic manifest operations with backup/recovery
├── progress_tracker.py        # Real-time progress tracking with tqdm integration
├── error_handlers.py          # Circuit breaker pattern and retry mechanisms
├── note_coordinator.py        # Universal note coordination and registry creation
├── tied_note_processor.py     # Tied note relationship processing
├── universal_orchestrator.py  # Main orchestrator script
├── xml_temporal_parser.py     # MusicXML temporal parsing utilities
├── midi_matcher.py            # MIDI note matching utilities
├── tests/                      # Comprehensive test suite (32 tests)
│   ├── test_pipeline_stage.py
│   ├── test_manifest_manager.py
│   └── test_error_handlers.py
└── README.md                   # This file
```

## 🚀 Quick Start

### Basic Usage

```python
from orchestrator import (
    OrchestrationConfig,
    UniversalOrchestrator,
    ExecutionMode
)
from pathlib import Path

# Configure the pipeline
config = OrchestrationConfig(
    musicxml_file=Path("Base/SS 9.musicxml"),
    midi_file=Path("Base/Saint-Saens Trio No 2.mid"),
    svg_file=Path("Base/SS 9 full.svg"),
    output_dir=Path("universal_output"),
    execution_mode=ExecutionMode.SEQUENTIAL
)

# Create orchestrator instance
orchestrator = UniversalOrchestrator(config)

# Execute complete pipeline
result = orchestrator.orchestrate_complete_pipeline()
```

### Command Line Usage

```bash
# From project root directory
python Brain/orchestrator/universal_orchestrator.py \
    "Brain/Base/SS 9.musicxml" \
    "Brain/Base/Saint-Saens Trio No 2.mid" \
    --svg "Brain/Base/SS 9 full.svg" \
    --output "universal_output" \
    --mode sequential

# Python module execution (recommended)
python -m Brain.orchestrator.universal_orchestrator \
    "Brain/Base/SS 9.musicxml" \
    "Brain/Base/Saint-Saens Trio No 2.mid" \
    --svg "Brain/Base/SS 9 full.svg" \
    --mode sequential

# Background execution (avoids verbose logs in Claude Code)
python -m Brain.orchestrator.universal_orchestrator \
    "Brain/Base/SS 9.musicxml" \
    "Brain/Base/Saint-Saens Trio No 2.mid" \
    --svg "Brain/Base/SS 9 full.svg" \
    --mode sequential > /dev/null 2>&1 &
```

## 💻 Claude Code Usage

### Context Management
When using the orchestrator in Claude Code sessions, avoid context pollution from verbose logs:

```bash
# Background execution (recommended for Claude Code)
python -m Brain.orchestrator.universal_orchestrator \
    "Brain/Base/SS 9.musicxml" \
    "Brain/Base/Saint-Saens Trio No 2.mid" \
    --svg "Brain/Base/SS 9 full.svg" \
    --mode sequential > /dev/null 2>&1 &

# Check completion
ls -la universal_output/
ls -la outputs/
```

### Quick Verification
```bash
# Verify pipeline completion
find outputs/ -name "*.wav" | wc -l     # Count audio files
find outputs/ -name "*.svg" | wc -l     # Count SVG files
find outputs/ -name "*keyframes*.json" | wc -l  # Count keyframes
```

### Status Monitoring
```bash
# Monitor progress without verbose output
tail -f universal_output/logs/progress.log | grep "Stage completed"
```

## 🏗️ Core Components

### 1. Pipeline Stage (`pipeline_stage.py`)

Defines pipeline stages and orchestration configuration:

```python
from orchestrator import PipelineStage, OrchestrationConfig, ExecutionMode

# Create pipeline stages
config = OrchestrationConfig(...)
note_stage = create_note_coordinator_stage(config)
symbolic_stages = create_symbolic_pipeline_stages(config)
audio_stages = create_audio_pipeline_stages(config)
```

**Key Features:**
- Stage dependency management
- Factory functions for Sib2Ae pipeline stages
- Execution mode configuration (sequential/parallel)
- Stage timeout and retry configuration

### 2. Universal Registry (`universal_registry.py`)

Tracks Universal IDs across all pipeline stages:

```python
from orchestrator import UniversalFileRegistry

registry = UniversalFileRegistry()

# Initialize from Note Coordinator output
registry.initialize_from_note_coordinator("universal_notes_registry.json")

# Transform filenames with Universal IDs
original = "note_000_Flûte_A4_vel76.wav"
transformed = registry.transform_filename_with_uuid(original, universal_id)
# Result: "Flûte_A4_vel76_2584.wav"

# Track file creation
registry.register_file_creation(universal_id, "audio_rendering", file_path)

# Validate integrity
integrity_report = registry.validate_universal_id_integrity()
```

**Key Features:**
- Universal ID to filename mapping
- Stage-specific file tracking
- Integrity validation and reporting
- Sib2Ae-specific filename transformations

### 3. Manifest Manager (`manifest_manager.py`)

Provides atomic manifest operations with backup and recovery:

```python
from orchestrator import AtomicManifestManager

manager = AtomicManifestManager(backup_enabled=True)

# Atomic manifest updates
def update_func(data):
    data["new_field"] = "value"
    return data

success = manager.update_manifest_atomically(manifest_path, update_func)

# Update with Universal ID information
manager.update_manifest_with_universal_id(
    manifest_path, universal_id, stage_name, file_path, metadata
)

# Validate manifest integrity
validation = manager.validate_manifest_integrity(manifest_path)
```

**Key Features:**
- Atomic write operations with temporary files
- Automatic backup creation and restoration
- File locking for concurrent access protection
- Manifest integrity validation

### 4. Progress Tracker (`progress_tracker.py`)

Real-time progress tracking with Universal ID granularity:

```python
from orchestrator import ProgressTracker

# Initialize with expected Universal IDs
tracker = ProgressTracker(
    total_universal_ids=100,
    expected_stages=["note_coordinator", "audio_rendering", ...]
)

# Track stage progress
with tracker:
    tracker.start_stage("audio_rendering", universal_id_set)

    for universal_id in universal_ids:
        tracker.update_universal_id_operation(
            universal_id, "audio_rendering", "Processing audio..."
        )

        # On completion
        tracker.complete_universal_id(
            universal_id, "audio_rendering",
            files_created=["audio.wav"],
            metadata={"duration": 3.5}
        )

    tracker.complete_stage("audio_rendering")

# Get comprehensive progress information
progress = tracker.get_overall_progress()
```

**Key Features:**
- tqdm-based progress visualization
- Universal ID-level tracking
- Stage completion monitoring
- Comprehensive progress reporting
- Thread-safe operations

### 5. Error Handlers (`error_handlers.py`)

Circuit breaker pattern and retry mechanisms for robust pipeline execution:

```python
from orchestrator import (
    CircuitBreaker,
    RetryMechanism,
    ProcessFailureHandler,
    create_process_failure_handler
)

# Create failure handler with circuit breaker and retry
handler = create_process_failure_handler(
    name="audio_processor",
    enable_circuit_breaker=True,
    enable_retry=True
)

# Execute subprocess with failure handling
result = handler.execute_subprocess(
    command=["python", "audio_renderer.py", "input.mid"],
    timeout=300.0,
    cwd=Path("audio_processing")
)

# Get handler statistics
stats = handler.get_statistics()
```

**Key Features:**
- Circuit breaker pattern with automatic recovery
- Exponential backoff retry mechanisms
- Subprocess execution protection
- Comprehensive failure statistics
- Configurable thresholds and timeouts

## 🧪 Testing

The orchestrator package includes a comprehensive test suite with 32 tests covering all components:

```bash
# Run all tests
uv run pytest orchestrator/tests/ -v

# Run specific test modules
uv run pytest orchestrator/tests/test_pipeline_stage.py -v
uv run pytest orchestrator/tests/test_manifest_manager.py -v
uv run pytest orchestrator/tests/test_error_handlers.py -v

# Run with coverage
uv run pytest orchestrator/tests/ --cov=orchestrator --cov-report=html
```

### Test Coverage

- **Pipeline Stage Tests**: Stage creation, configuration validation, factory functions
- **Manifest Manager Tests**: Atomic operations, backup/restore, integrity validation
- **Error Handler Tests**: Circuit breaker patterns, retry mechanisms, failure classification

## ⚙️ Configuration

### OrchestrationConfig Options

```python
config = OrchestrationConfig(
    # Required files
    musicxml_file=Path("Base/SS 9.musicxml"),
    midi_file=Path("Base/Saint-Saens Trio No 2.mid"),
    svg_file=Path("Base/SS 9 full.svg"),
    output_dir=Path("universal_output"),

    # Execution settings
    execution_mode=ExecutionMode.SEQUENTIAL,  # or PARALLEL
    max_workers=4,
    stage_timeout_seconds=600.0,
    max_stage_retries=3,

    # Universal ID settings
    preserve_universal_ids=True,
    validate_universal_id_integrity=True,
    apply_new_filename_pattern=True,

    # Error handling
    enable_circuit_breaker=True,
    continue_on_non_critical_failure=True,

    # Manifest management
    atomic_manifest_updates=True,
    manifest_backup_enabled=True,
    backup_existing_outputs=True,

    # Performance settings
    audio_renderer_mode="fast",  # or "standard"
    keyframe_generator_mode="fast",  # or "standard"

    # Monitoring
    verbose=True,
    progress_callback=None,
    log_file=Path("orchestrator.log")
)
```

## 🎼 Sib2Ae Pipeline Integration

The orchestrator coordinates the complete Sib2Ae pipeline with these stages:

### Coordination Stages
1. **Note Coordinator**: Creates Universal ID registry linking MusicXML, MIDI, and SVG data
2. **Tied Note Processor**: Processes tied note relationships with timing calculations

### Symbolic Pipeline (5 stages)
3. **Noteheads Extraction**: Extract noteheads from MusicXML with pixel-perfect coordinates
4. **Noteheads Subtraction**: Remove noteheads from SVG while preserving other elements
5. **Instrument Separation**: Create individual SVG files per instrument
6. **Individual Noteheads Creation**: Create one SVG file per notehead for After Effects
7. **Staff/Barlines Extraction**: Extract staff lines and barlines for background elements

### Audio Pipeline (3 stages)
8. **MIDI Note Separation**: Split MIDI files into individual note files
9. **Audio Rendering**: Convert MIDI notes to audio files (fast/standard modes)
10. **Keyframe Generation**: Generate After Effects keyframes from audio analysis

## 🔗 Universal ID System

The Universal ID system maintains relationships between:

- **MusicXML Notes**: Part ID, pitch, timing, measure information
- **MIDI Events**: Start time, velocity, duration, channel
- **SVG Elements**: Pixel coordinates, visual properties
- **Audio Files**: Rendered waveforms with instrument-specific parameters
- **Keyframes**: After Effects animation data synchronized to audio

### Filename Transformation

Original pipeline filenames are transformed to include Universal ID suffixes:

```
note_000_Flûte_A4_vel76.wav → Flûte_A4_vel76_2584.wav
note_001_Violon_B3_vel64.mid → Violon_B3_vel64_7e3f.mid
```

This ensures every file can be traced back to its source Universal ID throughout the pipeline.

## 📊 Monitoring and Logging

### Progress Tracking

- Real-time progress bars with tqdm
- Universal ID-level completion tracking
- Stage-by-stage progress reporting
- Time estimation and performance metrics

### Error Monitoring

- Circuit breaker state tracking
- Retry attempt monitoring
- Failure classification and statistics
- Comprehensive error logging

### Manifest Validation

- Universal ID integrity checking
- File dependency validation
- Manifest consistency verification
- Backup and recovery status

## 🚀 Production Usage

### Performance Considerations

- **Sequential Mode**: Reliable, predictable execution order
- **Parallel Mode**: Faster execution with dependency management
- **Fast Modes**: Optimized audio rendering (22kHz) and keyframe generation
- **Circuit Breakers**: Automatic failure detection and recovery

### Monitoring in Production

```python
# Set up progress callback for monitoring
def progress_callback(progress_data):
    print(f"Stage: {progress_data['stage']}")
    print(f"Progress: {progress_data['progress']['completion_percentage']:.1f}%")

config = OrchestrationConfig(
    # ... other settings
    progress_callback=progress_callback,
    log_file=Path("production.log"),
    verbose=True
)
```

### Error Recovery

The orchestrator provides multiple levels of error recovery:

1. **Retry Mechanisms**: Automatic retry with exponential backoff
2. **Circuit Breakers**: Prevent cascade failures, automatic recovery
3. **Atomic Operations**: Manifest corruption prevention
4. **Backup Systems**: Automatic backup creation and restoration

## 📚 API Reference

### Main Classes

- **`UniversalOrchestrator`**: Main orchestration coordinator
- **`OrchestrationConfig`**: Configuration dataclass
- **`PipelineStage`**: Individual pipeline stage representation
- **`UniversalFileRegistry`**: Universal ID tracking system
- **`AtomicManifestManager`**: Safe manifest operations
- **`ProgressTracker`**: Real-time progress monitoring
- **`CircuitBreaker`**: Failure detection and recovery
- **`ProcessFailureHandler`**: Subprocess execution protection

### Factory Functions

- **`create_note_coordinator_stage(config)`**
- **`create_tied_note_processor_stage(config)`**
- **`create_symbolic_pipeline_stages(config)`**
- **`create_audio_pipeline_stages(config)`**
- **`create_manifest_manager(backup_enabled, verbose)`**
- **`create_process_failure_handler(name, enable_circuit_breaker, enable_retry)`**

## 🤝 Contributing

### Development Setup

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest orchestrator/tests/ -v

# Code formatting
uv run ruff format orchestrator/
uv run ruff check orchestrator/ --fix

# Type checking
uv run mypy orchestrator/
```

### Adding New Pipeline Stages

1. Define stage in `pipeline_stage.py`
2. Add factory function for stage creation
3. Update `OrchestrationConfig` if needed
4. Add comprehensive tests
5. Update documentation

## 📄 License

Part of the Sib2Ae project - Music notation to After Effects synchronization pipeline.

## 🎯 Version

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: September 2025

---

🎼 **Ready to orchestrate your complete Sib2Ae pipeline with Universal ID integrity!**