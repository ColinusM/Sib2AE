name: "Universal ID Pipeline Orchestrator PRP"
description: |
  Comprehensive PRP for implementing a master orchestrator script that coordinates
  Note Coordinator, Tied Note Processor, and all pipeline scripts while maintaining
  Universal ID integrity throughout the entire Sib2Ae pipeline system.

---

## Goal

**Feature Goal**: Create a master orchestrator script that runs the complete Sib2Ae pipeline from MusicXML/MIDI input to synchronized After Effects-ready output, maintaining Universal ID relationships throughout all processing stages.

**Deliverable**: Python script `universal_orchestrator.py` that coordinates Note Coordinator → Tied Note Processor → Symbolic Pipeline → Audio Pipeline → Verification, with comprehensive progress tracking, error handling, and manifest management.

**Success Definition**:
- Takes MusicXML + MIDI files as input
- Generates individual noteheads, audio files, and keyframes all linked by Universal IDs
- Produces enhanced manifests with tied note timing calculations
- Maintains file chain integrity: `Flûte_A4_vel76_2584.wav` ↔ `Flûte_A4_vel76_2584_keyframes.json` ↔ notehead SVG
- Provides comprehensive progress reporting and error recovery

## User Persona

**Target User**: Music technology developer/composer using Sib2Ae pipeline

**Use Case**: Convert musical scores (MusicXML + MIDI) into synchronized After Effects animations

**User Journey**:
1. User runs: `python universal_orchestrator.py "score.musicxml" "performance.mid"`
2. Orchestrator automatically handles Note Coordinator → Tied Note Processor → Pipeline execution
3. User receives complete output with Universal ID-linked files ready for After Effects import

**Pain Points Addressed**:
- Manual pipeline coordination complexity
- Universal ID tracking across multiple scripts
- Tied note timing calculation coordination
- File dependency management and error recovery

## Why

- **Business Value**: Enables automated music-to-video synchronization workflow
- **Integration**: Unifies existing pipeline scripts under single coordinated execution
- **Problems Solved**: Universal ID preservation, tied note handling, dependency management, error recovery

## What

A master orchestrator that:
- Executes complete pipeline: Note Coordinator → Tied Note Processor → Symbolic → Audio → Verification
- Maintains Universal ID relationships across all processing stages
- Handles tied note detection and timing calculation automatically
- Provides real-time progress tracking with Universal ID-level granularity
- Implements robust error recovery with partial failure handling
- Updates manifests atomically throughout pipeline execution

### Success Criteria

- [ ] Coordinates 5+ pipeline stages with dependency management
- [ ] Maintains Universal ID integrity from input to final output files
- [ ] Automatically detects and processes tied notes with timing calculations
- [ ] Implements circuit breaker pattern for robust error handling
- [ ] Provides comprehensive progress reporting with file-level tracking
- [ ] Generates enhanced manifests compatible with After Effects import
- [ ] Supports both sequential and parallel execution modes

## All Needed Context

### Context Completeness Check

_This PRP provides complete codebase analysis, external best practices research, existing integration patterns, and step-by-step implementation guidance for successful one-pass orchestrator implementation._

### Documentation & References

```yaml
# CRITICAL: Advanced orchestration patterns from codebase analysis
- file: PRPs-agentic-eng/App/Synchronizer 19-26-28-342/synchronization_coordinator.py
  why: Master orchestration pattern with PipelineStage dataclass, dependency management
  pattern: Phase-based execution, comprehensive error tracking, dual execution modes
  gotcha: Uses dataclass-driven configuration for stage coordination

- file: PRPs-agentic-eng/note_coordinator.py
  why: Universal ID system implementation, manifest generation patterns
  pattern: UniversalNote dataclass linking XML/MIDI/SVG, coordinate transformation
  gotcha: Universal ID must propagate through filename chains, not just manifests

- file: PRPs-agentic-eng/App/Synchronizer 19-26-28-342/utils/tied_note_processor.py
  why: Tied note detection and timing calculation logic, 3:1 notehead-MIDI relationships
  pattern: TiedNoteAssignment with calculated_start_time, proportional timing algorithm
  gotcha: Always run tied processor - it detects tied notes automatically, no pre-check needed

- file: gui/script_runner.py
  why: Async subprocess execution pattern with progress tracking
  pattern: Background thread execution, real-time logging callbacks
  gotcha: Threading for non-blocking execution, subprocess capture_output=True

- docfile: PRPs/ai_docs/orchestrator_patterns.md
  why: File naming conventions, manifest update patterns, Universal ID tracking
  section: Universal Constants, Atomic Manifest Updates, File Chain Preservation

# MUST READ: External best practices for orchestrator implementation
- url: https://dagster.io/vs/dagster-vs-prefect
  why: Modern orchestration patterns, dependency graph management
  critical: Asset-oriented pipelines, dataclass-driven configuration approaches

- url: https://realpython.com/python-subprocess/
  why: Robust subprocess management with error handling
  critical: async subprocess patterns, capture_output and text parameters

- url: https://medium.com/@fahimad/resilient-apis-retry-logic-circuit-breakers-and-fallback-mechanisms-cfd37f523f43
  why: Circuit breaker pattern for process failure resilience
  critical: CircuitState enum, failure threshold patterns, timeout management
```

