#!/usr/bin/env python3
"""
Universal File Registry - Universal ID tracking throughout pipeline

This module provides comprehensive Universal ID tracking across all pipeline
stages, maintaining file relationships and filename transformations while
preserving Universal ID integrity.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# Import UniversalNote from note_coordinator for compatibility
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


@dataclass
class FileRegistration:
    """Registration record for a file associated with a Universal ID"""

    universal_id: str
    stage_name: str  # Which stage created this file
    original_filename: str  # Original filename pattern
    actual_filename: str  # Actual filename with Universal ID
    file_path: Path  # Full path to the file
    file_exists: bool  # Whether file actually exists
    file_size: int  # File size in bytes
    created_at: datetime  # When this registration was created
    updated_at: datetime  # When this registration was last updated
    metadata: Dict[str, Any]  # Additional metadata for this file


@dataclass
class UniversalIDRecord:
    """Complete record for a Universal ID across all pipeline stages"""

    universal_id: str
    xml_data: Dict[str, Any]  # XML note data
    midi_data: Optional[Dict[str, Any]]  # MIDI note data (if matched)
    svg_data: Dict[str, Any]  # SVG coordinate data
    match_confidence: float  # Confidence in XML-MIDI matching

    # File registrations by stage
    file_registrations: Dict[str, FileRegistration]  # stage_name -> FileRegistration

    # Timing and coordination data
    timing_data: Dict[str, Any]  # Timing calculations from tied note processor
    after_effects_data: Dict[str, Any]  # AE-specific data

    # Status tracking
    pipeline_stages_completed: Set[str]  # Which stages have processed this Universal ID
    last_updated: datetime  # When this record was last updated

    def __post_init__(self):
        """Initialize collections if not provided"""
        if not hasattr(self, "file_registrations") or self.file_registrations is None:
            self.file_registrations = {}
        if (
            not hasattr(self, "pipeline_stages_completed")
            or self.pipeline_stages_completed is None
        ):
            self.pipeline_stages_completed = set()
        if not hasattr(self, "last_updated") or self.last_updated is None:
            self.last_updated = datetime.now()


class UniversalFileRegistry:
    """
    Registry for tracking Universal ID file relationships throughout pipeline.

    Based on patterns from note_coordinator.py but enhanced for comprehensive
    file tracking, filename transformations, and pipeline coordination.
    """

    def __init__(self, registry_file: Optional[Path] = None):
        """
        Initialize Universal File Registry.

        Args:
            registry_file: Path to save/load registry data (optional)
        """
        self.registry_file = registry_file or Path(
            "universal_output/universal_file_registry.json"
        )
        self.universal_records: Dict[str, UniversalIDRecord] = {}
        self.stage_file_mappings: Dict[
            str, Dict[str, List[str]]
        ] = {}  # stage -> pattern -> [universal_ids]
        self.filename_transformations: Dict[str, str] = {}  # original -> transformed

        # Load existing registry if available
        if self.registry_file.exists():
            self.load_registry()

    def initialize_from_note_coordinator(
        self,
        universal_notes_registry_path: Path,
        midi_manifest_path: Path,
        svg_manifest_path: Path,
    ):
        """
        Initialize registry from Note Coordinator output files.

        Args:
            universal_notes_registry_path: Path to universal_notes_registry.json
            midi_manifest_path: Path to midi_pipeline_manifest.json
            svg_manifest_path: Path to svg_pipeline_manifest.json
        """
        print("🌍 Initializing Universal File Registry from Note Coordinator outputs")

        # Load universal notes registry
        if universal_notes_registry_path.exists():
            with open(universal_notes_registry_path, "r") as f:
                universal_data = json.load(f)

            # Create UniversalIDRecord for each note
            for note_data in universal_data.get("notes", []):
                universal_id = note_data["universal_id"]

                # Extract data components
                xml_data = note_data.get("xml_data", {})
                midi_data = note_data.get("midi_data")
                svg_data = note_data.get("svg_data", {})
                match_confidence = note_data.get("match_confidence", 0.0)

                # Create record
                record = UniversalIDRecord(
                    universal_id=universal_id,
                    xml_data=xml_data,
                    midi_data=midi_data,
                    svg_data=svg_data,
                    match_confidence=match_confidence,
                    file_registrations={},
                    timing_data={},
                    after_effects_data={},
                    pipeline_stages_completed={"note_coordinator"},
                    last_updated=datetime.now(),
                )

                self.universal_records[universal_id] = record

            print(f"   ✅ Loaded {len(self.universal_records)} Universal ID records")

        # Load and integrate MIDI manifest
        if midi_manifest_path.exists():
            self._integrate_midi_manifest(midi_manifest_path)

        # Load and integrate SVG manifest
        if svg_manifest_path.exists():
            self._integrate_svg_manifest(svg_manifest_path)

        # Mark note coordinator stage as completed for all records
        self._mark_stage_completed("note_coordinator")

        print(
            f"   🎯 Universal File Registry initialized with {len(self.universal_records)} Universal IDs"
        )

    def _integrate_midi_manifest(self, midi_manifest_path: Path):
        """Integrate MIDI pipeline manifest into registry"""
        print(f"   🎵 Integrating MIDI manifest: {midi_manifest_path}")

        with open(midi_manifest_path, "r") as f:
            midi_manifest = json.load(f)

        for entry in midi_manifest:
            universal_id = entry.get("universal_id")
            if universal_id in self.universal_records:
                record = self.universal_records[universal_id]

                # Store original filename patterns for transformation
                original_audio = entry.get("audio_filename", "")
                original_keyframes = entry.get("keyframes_filename", "")

                # Add to filename transformations mapping
                if original_audio:
                    self.filename_transformations[original_audio] = (
                        ""  # Will be filled later
                    )
                if original_keyframes:
                    self.filename_transformations[original_keyframes] = (
                        ""  # Will be filled later
                    )

                # Store timing data
                record.timing_data.update(entry.get("timing_data", {}))

        print(f"      📊 Integrated MIDI manifest with {len(midi_manifest)} entries")

    def _integrate_svg_manifest(self, svg_manifest_path: Path):
        """Integrate SVG pipeline manifest into registry"""
        print(f"   🖼️  Integrating SVG manifest: {svg_manifest_path}")

        with open(svg_manifest_path, "r") as f:
            svg_manifest = json.load(f)

        for entry in svg_manifest:
            universal_id = entry.get("universal_id")
            if universal_id in self.universal_records:
                record = self.universal_records[universal_id]

                # Store expected SVG filename
                svg_filename = entry.get("svg_filename", "")
                if svg_filename:
                    self.filename_transformations[svg_filename] = (
                        ""  # Will be filled later
                    )

                # Update coordinates and visual data
                record.svg_data.update(entry.get("coordinates", {}))
                record.svg_data.update(entry.get("visual_data", {}))

        print(f"      📊 Integrated SVG manifest with {len(svg_manifest)} entries")

    def register_file_creation(
        self,
        universal_id: str,
        stage_name: str,
        original_filename: str,
        actual_file_path: Path,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Register a file creation for a Universal ID.

        Args:
            universal_id: The Universal ID this file belongs to
            stage_name: Name of the pipeline stage that created this file
            original_filename: Original filename pattern
            actual_file_path: Actual path to the created file
            metadata: Additional metadata about the file

        Returns:
            True if registration successful, False otherwise
        """
        if universal_id not in self.universal_records:
            print(f"⚠️  Warning: Universal ID {universal_id} not found in registry")
            return False

        record = self.universal_records[universal_id]

        # Create file registration
        file_registration = FileRegistration(
            universal_id=universal_id,
            stage_name=stage_name,
            original_filename=original_filename,
            actual_filename=actual_file_path.name,
            file_path=actual_file_path,
            file_exists=actual_file_path.exists(),
            file_size=actual_file_path.stat().st_size
            if actual_file_path.exists()
            else 0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata or {},
        )

        # Register file with the Universal ID record
        record.file_registrations[stage_name] = file_registration
        record.pipeline_stages_completed.add(stage_name)
        record.last_updated = datetime.now()

        # Update filename transformation mapping
        self.filename_transformations[original_filename] = str(actual_file_path)

        # Update stage mappings
        if stage_name not in self.stage_file_mappings:
            self.stage_file_mappings[stage_name] = {}

        pattern = self._extract_filename_pattern(original_filename)
        if pattern not in self.stage_file_mappings[stage_name]:
            self.stage_file_mappings[stage_name][pattern] = []

        if universal_id not in self.stage_file_mappings[stage_name][pattern]:
            self.stage_file_mappings[stage_name][pattern].append(universal_id)

        return True

    def transform_filename_with_uuid(
        self, original_filename: str, universal_id: str
    ) -> str:
        """
        Transform filename to new pattern with Universal ID suffix.

        Implements the filename transformation pattern specified in the PRP:
        "note_000_Flûte_A4_vel76.wav" → "Flûte_A4_vel76_2584.wav"

        Args:
            original_filename: Original filename
            universal_id: Universal ID to incorporate

        Returns:
            Transformed filename with Universal ID
        """
        if not original_filename:
            return ""

        # Get record for this Universal ID
        if universal_id not in self.universal_records:
            return original_filename

        record = self.universal_records[universal_id]
        xml_data = record.xml_data

        # Extract components from filename
        parts = original_filename.split("_")
        extension = Path(original_filename).suffix

        # Handle different filename patterns
        if len(parts) >= 4 and parts[0] == "note":
            # Standard pattern: "note_000_Flûte_A4_vel76.wav"
            if len(parts) >= 3:
                # Extract instrument (part 2), pitch_velocity (parts 3+)
                instrument = (
                    parts[2] if len(parts) > 2 else xml_data.get("part_id", "Unknown")
                )
                pitch_vel = "_".join(parts[3:])

                # Remove extension from pitch_vel
                pitch_vel = pitch_vel.replace(extension, "")

                # Get first 4 characters of UUID
                uuid_suffix = universal_id[:4]

                # Create new filename
                return f"{instrument}_{pitch_vel}_{uuid_suffix}{extension}"

        # If pattern doesn't match expected format, append UUID
        base_name = original_filename.replace(extension, "")
        uuid_suffix = universal_id[:4]
        return f"{base_name}_{uuid_suffix}{extension}"

    def _extract_filename_pattern(self, filename: str) -> str:
        """Extract filename pattern for categorization"""
        # Remove numbers and UUIDs to get general pattern
        import re

        pattern = re.sub(r"\d+", "N", filename)
        pattern = re.sub(r"[a-f0-9]{4,}", "UUID", pattern)
        return pattern

    def get_universal_id_files(self, universal_id: str) -> Dict[str, FileRegistration]:
        """Get all file registrations for a Universal ID"""
        if universal_id not in self.universal_records:
            return {}

        return self.universal_records[universal_id].file_registrations

    def get_stage_universal_ids(self, stage_name: str) -> List[str]:
        """Get all Universal IDs that have been processed by a stage"""
        return [
            uid
            for uid, record in self.universal_records.items()
            if stage_name in record.pipeline_stages_completed
        ]

    def get_pending_universal_ids(self, stage_name: str) -> List[str]:
        """Get Universal IDs that haven't been processed by a stage yet"""
        return [
            uid
            for uid, record in self.universal_records.items()
            if stage_name not in record.pipeline_stages_completed
        ]

    def _mark_stage_completed(
        self, stage_name: str, universal_ids: Optional[List[str]] = None
    ):
        """Mark a stage as completed for specified Universal IDs (or all)"""
        target_ids = universal_ids or list(self.universal_records.keys())

        for universal_id in target_ids:
            if universal_id in self.universal_records:
                self.universal_records[universal_id].pipeline_stages_completed.add(
                    stage_name
                )
                self.universal_records[universal_id].last_updated = datetime.now()

    def update_timing_data(self, universal_id: str, timing_data: Dict[str, Any]):
        """Update timing data for a Universal ID"""
        if universal_id in self.universal_records:
            self.universal_records[universal_id].timing_data.update(timing_data)
            self.universal_records[universal_id].last_updated = datetime.now()

    def update_after_effects_data(self, universal_id: str, ae_data: Dict[str, Any]):
        """Update After Effects data for a Universal ID"""
        if universal_id in self.universal_records:
            self.universal_records[universal_id].after_effects_data.update(ae_data)
            self.universal_records[universal_id].last_updated = datetime.now()

    def validate_universal_id_integrity(self) -> Dict[str, List[str]]:
        """
        Validate Universal ID integrity across all registered files.

        Returns:
            Dictionary of validation issues by category
        """
        issues: Dict[str, List[str]] = {
            "missing_files": [],
            "orphaned_files": [],
            "filename_mismatches": [],
            "incomplete_stages": [],
        }

        for universal_id, record in self.universal_records.items():
            # Check for missing files
            for stage_name, file_reg in record.file_registrations.items():
                if not file_reg.file_exists:
                    issues["missing_files"].append(
                        f"Universal ID {universal_id[:8]}: {file_reg.actual_filename} (stage: {stage_name})"
                    )

                # Check filename transformation consistency
                expected_transformed = self.transform_filename_with_uuid(
                    file_reg.original_filename, universal_id
                )
                if file_reg.actual_filename != expected_transformed:
                    issues["filename_mismatches"].append(
                        f"Universal ID {universal_id[:8]}: expected {expected_transformed}, got {file_reg.actual_filename}"
                    )

            # Check for incomplete pipeline stages
            expected_stages = {
                "note_coordinator",
                "tied_note_processor",
                "midi_note_separation",
                "audio_rendering",
            }
            missing_stages = expected_stages - record.pipeline_stages_completed
            if missing_stages:
                issues["incomplete_stages"].append(
                    f"Universal ID {universal_id[:8]}: missing stages {missing_stages}"
                )

        return issues

    def get_registry_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the registry"""
        total_records = len(self.universal_records)

        # Count registrations by stage
        stage_counts: Dict[str, int] = {}
        for record in self.universal_records.values():
            for stage in record.pipeline_stages_completed:
                stage_counts[stage] = stage_counts.get(stage, 0) + 1

        # Count files by stage
        file_counts: Dict[str, int] = {}
        total_files = 0
        for record in self.universal_records.values():
            for stage_name, file_reg in record.file_registrations.items():
                file_counts[stage_name] = file_counts.get(stage_name, 0) + 1
                total_files += 1

        # Calculate match statistics
        matched_count = sum(
            1 for r in self.universal_records.values() if r.midi_data is not None
        )
        avg_confidence = (
            sum(r.match_confidence for r in self.universal_records.values())
            / total_records
            if total_records > 0
            else 0
        )

        return {
            "total_universal_ids": total_records,
            "matched_to_midi": matched_count,
            "match_rate": matched_count / total_records if total_records > 0 else 0,
            "average_confidence": avg_confidence,
            "total_files_registered": total_files,
            "stage_completion_counts": stage_counts,
            "file_counts_by_stage": file_counts,
            "filename_transformations": len(self.filename_transformations),
            "last_updated": max(
                (r.last_updated for r in self.universal_records.values()),
                default=datetime.now(),
            ),
        }

    def save_registry(self, file_path: Optional[Path] = None):
        """Save registry to JSON file"""
        save_path = file_path or self.registry_file
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert records to serializable format
        registry_data: Dict[str, Any] = {
            "metadata": {
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "total_universal_ids": len(self.universal_records),
            },
            "universal_records": {},
            "stage_file_mappings": self.stage_file_mappings,
            "filename_transformations": self.filename_transformations,
            "statistics": self.get_registry_statistics(),
        }

        for universal_id, record in self.universal_records.items():
            registry_data["universal_records"][universal_id] = {
                "universal_id": record.universal_id,
                "xml_data": record.xml_data,
                "midi_data": record.midi_data,
                "svg_data": record.svg_data,
                "match_confidence": record.match_confidence,
                "file_registrations": {
                    stage: asdict(file_reg)
                    for stage, file_reg in record.file_registrations.items()
                },
                "timing_data": record.timing_data,
                "after_effects_data": record.after_effects_data,
                "pipeline_stages_completed": list(record.pipeline_stages_completed),
                "last_updated": record.last_updated.isoformat(),
            }

        with open(save_path, "w") as f:
            json.dump(registry_data, f, indent=2, default=str)

        print(f"💾 Universal File Registry saved to: {save_path}")

    def load_registry(self, file_path: Optional[Path] = None):
        """Load registry from JSON file"""
        load_path = file_path or self.registry_file

        if not load_path.exists():
            print(f"⚠️  Registry file not found: {load_path}")
            return

        with open(load_path, "r") as f:
            registry_data = json.load(f)

        # Load universal records
        for universal_id, record_data in registry_data.get(
            "universal_records", {}
        ).items():
            # Reconstruct file registrations
            file_registrations = {}
            for stage, file_reg_data in record_data.get(
                "file_registrations", {}
            ).items():
                file_reg_data["created_at"] = datetime.fromisoformat(
                    file_reg_data["created_at"]
                )
                file_reg_data["updated_at"] = datetime.fromisoformat(
                    file_reg_data["updated_at"]
                )
                file_reg_data["file_path"] = Path(file_reg_data["file_path"])
                file_registrations[stage] = FileRegistration(**file_reg_data)

            # Reconstruct record
            record = UniversalIDRecord(
                universal_id=record_data["universal_id"],
                xml_data=record_data["xml_data"],
                midi_data=record_data.get("midi_data"),
                svg_data=record_data["svg_data"],
                match_confidence=record_data["match_confidence"],
                file_registrations=file_registrations,
                timing_data=record_data.get("timing_data", {}),
                after_effects_data=record_data.get("after_effects_data", {}),
                pipeline_stages_completed=set(
                    record_data.get("pipeline_stages_completed", [])
                ),
                last_updated=datetime.fromisoformat(record_data["last_updated"]),
            )

            self.universal_records[universal_id] = record

        # Load other data
        self.stage_file_mappings = registry_data.get("stage_file_mappings", {})
        self.filename_transformations = registry_data.get(
            "filename_transformations", {}
        )

        print(f"📂 Universal File Registry loaded from: {load_path}")
        print(f"   📊 Loaded {len(self.universal_records)} Universal ID records")
