#!/usr/bin/env python3
"""
Universal ID Registry Utilities

Standardized registry loading and lookup patterns for all Sib2Ae pipeline scripts.
Provides robust Universal ID matching, validation, and fallback mechanisms.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import hashlib


@dataclass
class UniversalIDMatch:
    """
    Represents a Universal ID lookup result with confidence scoring.
    """
    universal_id: str
    confidence: float  # 0.0 to 1.0
    match_method: str  # e.g., "pitch_track_exact", "pitch_only", "filename_extraction"
    source_data: Dict[str, Any]  # Original registry entry


class UniversalIDRegistry:
    """
    Robust Universal ID registry loader with multiple lookup strategies.

    Provides standardized access patterns for all pipeline scripts with
    confidence-based matching, fallback mechanisms, and integrity validation.
    """

    def __init__(self, registry_path: Optional[str] = None, fallback_mode: bool = True):
        """
        Initialize Universal ID registry.

        Args:
            registry_path: Path to universal_notes_registry.json file
            fallback_mode: Enable graceful fallback to filename extraction
        """
        self.registry_path = registry_path
        self.fallback_mode = fallback_mode
        self.logger = logging.getLogger("UniversalIDRegistry")

        # Registry data
        self.registry_data: Dict[str, Any] = {}
        self.notes: List[Dict[str, Any]] = []

        # Optimized lookup tables
        self.pitch_track_index: Dict[Tuple[str, int], str] = {}  # (pitch, track) → universal_id
        self.pitch_time_index: Dict[Tuple[str, float], str] = {}  # (pitch, time) → universal_id
        self.pitch_only_index: Dict[str, List[str]] = {}  # pitch → [universal_id, ...]
        self.filename_index: Dict[str, str] = {}  # filename_pattern → universal_id
        self.universal_id_lookup: Dict[str, Dict[str, Any]] = {}  # universal_id → full_entry

        # Validation data
        self.registry_checksum: Optional[str] = None
        self.total_entries: int = 0

        # Load registry if provided
        if registry_path:
            self.load_registry(registry_path)

    def load_registry(self, registry_path: str) -> bool:
        """
        Load Universal ID registry from JSON file.

        Args:
            registry_path: Path to registry JSON file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            registry_file = Path(registry_path)
            if not registry_file.exists():
                self.logger.warning(f"Registry file not found: {registry_path}")
                return False

            with open(registry_file, 'r', encoding='utf-8') as f:
                self.registry_data = json.load(f)

            # Extract notes array
            if 'notes' in self.registry_data:
                self.notes = self.registry_data['notes']
            else:
                self.logger.error("Registry missing 'notes' array")
                return False

            # Build lookup indices
            self._build_lookup_indices()

            # Calculate checksum for integrity validation
            self.registry_checksum = self._calculate_checksum()
            self.total_entries = len(self.notes)

            self.logger.info(f"Registry loaded: {self.total_entries} entries from {registry_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load registry {registry_path}: {e}")
            return False

    def _build_lookup_indices(self):
        """Build optimized lookup tables for fast matching."""
        self.pitch_track_index.clear()
        self.pitch_time_index.clear()
        self.pitch_only_index.clear()
        self.filename_index.clear()
        self.universal_id_lookup.clear()

        for entry in self.notes:
            universal_id = entry.get('universal_id')
            if not universal_id:
                continue

            # Store full entry for lookup
            self.universal_id_lookup[universal_id] = entry

            # Build pitch+track index
            if 'midi_data' in entry and entry['midi_data']:
                midi_data = entry['midi_data']
                pitch = midi_data.get('pitch_name') or midi_data.get('pitch')
                track = midi_data.get('track', 0)
                start_time = midi_data.get('start_time_seconds', 0.0)

                if pitch:
                    # Pitch+track exact match (highest confidence)
                    self.pitch_track_index[(pitch, track)] = universal_id

                    # Pitch+time match (for temporal matching)
                    self.pitch_time_index[(pitch, start_time)] = universal_id

                    # Pitch-only match (fallback)
                    if pitch not in self.pitch_only_index:
                        self.pitch_only_index[pitch] = []
                    self.pitch_only_index[pitch].append(universal_id)

            # Build XML-based index
            if 'xml_data' in entry and entry['xml_data']:
                xml_data = entry['xml_data']
                pitch = xml_data.get('pitch') or xml_data.get('note_name')
                if pitch and pitch not in self.pitch_only_index:
                    self.pitch_only_index[pitch] = []
                    self.pitch_only_index[pitch].append(universal_id)

        self.logger.debug(f"Built indices: {len(self.pitch_track_index)} pitch+track, "
                         f"{len(self.pitch_only_index)} pitch-only entries")

    def get_universal_id_by_midi_match(self, pitch: str, track: int = 0,
                                     start_time: Optional[float] = None) -> UniversalIDMatch:
        """
        Get Universal ID by MIDI note matching with confidence scoring.

        Args:
            pitch: Note pitch (e.g., "A4", "B3")
            track: MIDI track number
            start_time: Note start time in seconds (optional)

        Returns:
            UniversalIDMatch with confidence score and method
        """
        # Strategy 1: Exact pitch+track match (highest confidence)
        key = (pitch, track)
        if key in self.pitch_track_index:
            universal_id = self.pitch_track_index[key]
            entry = self.universal_id_lookup[universal_id]
            return UniversalIDMatch(
                universal_id=universal_id,
                confidence=1.0,
                match_method="pitch_track_exact",
                source_data=entry
            )

        # Strategy 2: Pitch+time match (high confidence)
        if start_time is not None:
            # Look for matches within tolerance (±0.1 seconds)
            for (stored_pitch, stored_time), universal_id in self.pitch_time_index.items():
                if stored_pitch == pitch and abs(stored_time - start_time) < 0.1:
                    entry = self.universal_id_lookup[universal_id]
                    return UniversalIDMatch(
                        universal_id=universal_id,
                        confidence=0.9,
                        match_method="pitch_time_fuzzy",
                        source_data=entry
                    )

        # Strategy 3: Pitch-only match (medium confidence)
        if pitch in self.pitch_only_index:
            candidates = self.pitch_only_index[pitch]
            if len(candidates) == 1:
                universal_id = candidates[0]
                entry = self.universal_id_lookup[universal_id]
                return UniversalIDMatch(
                    universal_id=universal_id,
                    confidence=0.7,
                    match_method="pitch_only_unique",
                    source_data=entry
                )
            else:
                # Multiple matches - return first with lower confidence
                universal_id = candidates[0]
                entry = self.universal_id_lookup[universal_id]
                return UniversalIDMatch(
                    universal_id=universal_id,
                    confidence=0.5,
                    match_method="pitch_only_ambiguous",
                    source_data=entry
                )

        # No match found
        return UniversalIDMatch(
            universal_id="",
            confidence=0.0,
            match_method="no_match",
            source_data={}
        )

    def get_universal_id_by_xml_match(self, part_id: str, pitch: str,
                                    measure: int) -> UniversalIDMatch:
        """
        Get Universal ID by XML note matching.

        Args:
            part_id: MusicXML part ID (e.g., "P1", "P2")
            pitch: Note pitch (e.g., "A4", "B3")
            measure: Measure number

        Returns:
            UniversalIDMatch with confidence score and method
        """
        # Search for exact XML match
        for entry in self.notes:
            xml_data = entry.get('xml_data')
            # Skip entries with no xml_data (e.g., ornament expansions)
            if not xml_data or not isinstance(xml_data, dict):
                continue

            if (xml_data.get('part_id') == part_id and
                xml_data.get('pitch') == pitch and
                xml_data.get('measure') == measure):

                return UniversalIDMatch(
                    universal_id=entry['universal_id'],
                    confidence=1.0,
                    match_method="xml_exact",
                    source_data=entry
                )

        # Fallback to pitch-only match
        return self.get_universal_id_by_midi_match(pitch)

    def get_universal_id_from_filename(self, filename: str) -> UniversalIDMatch:
        """
        Extract Universal ID from filename using pattern matching.

        Args:
            filename: File name containing UUID pattern or ornament ID

        Returns:
            UniversalIDMatch with extracted ID or fallback
        """
        # First check for ornament Universal IDs (e.g., "exp_000", "exp_001")
        ornament_pattern = r'(exp_\d{3})'
        ornament_matches = re.findall(ornament_pattern, filename)
        if ornament_matches:
            # Find full ornament Universal ID (e.g., "orn_mordent_001_exp_000")
            partial_ornament = ornament_matches[0]  # e.g., "exp_000"
            for universal_id in self.universal_id_lookup:
                if universal_id.endswith(partial_ornament):
                    entry = self.universal_id_lookup[universal_id]
                    return UniversalIDMatch(
                        universal_id=universal_id,
                        confidence=0.95,
                        match_method="filename_ornament_expanded",
                        source_data=entry
                    )
            # Return partial ornament ID if no expansion found
            return UniversalIDMatch(
                universal_id=partial_ornament,
                confidence=0.6,
                match_method="filename_ornament_partial",
                source_data={}
            )

        # Extract UUID patterns from filename
        uuid_patterns = [
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',  # Full UUID
            r'[0-9a-f]{4,8}',  # UUID prefix (4-8 characters)
        ]

        for pattern in uuid_patterns:
            matches = re.findall(pattern, filename, re.IGNORECASE)
            if matches:
                extracted_id = matches[0]

                # Try to find full UUID from partial match
                if len(extracted_id) < 32:  # Partial UUID
                    for universal_id in self.universal_id_lookup:
                        if universal_id.startswith(extracted_id):
                            entry = self.universal_id_lookup[universal_id]
                            return UniversalIDMatch(
                                universal_id=universal_id,
                                confidence=0.8,
                                match_method="filename_partial_expanded",
                                source_data=entry
                            )

                    # Return partial ID if no expansion found
                    return UniversalIDMatch(
                        universal_id=extracted_id,
                        confidence=0.6,
                        match_method="filename_partial",
                        source_data={}
                    )
                else:
                    # Full UUID found
                    if extracted_id in self.universal_id_lookup:
                        entry = self.universal_id_lookup[extracted_id]
                        return UniversalIDMatch(
                            universal_id=extracted_id,
                            confidence=0.9,
                            match_method="filename_full",
                            source_data=entry
                        )

        # No UUID found in filename
        return UniversalIDMatch(
            universal_id="",
            confidence=0.0,
            match_method="filename_no_uuid",
            source_data={}
        )

    def validate_universal_id(self, universal_id: str) -> bool:
        """
        Validate Universal ID format and existence in registry.

        Args:
            universal_id: Universal ID to validate

        Returns:
            True if valid, False otherwise
        """
        if not universal_id:
            return False

        # Check UUID format
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, universal_id, re.IGNORECASE):
            return False

        # Check existence in registry
        return universal_id in self.universal_id_lookup

    def get_registry_entry(self, universal_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full registry entry for Universal ID.

        Args:
            universal_id: Universal ID to lookup

        Returns:
            Registry entry or None if not found
        """
        return self.universal_id_lookup.get(universal_id)

    def get_registry_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics and health information.

        Returns:
            Dictionary with registry statistics
        """
        return {
            "total_entries": self.total_entries,
            "registry_loaded": bool(self.registry_data),
            "checksum": self.registry_checksum,
            "indices_built": {
                "pitch_track": len(self.pitch_track_index),
                "pitch_time": len(self.pitch_time_index),
                "pitch_only": len(self.pitch_only_index),
                "universal_id_lookup": len(self.universal_id_lookup)
            },
            "registry_path": self.registry_path
        }

    def _calculate_checksum(self) -> str:
        """Calculate SHA256 checksum of registry data for integrity validation."""
        registry_str = json.dumps(self.registry_data, sort_keys=True)
        return hashlib.sha256(registry_str.encode()).hexdigest()[:16]


def create_registry_for_script(registry_path: Optional[str],
                             script_name: str,
                             fallback_mode: bool = True) -> UniversalIDRegistry:
    """
    Factory function to create registry instance for pipeline scripts.

    Args:
        registry_path: Path to registry file (None for fallback mode)
        script_name: Name of calling script (for logging)
        fallback_mode: Enable graceful fallback when registry unavailable

    Returns:
        Configured UniversalIDRegistry instance
    """
    logger = logging.getLogger(f"UniversalIDRegistry.{script_name}")

    registry = UniversalIDRegistry(registry_path, fallback_mode)

    if registry_path and registry.total_entries > 0:
        logger.info(f"Registry mode: Full registry loaded ({registry.total_entries} entries)")
    elif fallback_mode:
        logger.info("Registry mode: Fallback filename extraction")
    else:
        logger.warning("Registry mode: No registry available, may affect Universal ID preservation")

    return registry


def get_universal_id_with_fallback(registry: Optional[UniversalIDRegistry],
                                 primary_method: callable,
                                 fallback_filename: str = "") -> UniversalIDMatch:
    """
    Robust Universal ID lookup with fallback mechanisms.

    Args:
        registry: Registry instance (None for fallback only)
        primary_method: Primary lookup method to try
        fallback_filename: Filename for fallback extraction

    Returns:
        UniversalIDMatch with best available result
    """
    if registry and registry.total_entries > 0:
        try:
            match = primary_method()
            if match.confidence > 0.0:
                return match
        except Exception as e:
            logging.getLogger("UniversalIDRegistry").warning(f"Primary lookup failed: {e}")

    # Fallback to filename extraction
    if fallback_filename and registry:
        return registry.get_universal_id_from_filename(fallback_filename)

    # Ultimate fallback - return empty match
    return UniversalIDMatch(
        universal_id="",
        confidence=0.0,
        match_method="fallback_failed",
        source_data={}
    )