#!/usr/bin/env python3
"""
Basic smoke tests for manifest_manager module
"""

import pytest
import tempfile
import json
from pathlib import Path

from orchestrator.manifest_manager import AtomicManifestManager, create_manifest_manager


def test_manifest_manager_creation():
    """Test AtomicManifestManager instantiation"""
    manager = AtomicManifestManager(backup_enabled=True, verbose=False)

    assert manager.backup_enabled == True
    assert manager.verbose == False
    assert manager.backup_dir == Path("universal_output/backups")
    assert manager.temp_dir == Path("universal_output/temp")


def test_manifest_manager_factory():
    """Test create_manifest_manager factory function"""
    manager = create_manifest_manager(backup_enabled=False, verbose=True)

    assert manager.backup_enabled == False
    assert manager.verbose == True


def test_load_manifest_nonexistent_file():
    """Test loading a non-existent manifest file"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = AtomicManifestManager(backup_enabled=False, verbose=False)
        temp_path = Path(temp_dir) / "nonexistent.json"

        # Should return empty dict for non-existent file
        result = manager.load_manifest(temp_path)
        assert result == {}

        # Should return default value if provided
        default_data = {"default": True}
        result = manager.load_manifest(temp_path, default=default_data)
        assert result == default_data


def test_atomic_write_context_manager():
    """Test atomic write context manager"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = AtomicManifestManager(backup_enabled=False, verbose=False)
        manager.temp_dir = Path(temp_dir) / "temp"
        manager.temp_dir.mkdir(exist_ok=True)

        test_file = Path(temp_dir) / "test.json"
        test_data = {"test": "data", "number": 42}

        # Write using atomic write
        with manager.atomic_write(test_file) as f:
            json.dump(test_data, f)

        # Verify file exists and contains correct data
        assert test_file.exists()

        with open(test_file, 'r') as f:
            loaded_data = json.load(f)

        assert loaded_data == test_data


def test_update_manifest_atomically():
    """Test atomic manifest update"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = AtomicManifestManager(backup_enabled=False, verbose=False)
        manager.temp_dir = Path(temp_dir) / "temp"
        manager.temp_dir.mkdir(exist_ok=True)

        manifest_path = Path(temp_dir) / "test_manifest.json"

        # Update function that adds a new key
        def update_func(data):
            data["updated"] = True
            data["count"] = data.get("count", 0) + 1
            return data

        # First update (file doesn't exist)
        success = manager.update_manifest_atomically(manifest_path, update_func)
        assert success == True

        # Verify file exists and has metadata
        assert manifest_path.exists()

        data = manager.load_manifest(manifest_path)
        assert data["updated"] == True
        assert data["count"] == 1
        assert "_metadata" in data
        assert "last_updated" in data["_metadata"]
        assert data["_metadata"]["atomic_write"] == True


def test_update_manifest_with_universal_id():
    """Test updating manifest with Universal ID information"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = AtomicManifestManager(backup_enabled=False, verbose=False)
        manager.temp_dir = Path(temp_dir) / "temp"
        manager.temp_dir.mkdir(exist_ok=True)

        manifest_path = Path(temp_dir) / "test_manifest.json"

        # Create a test file to reference
        test_file = Path(temp_dir) / "test_audio.wav"
        test_file.write_text("dummy audio content")

        universal_id = "test-uuid-1234"
        stage = "audio_rendering"
        metadata = {"instrument": "Flûte", "pitch": "A4"}

        # Update manifest with Universal ID info
        success = manager.update_manifest_with_universal_id(
            manifest_path, universal_id, stage, str(test_file), metadata
        )

        assert success == True

        # Verify manifest content
        data = manager.load_manifest(manifest_path)
        assert "entries" in data
        assert len(data["entries"]) == 1

        entry = data["entries"][0]
        assert entry["universal_id"] == universal_id
        assert entry["stage_completed"] == stage
        assert entry["actual_filename"] == "test_audio.wav"
        assert entry["file_exists"] == True
        assert entry["metadata"] == metadata


def test_validate_manifest_integrity():
    """Test manifest integrity validation"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = AtomicManifestManager(backup_enabled=False, verbose=False)
        manifest_path = Path(temp_dir) / "test_manifest.json"

        # Test non-existent file
        result = manager.validate_manifest_integrity(manifest_path)
        assert result["valid"] == False
        assert result["file_exists"] == False
        assert "does not exist" in result["issues"][0]

        # Create valid manifest
        valid_data = {
            "entries": [
                {"universal_id": "test-1", "data": "value1"},
                {"universal_id": "test-2", "data": "value2"}
            ]
        }

        with open(manifest_path, 'w') as f:
            json.dump(valid_data, f)

        # Test valid manifest
        result = manager.validate_manifest_integrity(manifest_path)
        assert result["valid"] == True
        assert result["file_exists"] == True
        assert result["readable"] == True
        assert result["valid_json"] == True
        assert result["has_entries"] == True
        assert result["entry_count"] == 2
        assert len(result["issues"]) == 0


def test_verify_atomic_operations():
    """Test atomic operations verification"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = AtomicManifestManager(backup_enabled=False, verbose=False)
        manager.temp_dir = Path(temp_dir) / "temp"
        manager.temp_dir.mkdir(exist_ok=True)

        # Verify atomic operations work
        result = manager.verify_atomic_operations()
        assert result == True