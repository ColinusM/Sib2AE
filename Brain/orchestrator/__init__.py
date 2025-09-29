#!/usr/bin/env python3
"""
Orchestrator Package - Universal ID Pipeline Orchestration

This package provides comprehensive orchestration for the Sib2Ae pipeline,
maintaining Universal ID integrity throughout all processing stages.

Key Components:
- PipelineStage: Stage coordination and dependency management
- UniversalFileRegistry: Universal ID tracking across all pipeline files
- AtomicManifestManager: Safe manifest updates with atomic operations
- ProgressTracker: Real-time progress reporting with Universal ID granularity
- ErrorHandlers: Circuit breaker pattern and retry mechanisms
"""

from .pipeline_stage import (
    PipelineStage, OrchestrationConfig, ExecutionMode,
    create_note_coordinator_stage, create_tied_note_processor_stage,
    create_symbolic_pipeline_stages, create_audio_pipeline_stages
)
from .universal_registry import UniversalFileRegistry
from .manifest_manager import AtomicManifestManager, create_manifest_manager
from .progress_tracker import ProgressTracker
from .error_handlers import CircuitBreaker, ProcessFailureHandler, create_process_failure_handler
from .registry_utils import (
    UniversalIDRegistry, UniversalIDMatch,
    create_registry_for_script, get_universal_id_with_fallback
)

__version__ = "1.0.0"

__all__ = [
    "PipelineStage",
    "OrchestrationConfig",
    "ExecutionMode",
    "UniversalFileRegistry",
    "AtomicManifestManager",
    "ProgressTracker",
    "CircuitBreaker",
    "ProcessFailureHandler",
    "UniversalIDRegistry",
    "UniversalIDMatch",
    "create_note_coordinator_stage",
    "create_tied_note_processor_stage",
    "create_symbolic_pipeline_stages",
    "create_audio_pipeline_stages",
    "create_manifest_manager",
    "create_process_failure_handler",
    "create_registry_for_script",
    "get_universal_id_with_fallback",
]