### Current Codebase Tree

```bash
PRPs-agentic-eng/
├── note_coordinator.py                    # Universal ID generation (EXISTING)
├── App/
│   ├── Synchronizer 19-26-28-342/
│   │   ├── synchronization_coordinator.py # Master orchestration pattern (EXISTING)
│   │   └── utils/
│   │       └── tied_note_processor.py     # Tied note logic (EXISTING)
│   ├── Symbolic Separators/              # 5 symbolic pipeline scripts (EXISTING)
│   │   ├── individual_noteheads_creator.py
│   │   ├── xml_based_instrument_separator.py
│   │   └── [3 more scripts...]
│   └── Audio Separators/                  # 3 audio pipeline scripts (EXISTING)
│       ├── midi_note_separator.py
│       ├── midi_to_audio_renderer_fast.py
│       └── audio_to_keyframes_fast.py
├── universal_output/                      # Note Coordinator output (EXISTING)
├── Audio/                                 # Audio pipeline output (EXISTING)
└── instruments_output/                    # SVG pipeline output (EXISTING)
```

### Desired Codebase Tree with New Files

```bash
PRPs-agentic-eng/
├── universal_orchestrator.py             # NEW: Master orchestrator script
├── orchestrator/                         # NEW: Orchestrator module
│   ├── __init__.py
│   ├── pipeline_stage.py                 # NEW: Stage coordination logic
│   ├── universal_registry.py             # NEW: Universal ID tracking
│   ├── manifest_manager.py               # NEW: Atomic manifest operations
│   ├── progress_tracker.py               # NEW: Progress reporting system
│   └── error_handlers.py                 # NEW: Circuit breaker, retry logic
└── [All existing files remain unchanged]
```

### Known Gotchas & Library Quirks

```python
# CRITICAL: Universal ID System Requirements
# Universal IDs must persist through filename chains, not just manifests background tracking
# Example: "2584802d-2469-4e45-8cf0-ff934e1032d7" → "Flûte_A4_vel76_2584.wav"

# CRITICAL: Tied Note Processor Logic
# Always run tied_note_processor.py - it auto-detects tied notes
# Do NOT pre-check for tied notes - processor handles detection internally

# CRITICAL: File Naming Pattern Changes
# User requested: {instrument}_{pitch}_vel{velocity}_{uuid_first4}.wav
# Replace existing: note_000_Flûte_A4_vel76.wav → Flûte_A4_vel76_2584.wav

# CRITICAL: Subprocess Management
# Use capture_output=True, text=True for proper subprocess handling
# Implement timeout parameters to prevent hanging processes

# CRITICAL: Manifest Updates
# Use atomicwrites for manifest updates to prevent corruption
# Manifests are "living documents" - updated at each pipeline stage

# CRITICAL: Working Directory
# All commands must run from project root: /Users/colinmignot/Claude Code/Sib2Ae/
```

## Implementation Blueprint

### Data Models and Structure

Create type-safe data models for orchestrator coordination:

