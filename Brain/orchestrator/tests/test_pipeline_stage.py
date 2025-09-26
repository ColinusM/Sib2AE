#!/usr/bin/env python3
"""
Basic smoke tests for pipeline_stage module
"""

import pytest
from pathlib import Path
from typing import List

from orchestrator.pipeline_stage import (
    StageStatus,
    PipelineStage,
    OrchestrationConfig,
    create_note_coordinator_stage,
    create_tied_note_processor_stage,
    create_symbolic_pipeline_stages,
    create_audio_pipeline_stages
)


def test_stage_status_enum():
    """Test StageStatus enum values"""
    assert StageStatus.PENDING.value == "pending"
    assert StageStatus.RUNNING.value == "running"
    assert StageStatus.COMPLETED.value == "completed"
    assert StageStatus.FAILED.value == "failed"


def test_pipeline_stage_creation():
    """Test PipelineStage dataclass creation"""
    stage = PipelineStage(
        name="test_stage",
        description="Test stage",
        command=["echo", "test"],
        input_files=[Path("input.txt")],
        output_files=[Path("output.txt")]
    )

    assert stage.name == "test_stage"
    assert stage.description == "Test stage"
    assert stage.command == ["echo", "test"]
    assert len(stage.input_files) == 1
    assert len(stage.output_files) == 1
    assert stage.status == StageStatus.PENDING
    assert len(stage.depends_on) == 0
    assert len(stage.universal_ids_processed) == 0


def test_orchestration_config_creation():
    """Test OrchestrationConfig dataclass creation"""
    config = OrchestrationConfig(
        musicxml_file=Path("test.musicxml"),
        midi_file=Path("test.mid"),
        svg_file=Path("test.svg"),
        output_dir=Path("output")
    )

    assert config.musicxml_file == Path("test.musicxml")
    assert config.midi_file == Path("test.mid")
    assert config.svg_file == Path("test.svg")
    assert config.output_dir == Path("output")
    # Test default values that actually exist based on error message
    assert hasattr(config, 'execution_mode')
    assert hasattr(config, 'max_workers')
    assert hasattr(config, 'enable_circuit_breaker')
    assert hasattr(config, 'preserve_universal_ids')
    assert config.max_workers == 4
    assert config.verbose == True


def test_create_note_coordinator_stage():
    """Test note coordinator stage factory function"""
    config = OrchestrationConfig(
        musicxml_file=Path("test.musicxml"),
        midi_file=Path("test.mid"),
        svg_file=Path("test.svg"),
        output_dir=Path("output")
    )

    stage = create_note_coordinator_stage(config)

    assert stage.name == "note_coordinator"
    assert "Universal ID" in stage.description
    assert len(stage.command) > 0
    assert "note_coordinator.py" in stage.command[1]
    assert len(stage.input_files) == 2  # musicxml and midi files
    assert len(stage.output_files) >= 1


def test_create_tied_note_processor_stage():
    """Test tied note processor stage factory function"""
    config = OrchestrationConfig(
        musicxml_file=Path("test.musicxml"),
        midi_file=Path("test.mid"),
        svg_file=Path("test.svg"),
        output_dir=Path("output")
    )

    stage = create_tied_note_processor_stage(config)

    assert stage.name == "tied_note_processor"
    assert "tied note" in stage.description
    assert len(stage.command) > 0
    assert "tied_note_processor.py" in stage.command[1]
    assert stage.depends_on == ["note_coordinator"]


def test_create_symbolic_pipeline_stages():
    """Test symbolic pipeline stages factory function"""
    config = OrchestrationConfig(
        musicxml_file=Path("test.musicxml"),
        midi_file=Path("test.mid"),
        svg_file=Path("test.svg"),
        output_dir=Path("output")
    )

    stages = create_symbolic_pipeline_stages(config)

    assert isinstance(stages, list)
    assert len(stages) >= 5  # Should have at least 5 symbolic pipeline stages

    stage_names = [stage.name for stage in stages]
    expected_stages = [
        "noteheads_extraction",
        "noteheads_subtraction",
        "instrument_separation",
        "individual_noteheads_creation",
        "staff_barlines_extraction"
    ]

    for expected_stage in expected_stages:
        assert expected_stage in stage_names


def test_create_audio_pipeline_stages():
    """Test audio pipeline stages factory function"""
    config = OrchestrationConfig(
        musicxml_file=Path("test.musicxml"),
        midi_file=Path("test.mid"),
        svg_file=Path("test.svg"),
        output_dir=Path("output")
    )

    stages = create_audio_pipeline_stages(config)

    assert isinstance(stages, list)
    assert len(stages) >= 3  # Should have at least 3 audio pipeline stages

    stage_names = [stage.name for stage in stages]
    expected_stages = [
        "midi_note_separation",
        "midi_to_audio_rendering",
        "audio_to_keyframes"
    ]

    for expected_stage in expected_stages:
        assert expected_stage in stage_names