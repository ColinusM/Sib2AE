#!/usr/bin/env python3
"""
Atomic Manifest Manager - Safe manifest operations with atomic writes

This module provides atomic manifest operations to prevent corruption during
pipeline failures. Manifests are "living documents" that get updated throughout
the pipeline execution and must maintain consistency.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from contextlib import contextmanager
import fcntl


class AtomicManifestManager:
    """
    Manager for atomic manifest operations to prevent corruption.

    Uses atomic write operations to ensure manifest consistency even
    during pipeline failures or interruptions.
    """

    def __init__(self, backup_enabled: bool = True, verbose: bool = True):
        """
        Initialize Atomic Manifest Manager.

        Args:
            backup_enabled: Whether to create backups before updates
            verbose: Whether to provide detailed logging
        """
        self.backup_enabled = backup_enabled
        self.verbose = verbose
        self.backup_dir = Path("universal_output/backups")
        self.temp_dir = Path("universal_output/temp")

        # Create necessary directories
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str):
        """Log message if verbose mode enabled"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 🔒 {message}")

    @contextmanager
    def atomic_write(self, file_path: Path, encoding: str = "utf-8"):
        """
        Context manager for atomic file writes.

        Creates a temporary file, writes to it, then atomically moves it
        to the target location to prevent corruption.

        Args:
            file_path: Target file path
            encoding: File encoding (default: utf-8)

        Yields:
            File handle for writing
        """
        file_path = Path(file_path)
        temp_file = self.temp_dir / f"{file_path.name}.tmp.{os.getpid()}"

        try:
            # Create backup if file exists and backup is enabled
            if self.backup_enabled and file_path.exists():
                self._create_backup(file_path)

            # Open temporary file for writing
            with open(temp_file, "w", encoding=encoding) as f:
                yield f
                f.flush()
                os.fsync(f.fileno())  # Force write to disk

            # Atomic move to target location
            shutil.move(str(temp_file), str(file_path))
            self.log(f"Atomic write completed: {file_path.name}")

        except Exception as e:
            # Clean up temporary file on error
            if temp_file.exists():
                temp_file.unlink()
            self.log(f"Atomic write failed for {file_path.name}: {e}")
            raise

    def load_manifest(self, manifest_path: Path, default: Any = None) -> Any:
        """
        Safely load a manifest file with error handling.

        Args:
            manifest_path: Path to manifest file
            default: Default value if file doesn't exist or is corrupted

        Returns:
            Loaded manifest data or default value
        """
        manifest_path = Path(manifest_path)

        if not manifest_path.exists():
            if default is not None:
                return default
            return {}

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                # Use file locking for read operations
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                    self.log(f"Loaded manifest: {manifest_path.name}")
                    return data
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        except (json.JSONDecodeError, IOError) as e:
            self.log(f"Failed to load manifest {manifest_path.name}: {e}")

            # Try to restore from backup if available
            if self.backup_enabled:
                restored = self._try_restore_from_backup(manifest_path)
                if restored is not None:
                    return restored

            # Return default if everything fails
            return default if default is not None else {}

    def update_manifest_atomically(
        self,
        manifest_path: Path,
        update_func: Callable[[Dict], Dict],
        default: Optional[Dict] = None,
    ) -> bool:
        """
        Atomically update a manifest file using an update function.

        Args:
            manifest_path: Path to manifest file
            update_func: Function that takes current data and returns updated data
            default: Default data structure if file doesn't exist

        Returns:
            True if update successful, False otherwise
        """
        try:
            # Load current data
            current_data = self.load_manifest(manifest_path, default or {})

            # Apply update function
            updated_data = update_func(current_data.copy())

            # Add metadata
            if isinstance(updated_data, dict):
                updated_data["_metadata"] = {
                    "last_updated": datetime.now().isoformat(),
                    "atomic_write": True,
                    "version": updated_data.get("_metadata", {}).get("version", 1) + 1,
                }

            # Write atomically
            with self.atomic_write(manifest_path) as f:
                json.dump(updated_data, f, indent=2, default=str)

            return True

        except Exception as e:
            self.log(f"Failed to update manifest {manifest_path.name}: {e}")
            return False

    def update_manifest_with_universal_id(
        self,
        manifest_path: Path,
        universal_id: str,
        stage: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update manifest with Universal ID file tracking information.

        Args:
            manifest_path: Path to manifest file
            universal_id: Universal ID to update
            stage: Pipeline stage name
            file_path: Actual file path created
            metadata: Additional metadata

        Returns:
            True if update successful, False otherwise
        """

        def update_func(manifest_data: Dict) -> Dict:
            # Ensure entries list exists
            if "entries" not in manifest_data:
                manifest_data["entries"] = []

            # Find existing entry or create new one
            entry_found = False
            for entry in manifest_data["entries"]:
                if entry.get("universal_id") == universal_id:
                    # Update existing entry
                    entry.update(
                        {
                            "actual_filename": Path(file_path).name,
                            "actual_file_path": str(file_path),
                            "file_exists": os.path.exists(file_path),
                            "file_size": os.path.getsize(file_path)
                            if os.path.exists(file_path)
                            else 0,
                            "stage_completed": stage,
                            "updated_at": datetime.now().isoformat(),
                            "metadata": metadata or {},
                        }
                    )
                    entry_found = True
                    break

            if not entry_found:
                # Create new entry
                new_entry = {
                    "universal_id": universal_id,
                    "actual_filename": Path(file_path).name,
                    "actual_file_path": str(file_path),
                    "file_exists": os.path.exists(file_path),
                    "file_size": os.path.getsize(file_path)
                    if os.path.exists(file_path)
                    else 0,
                    "stage_completed": stage,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "metadata": metadata or {},
                }
                manifest_data["entries"].append(new_entry)

            return manifest_data

        return self.update_manifest_atomically(manifest_path, update_func)

    def merge_manifests(
        self,
        primary_manifest: Path,
        secondary_manifest: Path,
        output_manifest: Path,
        merge_strategy: str = "primary_wins",
    ) -> bool:
        """
        Merge two manifests atomically.

        Args:
            primary_manifest: Primary manifest file
            secondary_manifest: Secondary manifest file
            output_manifest: Output merged manifest file
            merge_strategy: "primary_wins", "secondary_wins", or "deep_merge"

        Returns:
            True if merge successful, False otherwise
        """
        try:
            primary_data = self.load_manifest(primary_manifest, {})
            secondary_data = self.load_manifest(secondary_manifest, {})

            def merge_func(current_data: Dict) -> Dict:
                if merge_strategy == "primary_wins":
                    merged = secondary_data.copy()
                    merged.update(primary_data)
                elif merge_strategy == "secondary_wins":
                    merged = primary_data.copy()
                    merged.update(secondary_data)
                else:  # deep_merge
                    merged = self._deep_merge(primary_data, secondary_data)

                return merged

            return self.update_manifest_atomically(output_manifest, merge_func)

        except Exception as e:
            self.log(f"Failed to merge manifests: {e}")
            return False

    def _deep_merge(self, primary: Dict, secondary: Dict) -> Dict:
        """Deep merge two dictionaries"""
        merged = secondary.copy()

        for key, value in primary.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._deep_merge(value, merged[key])
            else:
                merged[key] = value

        return merged

    def validate_manifest_integrity(self, manifest_path: Path) -> Dict[str, Any]:
        """
        Validate manifest file integrity.

        Args:
            manifest_path: Path to manifest file

        Returns:
            Dictionary with validation results
        """
        validation_result: Dict[str, Any] = {
            "valid": False,
            "file_exists": False,
            "readable": False,
            "valid_json": False,
            "has_entries": False,
            "entry_count": 0,
            "issues": [],
        }

        try:
            # Check file existence
            if not manifest_path.exists():
                validation_result["issues"].append(
                    f"Manifest file does not exist: {manifest_path}"
                )
                return validation_result

            validation_result["file_exists"] = True

            # Check readability
            try:
                with open(manifest_path, "r") as f:
                    content = f.read()
                validation_result["readable"] = True
            except Exception as e:
                validation_result["issues"].append(f"Cannot read file: {e}")
                return validation_result

            # Check JSON validity
            try:
                data = json.loads(content)
                validation_result["valid_json"] = True
            except json.JSONDecodeError as e:
                validation_result["issues"].append(f"Invalid JSON: {e}")
                return validation_result

            # Check structure
            if isinstance(data, dict):
                if "entries" in data and isinstance(data["entries"], list):
                    validation_result["has_entries"] = True
                    validation_result["entry_count"] = len(data["entries"])

                    # Validate entries
                    for i, entry in enumerate(data["entries"]):
                        if not isinstance(entry, dict):
                            validation_result["issues"].append(
                                f"Entry {i} is not a dictionary"
                            )
                        elif "universal_id" not in entry:
                            validation_result["issues"].append(
                                f"Entry {i} missing universal_id"
                            )

            # Overall validation
            validation_result["valid"] = (
                validation_result["file_exists"]
                and validation_result["readable"]
                and validation_result["valid_json"]
                and len(validation_result["issues"]) == 0
            )

        except Exception as e:
            validation_result["issues"].append(f"Validation error: {e}")

        return validation_result

    def _create_backup(self, file_path: Path):
        """Create backup of existing file"""
        if not file_path.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name

        try:
            shutil.copy2(file_path, backup_path)
            self.log(f"Created backup: {backup_name}")
        except Exception as e:
            self.log(f"Failed to create backup for {file_path.name}: {e}")

    def _try_restore_from_backup(self, manifest_path: Path) -> Optional[Dict]:
        """Try to restore manifest from most recent backup"""
        if not self.backup_enabled:
            return None

        # Find most recent backup
        pattern = f"{manifest_path.stem}_*{manifest_path.suffix}"
        backup_files = list(self.backup_dir.glob(pattern))

        if not backup_files:
            return None

        # Sort by modification time (most recent first)
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        most_recent_backup = backup_files[0]

        try:
            with open(most_recent_backup, "r") as f:
                data = json.load(f)

            # Copy backup to original location
            shutil.copy2(most_recent_backup, manifest_path)
            self.log(f"Restored from backup: {most_recent_backup.name}")
            return data

        except Exception as e:
            self.log(f"Failed to restore from backup {most_recent_backup.name}: {e}")
            return None

    def cleanup_old_backups(self, keep_count: int = 10):
        """Clean up old backup files, keeping only the most recent ones"""
        try:
            backup_files = list(self.backup_dir.glob("*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Remove old backups beyond keep_count
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
                self.log(f"Removed old backup: {old_backup.name}")

        except Exception as e:
            self.log(f"Failed to cleanup old backups: {e}")

    def get_manifest_history(self, manifest_path: Path) -> List[Dict[str, Any]]:
        """Get history of a manifest from backups"""
        pattern = f"{manifest_path.stem}_*{manifest_path.suffix}"
        backup_files = list(self.backup_dir.glob(pattern))

        history = []
        for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime):
            try:
                stat_info = backup_file.stat()
                history.append(
                    {
                        "backup_file": backup_file.name,
                        "created_at": datetime.fromtimestamp(stat_info.st_mtime),
                        "size": stat_info.st_size,
                    }
                )
            except Exception as e:
                self.log(f"Failed to get info for backup {backup_file.name}: {e}")

        return history

    def verify_atomic_operations(self) -> bool:
        """Verify that atomic operations are working correctly"""
        test_file = self.temp_dir / "atomic_test.json"

        try:
            # Test atomic write
            test_data = {"test": True, "timestamp": datetime.now().isoformat()}
            with self.atomic_write(test_file) as f:
                json.dump(test_data, f)

            # Verify file was created and contains correct data
            if not test_file.exists():
                return False

            with open(test_file, "r") as f:
                loaded_data = json.load(f)

            if loaded_data != test_data:
                return False

            # Clean up
            test_file.unlink()
            return True

        except Exception as e:
            self.log(f"Atomic operations verification failed: {e}")
            return False


# Factory function for creating manifest managers
def create_manifest_manager(
    backup_enabled: bool = True, verbose: bool = True
) -> AtomicManifestManager:
    """Create a configured AtomicManifestManager instance"""
    return AtomicManifestManager(backup_enabled=backup_enabled, verbose=verbose)