```python
# orchestrator/pipeline_stage.py - Stage coordination
@dataclass
class PipelineStage:
    name: str                           # "note_coordinator", "tied_processor", etc.
    command: List[str]                  # Command to execute
    input_files: List[Path]             # Required input files
    output_files: List[Path]            # Expected output files
    depends_on: List[str]               # Stage dependencies
    status: str                         # "pending", "running", "completed", "failed"
    universal_ids_processed: List[str]  # Track which Universal IDs completed
    start_time: Optional[datetime]      # Execution timing
    end_time: Optional[datetime]
    error_message: Optional[str]        # Error details if failed

@dataclass
class OrchestrationConfig:
    musicxml_file: Path
    midi_file: Path
    output_dir: Path
    execution_mode: str                 # "sequential" or "parallel"
    max_workers: int                   # For parallel processing
    enable_circuit_breaker: bool       # Error resilience
    verbose: bool                      # Detailed logging
```

### Implementation Tasks (ordered by dependencies)

```yaml
Task 1: CREATE orchestrator/__init__.py
  - IMPLEMENT: Package initialization with imports
  - FOLLOW pattern: Standard Python package structure
  - NAMING: orchestrator package in PRPs-agentic-eng/
  - PLACEMENT: PRPs-agentic-eng/orchestrator/__init__.py

Task 2: CREATE orchestrator/pipeline_stage.py
  - IMPLEMENT: PipelineStage, OrchestrationConfig dataclasses
  - FOLLOW pattern: PRPs-agentic-eng/App/Synchronizer 19-26-28-342/synchronization_coordinator.py (dataclass patterns)
  - NAMING: PipelineStage class, OrchestrationConfig class
  - DEPENDENCIES: dataclasses, pathlib, datetime, typing
  - PLACEMENT: Core data structures for orchestration

Task 3: CREATE orchestrator/universal_registry.py
  - IMPLEMENT: UniversalFileRegistry class for Universal ID tracking
  - FOLLOW pattern: PRPs-agentic-eng/note_coordinator.py (Universal ID management)
  - NAMING: UniversalFileRegistry class, register_file_creation method
  - DEPENDENCIES: Import UniversalNote from note_coordinator
  - PLACEMENT: Universal ID state management and file tracking

Task 4: CREATE orchestrator/manifest_manager.py
  - IMPLEMENT: AtomicManifestManager class for safe manifest updates
  - FOLLOW pattern: External atomicwrites library usage
  - NAMING: AtomicManifestManager class, update_manifest_atomically method
  - DEPENDENCIES: atomicwrites, json, pathlib
  - PLACEMENT: Atomic file operations for manifest safety

Task 5: CREATE orchestrator/progress_tracker.py
  - IMPLEMENT: ProgressTracker class with Universal ID-level tracking
  - FOLLOW pattern: gui/script_runner.py (async execution, logging callbacks)
  - NAMING: ProgressTracker class, track_universal_id_progress method
  - DEPENDENCIES: logging, tqdm, json, datetime
  - PLACEMENT: Progress reporting and user feedback system

Task 6: CREATE orchestrator/error_handlers.py
  - IMPLEMENT: CircuitBreaker class, RetryMechanism class
  - FOLLOW pattern: External circuit breaker research patterns
  - NAMING: CircuitBreaker class, ProcessFailureHandler class
  - DEPENDENCIES: enum, time, logging, tenacity
  - PLACEMENT: Resilience patterns for subprocess failures

Task 7: CREATE universal_orchestrator.py
  - IMPLEMENT: UniversalOrchestrator class coordinating all pipeline stages
  - FOLLOW pattern: PRPs-agentic-eng/App/Synchronizer 19-26-28-342/synchronization_coordinator.py (orchestration)
  - NAMING: UniversalOrchestrator class, main() function
  - DEPENDENCIES: Import all orchestrator modules, subprocess, asyncio
  - PLACEMENT: Main orchestrator script in PRPs-agentic-eng/

Task 8: INTEGRATE Note Coordinator execution
  - IMPLEMENT: Note coordinator subprocess execution with manifest capture
  - FOLLOW pattern: gui/script_runner.py (subprocess management)
  - MODIFY: Extract Universal ID manifests, initialize file registry
  - DEPENDENCIES: Read universal_output/ manifests after Note Coordinator
  - VALIDATION: Verify Universal ID manifests created successfully

Task 9: INTEGRATE Tied Note Processor execution
  - IMPLEMENT: Tied note processor subprocess execution
  - FOLLOW pattern: Always run (auto-detection), capture enhanced manifests
  - MODIFY: Generate tied-note-enhanced manifests with timing calculations
  - DEPENDENCIES: Use Note Coordinator outputs as tied processor inputs
  - VALIDATION: Verify enhanced manifests contain timing calculations

Task 10: INTEGRATE Symbolic Pipeline coordination
  - IMPLEMENT: Execute 5 symbolic scripts with Universal ID manifest updates
  - FOLLOW pattern: Individual execution of each symbolic script with dependency order
  - MODIFY: Update manifests after each script with actual filenames created
  - DEPENDENCIES: Read manifests, execute scripts, update with actual file paths
  - VALIDATION: Verify individual SVG files created and manifests updated

Task 11: INTEGRATE Audio Pipeline coordination
  - IMPLEMENT: Execute 3 audio scripts with Universal ID filename preservation
  - FOLLOW pattern: Parallel processing for audio rendering (6 workers)
  - MODIFY: Apply new filename pattern {instrument}_{pitch}_vel{velocity}_{uuid_first4}
  - DEPENDENCIES: MIDI separation → audio rendering → keyframe generation
  - VALIDATION: Verify audio files and keyframes created with Universal ID links

Task 12: IMPLEMENT Progress tracking and error recovery
  - IMPLEMENT: Real-time progress updates, circuit breaker error handling
  - FOLLOW pattern: tqdm progress bars, comprehensive logging
  - MODIFY: Track Universal ID completion status through all pipeline stages
  - DEPENDENCIES: ProgressTracker, CircuitBreaker classes from previous tasks
  - VALIDATION: Verify error recovery and progress reporting work correctly
```

