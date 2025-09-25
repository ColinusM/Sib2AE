#!/usr/bin/env python3
"""
Pipeline Stage Coordination - Core data structures for orchestration

This module provides the foundational data structures for coordinating
pipeline execution with Universal ID tracking and dependency management.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Set, Callable
from datetime import datetime
from enum import Enum


class StageStatus(Enum):
    """Pipeline stage execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionMode(Enum):
    """Pipeline execution mode"""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


@dataclass
class PipelineStage:
    """
    Represents a single pipeline execution stage with Universal ID tracking.

    Based on patterns from synchronization_coordinator.py but enhanced for
    Universal ID preservation and atomic manifest updates.
    """

    name: str  # Stage identifier (e.g., "note_coordinator")
    description: str  # Human-readable description
    command: List[str]  # Command to execute
    input_files: List[Path]  # Required input files
    output_files: List[Path]  # Expected output files
    depends_on: List[str] = field(default_factory=list)  # Stage dependencies

    # Universal ID tracking
    universal_ids_processed: List[str] = field(
        default_factory=list
    )  # Track which Universal IDs completed
    universal_ids_expected: Set[str] = field(
        default_factory=set
    )  # Expected Universal IDs for this stage

    # Execution tracking
    status: StageStatus = StageStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    actual_duration_seconds: float = 0.0
    estimated_duration_seconds: float = 0.0

    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Progress tracking
    progress_percentage: float = 0.0
    current_operation: str = ""

    # Manifest tracking
    manifests_updated: List[str] = field(
        default_factory=list
    )  # Track which manifests were updated
    files_created: Dict[str, str] = field(
        default_factory=dict
    )  # Map Universal ID to actual filename

    def is_ready_to_run(self, completed_stages: Set[str]) -> bool:
        """Check if all dependencies are satisfied"""
        return all(dep in completed_stages for dep in self.depends_on)

    def mark_universal_id_completed(self, universal_id: str, actual_filename: str = ""):
        """Mark a Universal ID as completed for this stage"""
        if universal_id not in self.universal_ids_processed:
            self.universal_ids_processed.append(universal_id)

        if actual_filename:
            self.files_created[universal_id] = actual_filename

        # Update progress percentage
        if self.universal_ids_expected:
            completed_count = len(self.universal_ids_processed)
            total_count = len(self.universal_ids_expected)
            self.progress_percentage = min(
                100.0, (completed_count / total_count) * 100.0
            )

    def get_completion_rate(self) -> float:
        """Get completion rate as fraction (0.0 to 1.0)"""
        if not self.universal_ids_expected:
            return 1.0 if self.status == StageStatus.COMPLETED else 0.0

        completed = len(self.universal_ids_processed)
        expected = len(self.universal_ids_expected)
        return min(1.0, completed / expected)

    def start_execution(self):
        """Mark stage as started"""
        self.status = StageStatus.RUNNING
        self.start_time = datetime.now()
        self.current_operation = f"Executing {self.name}"

    def complete_successfully(self):
        """Mark stage as completed successfully"""
        self.status = StageStatus.COMPLETED
        self.end_time = datetime.now()
        if self.start_time:
            self.actual_duration_seconds = (
                self.end_time - self.start_time
            ).total_seconds()
        self.progress_percentage = 100.0
        self.current_operation = "Completed"

    def fail_with_error(self, error_message: str):
        """Mark stage as failed with error"""
        self.status = StageStatus.FAILED
        self.end_time = datetime.now()
        if self.start_time:
            self.actual_duration_seconds = (
                self.end_time - self.start_time
            ).total_seconds()
        self.error_message = error_message
        self.current_operation = f"Failed: {error_message}"

    def can_retry(self) -> bool:
        """Check if stage can be retried"""
        return self.retry_count < self.max_retries and self.status == StageStatus.FAILED

    def prepare_retry(self):
        """Prepare stage for retry"""
        if self.can_retry():
            self.retry_count += 1
            self.status = StageStatus.PENDING
            self.error_message = None
            self.progress_percentage = 0.0
            self.current_operation = f"Retry {self.retry_count}/{self.max_retries}"