### Implementation Patterns & Key Details

```python
# Universal ID filename transformation pattern
def transform_filename_with_uuid(self, original_filename: str, universal_id: str) -> str:
    """Transform filename to new pattern with Universal ID suffix"""
    # Example: "note_000_Flûte_A4_vel76.wav" → "Flûte_A4_vel76_2584.wav"

    parts = original_filename.split('_')
    if len(parts) >= 4:
        # Extract: instrument, pitch, velocity from existing pattern
        instrument = parts[2] if len(parts) > 2 else "Unknown"
        pitch_vel = '_'.join(parts[3:]).replace('.wav', '').replace('.json', '')
        uuid_suffix = universal_id[:4]  # First 4 chars of UUID
        extension = Path(original_filename).suffix

        return f"{instrument}_{pitch_vel}_{uuid_suffix}{extension}"
    return original_filename

# Atomic manifest update pattern
async def update_manifest_with_universal_id(self, universal_id: str, stage: str, file_path: str):
    """Update manifest atomically with Universal ID file tracking"""

    manifest_path = self.output_dir / f"{stage}_manifest.json"

    # Atomic read-modify-write
    with atomic_write(manifest_path, overwrite=True) as f:
        manifest = self.load_manifest(manifest_path)

        # Find Universal ID entry and update
        for entry in manifest.get('entries', []):
            if entry['universal_id'] == universal_id:
                entry['actual_filename'] = file_path
                entry['file_exists'] = os.path.exists(file_path)
                entry['updated_at'] = datetime.now().isoformat()
                break

        json.dump(manifest, f, indent=2)

# Circuit breaker subprocess execution pattern
def execute_subprocess_with_breaker(self, command: List[str], stage_name: str) -> subprocess.CompletedProcess:
    """Execute subprocess with circuit breaker protection"""

    @self.circuit_breaker.call
    def run_subprocess():
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=self.working_directory
        )

    try:
        result = run_subprocess()
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, command)
        return result
    except Exception as e:
        self.logger.error(f"Stage {stage_name} failed: {e}")
        raise

# Progress tracking with Universal ID granularity
async def track_stage_progress(self, stage: PipelineStage, universal_ids: List[str]):
    """Track progress at Universal ID level throughout stage execution"""

    with tqdm(total=len(universal_ids), desc=f"{stage.name}") as pbar:
        for universal_id in universal_ids:
            # Execute processing for this Universal ID
            await self.process_universal_id(stage, universal_id)

            # Update progress tracking
            self.progress_tracker.complete_universal_id(universal_id, stage.name)
            pbar.update(1)

            # Log completion with Universal ID
            self.logger.info(f"Universal ID {universal_id[:8]}: {stage.name} completed")
```

### Integration Points