@dataclass
class OrchestrationConfig:
    """
    Configuration for pipeline orchestration with Universal ID preservation.

    Based on patterns from synchronization_coordinator.py but extended for
    Universal ID tracking and enhanced error handling.
    """

    # Input files
    musicxml_file: Path
    midi_file: Path
    svg_file: Optional[Path] = None  # SVG file for symbolic processing
    output_dir: Path = Path("universal_output")

    # Execution configuration
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    max_workers: int = 4  # For parallel processing
    enable_circuit_breaker: bool = True  # Error resilience

    # Universal ID configuration
    preserve_universal_ids: bool = True  # Maintain Universal ID through filenames
    apply_new_filename_pattern: bool = (
        True  # Use {instrument}_{pitch}_vel{velocity}_{uuid} pattern
    )

    # Progress and logging
    verbose: bool = True  # Detailed logging
    progress_callback: Optional[Callable] = None  # Real-time progress updates
    log_file: Optional[Path] = None  # Log file path

    # Performance and reliability
    stage_timeout_seconds: float = 600.0  # 10 minute timeout per stage
    enable_performance_tracking: bool = True
    backup_existing_outputs: bool = True

    # Pipeline customization
    skip_tied_note_processing: bool = False  # Always run tied note processor by default
    audio_renderer_mode: str = "fast"  # "fast" or "standard"
    keyframe_generator_mode: str = "fast"  # "fast" or "standard"

    # Error handling configuration
    max_stage_retries: int = 3  # Maximum retries per stage
    continue_on_non_critical_failure: bool = (
        True  # Continue pipeline if non-critical stages fail
    )

    # Manifest management
    atomic_manifest_updates: bool = True  # Use atomic operations for manifest updates
    manifest_backup_enabled: bool = True  # Backup manifests before updates

    # Validation configuration
    validate_universal_id_integrity: bool = True  # Verify Universal ID preservation
    validate_file_dependencies: bool = True  # Check input/output file dependencies

    def get_audio_renderer_script(self) -> str:
        """Get the appropriate audio renderer script name"""
        if self.audio_renderer_mode == "fast":
            return "midi_to_audio_renderer_fast.py"
        else:
            return "midi_to_audio_renderer.py"

    def get_keyframe_generator_script(self) -> str:
        """Get the appropriate keyframe generator script name"""
        if self.keyframe_generator_mode == "fast":
            return "audio_to_keyframes_fast.py"
        else:
            return "audio_to_keyframes.py"

    def get_working_directory(self) -> Path:
        """Get the working directory for pipeline execution"""
        # All commands must run from project root per CLAUDE.md
        return Path("/Users/colinmignot/Claude Code/Sib2Ae/")

    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []

        # Validate required input files
        if not self.musicxml_file.exists():
            issues.append(f"MusicXML file not found: {self.musicxml_file}")

        if not self.midi_file.exists():
            issues.append(f"MIDI file not found: {self.midi_file}")

        if self.svg_file and not self.svg_file.exists():
            issues.append(f"SVG file not found: {self.svg_file}")

        # Validate configuration values
        if self.max_workers < 1:
            issues.append("max_workers must be at least 1")

        if self.stage_timeout_seconds <= 0:
            issues.append("stage_timeout_seconds must be positive")

        if self.max_stage_retries < 0:
            issues.append("max_stage_retries must be non-negative")

        # Validate execution mode
        if self.execution_mode not in ExecutionMode:
            issues.append(f"Invalid execution mode: {self.execution_mode}")

        # Validate audio/keyframe modes
        valid_audio_modes = ["fast", "standard"]
        if self.audio_renderer_mode not in valid_audio_modes:
            issues.append(f"Invalid audio_renderer_mode: {self.audio_renderer_mode}")

        if self.keyframe_generator_mode not in valid_audio_modes:
            issues.append(
                f"Invalid keyframe_generator_mode: {self.keyframe_generator_mode}"
            )

        return issues

    def create_output_directory(self):
        """Create output directory if it doesn't exist"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for different pipeline outputs
        (self.output_dir / "manifests").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        (self.output_dir / "backups").mkdir(exist_ok=True)


# Factory functions for creating common pipeline stages


def create_note_coordinator_stage(config: OrchestrationConfig) -> PipelineStage:
    """Create Note Coordinator pipeline stage"""
    return PipelineStage(
        name="note_coordinator",
        description="Generate Universal ID registry and manifests",
        command=[
            "python",
            "PRPs-agentic-eng/note_coordinator.py",
            str(config.musicxml_file),
            str(config.midi_file),
            str(config.output_dir),
        ],
        input_files=[config.musicxml_file, config.midi_file],
        output_files=[
            config.output_dir / "universal_notes_registry.json",
            config.output_dir / "midi_pipeline_manifest.json",
            config.output_dir / "svg_pipeline_manifest.json",
            config.output_dir / "coordination_metadata.json",
        ],
        depends_on=[],
        estimated_duration_seconds=15.0,
    )


def create_tied_note_processor_stage(config: OrchestrationConfig) -> PipelineStage:
    """Create Tied Note Processor pipeline stage"""
    return PipelineStage(
        name="tied_note_processor",
        description="Process tied note relationships with timing calculations",
        command=[
            "python",
            "PRPs-agentic-eng/App/Synchronizer 19-26-28-342/utils/tied_note_processor.py",
            str(config.musicxml_file),
            str(config.output_dir / "coordination_metadata.json"),
            str(config.output_dir / "universal_notes_registry.json"),
        ],
        input_files=[
            config.musicxml_file,
            config.output_dir / "coordination_metadata.json",
            config.output_dir / "universal_notes_registry.json",
        ],
        output_files=[
            config.output_dir / "tied_note_assignments.json",
            config.output_dir / "ae_timing_data.json",
        ],
        depends_on=["note_coordinator"],
        estimated_duration_seconds=10.0,
    )


def create_symbolic_pipeline_stages(config: OrchestrationConfig) -> List[PipelineStage]:
    """Create all symbolic pipeline stages"""
    stages = []

    # Stage 1: Noteheads Extraction
    stages.append(
        PipelineStage(
            name="noteheads_extraction",
            description="Extract noteheads from MusicXML with pixel-perfect coordinates",
            command=[
                "python",
                "PRPs-agentic-eng/App/Symbolic Separators/truly_universal_noteheads_extractor.py",
                str(config.musicxml_file),
            ],
            input_files=[config.musicxml_file],
            output_files=[Path(f"{config.musicxml_file.stem}_noteheads_universal.svg")],
            depends_on=["tied_note_processor"]
            if not config.skip_tied_note_processing
            else ["note_coordinator"],
            estimated_duration_seconds=10.0,
        )
    )

    # Stage 2: Noteheads Subtraction
    if config.svg_file:
        stages.append(
            PipelineStage(
                name="noteheads_subtraction",
                description="Remove noteheads from full SVG while preserving other elements",
                command=[
                    "python",
                    "PRPs-agentic-eng/App/Symbolic Separators/truly_universal_noteheads_subtractor.py",
                    str(config.musicxml_file),
                    str(config.svg_file),
                ],
                input_files=[config.musicxml_file, config.svg_file],
                output_files=[Path(f"{config.svg_file.stem}_without_noteheads.svg")],
                depends_on=["noteheads_extraction"],
                estimated_duration_seconds=8.0,
            )
        )

    # Stage 3: Instrument Separation
    stages.append(
        PipelineStage(
            name="instrument_separation",
            description="Create individual SVG files per instrument",
            command=[
                "python",
                "PRPs-agentic-eng/App/Symbolic Separators/xml_based_instrument_separator.py",
                str(config.musicxml_file),
                str(config.svg_file or ""),
                "instruments_output",
            ],
            input_files=[config.musicxml_file]
            + ([config.svg_file] if config.svg_file else []),
            output_files=[Path("instruments_output")],
            depends_on=["noteheads_extraction"],
            estimated_duration_seconds=12.0,
        )
    )

    # Stage 4: Individual Noteheads Creation
    stages.append(
        PipelineStage(
            name="individual_noteheads_creation",
            description="Create one SVG file per notehead for After Effects animation",
            command=[
                "python",
                "PRPs-agentic-eng/App/Symbolic Separators/individual_noteheads_creator.py",
                str(config.musicxml_file),
            ],
            input_files=[config.musicxml_file],
            output_files=[Path("individual_noteheads")],
            depends_on=["instrument_separation"],
            estimated_duration_seconds=15.0,
        )
    )

    # Stage 5: Staff and Barlines Extraction
    if config.svg_file:
        stages.append(
            PipelineStage(
                name="staff_barlines_extraction",
                description="Extract staff lines and barlines for background elements",
                command=[
                    "python",
                    "PRPs-agentic-eng/App/Symbolic Separators/staff_barlines_extractor.py",
                    str(config.musicxml_file),
                    str(config.svg_file),
                ],
                input_files=[config.musicxml_file, config.svg_file],
                output_files=[Path(f"{config.svg_file.stem}_staff_barlines.svg")],
                depends_on=["individual_noteheads_creation"],
                estimated_duration_seconds=5.0,
            )
        )

    return stages


def create_audio_pipeline_stages(config: OrchestrationConfig) -> List[PipelineStage]:
    """Create all audio pipeline stages"""
    stages = []

    # Stage 1: MIDI Note Separation
    midi_notes_dir = Path(f"{config.midi_file.stem}_individual_notes")
    stages.append(
        PipelineStage(
            name="midi_note_separation",
            description="Split MIDI into individual note files (foundation)",
            command=[
                "python",
                "PRPs-agentic-eng/App/Audio Separators/midi_note_separator.py",
                str(config.midi_file),
            ],
            input_files=[config.midi_file],
            output_files=[midi_notes_dir],
            depends_on=["tied_note_processor"]
            if not config.skip_tied_note_processing
            else ["note_coordinator"],
            estimated_duration_seconds=15.0,
        )
    )

    # Stage 2: MIDI to Audio Rendering
    stages.append(
        PipelineStage(
            name="midi_to_audio_rendering",
            description=f"Convert MIDI notes to audio files ({config.audio_renderer_mode} mode)",
            command=[
                "python",
                f"PRPs-agentic-eng/App/Audio Separators/{config.get_audio_renderer_script()}",
                str(midi_notes_dir),
            ],
            input_files=[midi_notes_dir],
            output_files=[Path("Audio")],
            depends_on=["midi_note_separation"],
            estimated_duration_seconds=45.0
            if config.audio_renderer_mode == "fast"
            else 90.0,
        )
    )

    # Stage 3: Audio to Keyframes
    stages.append(
        PipelineStage(
            name="audio_to_keyframes",
            description=f"Generate After Effects keyframe data ({config.keyframe_generator_mode} mode)",
            command=[
                "python",
                f"PRPs-agentic-eng/App/Audio Separators/{config.get_keyframe_generator_script()}",
                "Audio",
            ],
            input_files=[Path("Audio")],
            output_files=[Path("Audio/Keyframes")],
            depends_on=["midi_to_audio_rendering"],
            estimated_duration_seconds=20.0
            if config.keyframe_generator_mode == "fast"
            else 40.0,
        )
    )

    return stages