```yaml
NOTE_COORDINATOR:
  - input_files: [musicxml_file, midi_file]
  - output_dir: "universal_output"
  - command: ["python", "note_coordinator.py", "{musicxml}", "{midi}", "{output_dir}"]
  - outputs: ["universal_notes_registry.json", "midi_pipeline_manifest.json", "svg_pipeline_manifest.json"]

TIED_NOTE_PROCESSOR:
  - input_files: [musicxml_file, "universal_output/coordination_metadata.json"]
  - depends_on: ["note_coordinator"]
  - command: ["python", "App/Synchronizer 19-26-28-342/utils/tied_note_processor.py", "{musicxml}", "{metadata}", "{matches}"]
  - outputs: ["tied_note_assignments.json", "ae_timing_data.json"]

SYMBOLIC_PIPELINE:
  - stage_1: ["python", "App/Symbolic Separators/truly_universal_noteheads_extractor.py", "{musicxml}"]
  - stage_2: ["python", "App/Symbolic Separators/truly_universal_noteheads_subtractor.py", "{musicxml}", "{svg}"]
  - stage_3: ["python", "App/Symbolic Separators/xml_based_instrument_separator.py", "{musicxml}", "{svg}", "instruments_output"]
  - stage_4: ["python", "App/Symbolic Separators/individual_noteheads_creator.py", "{musicxml}"]
  - stage_5: ["python", "App/Symbolic Separators/staff_barlines_extractor.py", "{musicxml}", "{svg}"]

AUDIO_PIPELINE:
  - stage_1: ["python", "App/Audio Separators/midi_note_separator.py", "{midi}"]
  - stage_2: ["python", "App/Audio Separators/midi_to_audio_renderer_fast.py", "{midi_dir}"]
  - stage_3: ["python", "App/Audio Separators/audio_to_keyframes_fast.py", "{audio_dir}"]
```

## Validation Loop

### Level 1: Syntax & Style (Immediate Feedback)

```bash
# Run after each file creation - fix before proceeding
ruff check orchestrator/ --fix              # Auto-format orchestrator package
mypy orchestrator/                          # Type checking
ruff format orchestrator/                   # Consistent formatting

# Main orchestrator script validation
ruff check universal_orchestrator.py --fix
mypy universal_orchestrator.py
ruff format universal_orchestrator.py

# Expected: Zero errors. If errors exist, READ output and fix before proceeding.
```

### Level 2: Unit Tests (Component Validation)

```bash
# Test orchestrator components individually
uv run pytest orchestrator/tests/test_pipeline_stage.py -v
uv run pytest orchestrator/tests/test_universal_registry.py -v
uv run pytest orchestrator/tests/test_manifest_manager.py -v
uv run pytest orchestrator/tests/test_progress_tracker.py -v

# Test main orchestrator logic
uv run pytest tests/test_universal_orchestrator.py -v

# Expected: All unit tests pass, components work in isolation
```

### Level 3: Integration Testing (System Validation)

```bash
# Test with sample MusicXML and MIDI files
python universal_orchestrator.py "PRPs-agentic-eng/Base/SS 9.musicxml" "PRPs-agentic-eng/Base/Saint-Saens Trio No 2.mid"

# Verify Note Coordinator integration
ls -la universal_output/
cat universal_output/universal_notes_registry.json | jq '.notes[0]'

# Verify Tied Note Processor integration
ls -la tied_note_enhanced_manifests/
cat tied_note_enhanced_manifests/tied_note_assignments.json | jq '.tied_note_assignments[0]'

# Verify Symbolic Pipeline integration
ls -la instruments_output/
ls -la individual_noteheads/

# Verify Audio Pipeline integration with new filename patterns
ls -la Audio/*/
find Audio/ -name "*_*.wav" | head -5   # Should show new {instrument}_{pitch}_vel{velocity}_{uuid} pattern

# Verify Universal ID preservation through pipeline
python -c "
import json
with open('universal_output/universal_notes_registry.json', 'r') as f:
    registry = json.load(f)
    print('Universal IDs found:', len(registry['notes']))
    print('First Universal ID:', registry['notes'][0]['universal_id'])
"

# Expected: All files created, Universal ID preserved, new filename patterns applied
```

### Level 4: Creative & Domain-Specific Validation

```bash
# Validate Universal ID integrity across entire pipeline
python -c "
import json, glob, os
from pathlib import Path

# Load registry
with open('universal_output/universal_notes_registry.json', 'r') as f:
    registry = json.load(f)

# Check each Universal ID has corresponding files
for note in registry['notes']:
    uid = note['universal_id'][:4]  # First 4 chars
    xml_data = note['xml_data']

    # Expected audio filename pattern
    expected_audio = f\"Audio/{xml_data['part_id']}/{xml_data['note_name']}_vel{note.get('midi_data', {}).get('velocity', 64)}_{uid}.wav\"
    expected_keyframes = expected_audio.replace('.wav', '_keyframes.json').replace('Audio/', 'Audio/Keyframes/')

    print(f'Universal ID {uid}:')
    print(f'  Audio: {\"✅\" if os.path.exists(expected_audio) else \"❌\"} {expected_audio}')
    print(f'  Keyframes: {\"✅\" if os.path.exists(expected_keyframes) else \"❌\"} {expected_keyframes}')
"

# Validate tied note processing worked correctly
python -c "
import json
if os.path.exists('tied_note_enhanced_manifests/tied_note_assignments.json'):
    with open('tied_note_enhanced_manifests/tied_note_assignments.json', 'r') as f:
        assignments = json.load(f)
    print('Tied note assignments found:', len(assignments.get('tied_note_assignments', [])))
    if assignments.get('tied_note_assignments'):
        print('Sample assignment:', assignments['tied_note_assignments'][0])
else:
    print('No tied notes detected in this score')
"

# Performance validation - check pipeline execution time
grep "Pipeline completed in" universal_orchestrator.log

# Error resilience validation - verify error recovery logs
grep -i "error\|retry\|circuit" universal_orchestrator.log

# Expected: Universal ID integrity maintained, tied notes processed, performance acceptable
```

## Final Validation Checklist

### Technical Validation

- [ ] All 4 validation levels completed successfully
- [ ] All tests pass: `uv run pytest orchestrator/ tests/ -v`
- [ ] No linting errors: `uv run ruff check orchestrator/ universal_orchestrator.py`
- [ ] No type errors: `uv run mypy orchestrator/ universal_orchestrator.py`
- [ ] No formatting issues: `uv run ruff format orchestrator/ universal_orchestrator.py --check`

### Feature Validation

- [ ] Note Coordinator integration: Universal ID manifests generated
- [ ] Tied Note Processor integration: Enhanced manifests with timing calculations
- [ ] Symbolic Pipeline coordination: Individual SVG files created with proper naming
- [ ] Audio Pipeline coordination: New filename pattern applied {instrument}_{pitch}_vel{velocity}_{uuid}
- [ ] Universal ID preservation: Files linkable through Universal ID throughout pipeline
- [ ] Progress tracking: Real-time progress with Universal ID-level granularity
- [ ] Error recovery: Circuit breaker prevents cascade failures, partial failures handled gracefully

### Code Quality Validation

- [ ] Follows existing codebase patterns (dataclass-driven config, subprocess management)
- [ ] File placement matches desired codebase tree structure
- [ ] Universal constants used consistently across coordinate transformations
- [ ] Atomic manifest updates prevent corruption during failures
- [ ] Working directory handling matches existing script patterns
- [ ] Filename transformations maintain Universal ID linkage

### Documentation & Deployment

- [ ] CLI interface matches Sib2Ae conventions: `python universal_orchestrator.py <musicxml> <midi> [options]`
- [ ] Progress logs are comprehensive but not verbose
- [ ] Error messages are actionable with specific Universal ID context
- [ ] Performance metrics logged for pipeline optimization

---

## Anti-Patterns to Avoid

- ❌ Don't modify existing pipeline scripts - use wrapper approach with manifest updates
- ❌ Don't pre-check for tied notes - tied_note_processor.py auto-detects
- ❌ Don't skip atomic manifest updates - corruption will break Universal ID integrity
- ❌ Don't use synchronous subprocess calls for long-running processes - implement async patterns
- ❌ Don't ignore Universal ID preservation in filename transformations
- ❌ Don't hardcode file paths - use configurable Path objects
- ❌ Don't catch all exceptions - be specific about subprocess vs. file operation failures

---

**Confidence Score: 9/10** - This PRP provides comprehensive codebase analysis, proven orchestration patterns, atomic operation safety, and detailed implementation guidance for successful one-pass implementation of the Universal ID pipeline orchestrator.