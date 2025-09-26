#!/usr/bin/env python3
"""
Migration script to consolidate all output folders into master outputs/ structure
Option 2: By File Type (svg/, audio/, json/, midi/)
"""

import os
import shutil
from pathlib import Path
import json

def ensure_dir(path):
    """Create directory if it doesn't exist"""
    Path(path).mkdir(parents=True, exist_ok=True)

def migrate_outputs():
    """Migrate all existing outputs to new structure"""

    print("🔄 Starting migration to master outputs/ structure...")

    # Create new structure
    ensure_dir("outputs/svg/instruments")
    ensure_dir("outputs/svg/noteheads")
    ensure_dir("outputs/svg/staff_barlines")
    ensure_dir("outputs/svg/annotated")
    ensure_dir("outputs/audio")
    ensure_dir("outputs/json/keyframes")
    ensure_dir("outputs/json/coordination")
    ensure_dir("outputs/json/manifests")
    ensure_dir("outputs/midi")

    moved_files = []

    # 1. Migrate Brain/Audio/ to outputs/audio/
    brain_audio = Path("Brain/Audio")
    if brain_audio.exists():
        print(f"📁 Migrating {brain_audio} to outputs/audio/")
        for item in brain_audio.iterdir():
            if item.is_dir() and item.name != "Keyframes":
                # Move instrument directories (Flûte, Violon, etc.)
                dest = Path(f"outputs/audio/{item.name}")
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(item), str(dest))
                moved_files.append(f"{item} → {dest}")

        # Move keyframes separately
        keyframes_dir = brain_audio / "Keyframes"
        if keyframes_dir.exists():
            print("📁 Migrating keyframes to outputs/json/keyframes/")
            for keyframe_file in keyframes_dir.glob("*.json"):
                dest = Path(f"outputs/json/keyframes/{keyframe_file.name}")
                shutil.move(str(keyframe_file), str(dest))
                moved_files.append(f"{keyframe_file} → {dest}")

    # 2. Migrate Brain/instruments_output/ to outputs/svg/instruments/
    instruments_dir = Path("Brain/instruments_output")
    if instruments_dir.exists():
        print(f"📁 Migrating {instruments_dir} to outputs/svg/instruments/")
        for svg_file in instruments_dir.glob("*.svg"):
            dest = Path(f"outputs/svg/instruments/{svg_file.name}")
            shutil.move(str(svg_file), str(dest))
            moved_files.append(f"{svg_file} → {dest}")

    # 3. Migrate individual noteheads to outputs/svg/noteheads/
    notehead_patterns = [
        "Brain/*_noteheads_*.svg",
        "Brain/individual_noteheads/*.svg",
        "**/individual_noteheads/*.svg"
    ]
    for pattern in notehead_patterns:
        for svg_file in Path(".").glob(pattern):
            if svg_file.is_file():
                dest = Path(f"outputs/svg/noteheads/{svg_file.name}")
                print(f"📁 Migrating notehead {svg_file} to {dest}")
                shutil.move(str(svg_file), str(dest))
                moved_files.append(f"{svg_file} → {dest}")

    # 4. Migrate staff/barlines SVGs to outputs/svg/staff_barlines/
    staff_patterns = [
        "Brain/*_staff_barlines.svg",
        "Brain/*_without_noteheads.svg"
    ]
    for pattern in staff_patterns:
        for svg_file in Path(".").glob(pattern):
            if svg_file.is_file():
                dest = Path(f"outputs/svg/staff_barlines/{svg_file.name}")
                print(f"📁 Migrating staff/barlines {svg_file} to {dest}")
                shutil.move(str(svg_file), str(dest))
                moved_files.append(f"{svg_file} → {dest}")

    # 5. Migrate annotated SVGs to outputs/svg/annotated/
    annotated_dirs = ["output", "coordinator_output"]
    for dir_name in annotated_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"📁 Migrating {dir_path} to outputs/svg/annotated/")
            for svg_file in dir_path.glob("*.svg"):
                dest = Path(f"outputs/svg/annotated/{svg_file.name}")
                shutil.move(str(svg_file), str(dest))
                moved_files.append(f"{svg_file} → {dest}")

    # 6. Migrate coordination JSONs to outputs/json/coordination/
    coordination_dirs = [
        "Brain/universal_output",
        "Brain/test_output",
        "Brain/working_output",
        "coordinator_output",
        "universal_output",
        "test_coordination_output"
    ]
    for dir_name in coordination_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"📁 Migrating {dir_path} coordination files to outputs/json/coordination/")
            for json_file in dir_path.glob("*.json"):
                # Determine subfolder based on file type
                if "manifest" in json_file.name:
                    dest = Path(f"outputs/json/manifests/{json_file.name}")
                else:
                    dest = Path(f"outputs/json/coordination/{json_file.name}")

                ensure_dir(dest.parent)
                if dest.exists():
                    # Add timestamp to avoid conflicts
                    stem = dest.stem
                    suffix = dest.suffix
                    dest = dest.parent / f"{stem}_backup{suffix}"

                shutil.move(str(json_file), str(dest))
                moved_files.append(f"{json_file} → {dest}")

    # 7. Migrate MIDI files to outputs/midi/
    midi_patterns = [
        "Brain/Base/*_individual_notes/*.mid",
        "Brain/*_individual_notes/*.mid"
    ]
    for pattern in midi_patterns:
        for midi_file in Path(".").glob(pattern):
            if midi_file.is_file():
                dest = Path(f"outputs/midi/{midi_file.name}")
                print(f"📁 Migrating MIDI {midi_file} to {dest}")
                shutil.move(str(midi_file), str(dest))
                moved_files.append(f"{midi_file} → {dest}")

    # 8. Clean up empty directories
    empty_dirs = []
    for dir_name in coordination_dirs + ["output"]:
        dir_path = Path(dir_name)
        if dir_path.exists() and not any(dir_path.iterdir()):
            shutil.rmtree(dir_path)
            empty_dirs.append(str(dir_path))

    # Create migration report
    report = {
        "migration_timestamp": "2025-09-26",
        "moved_files_count": len(moved_files),
        "moved_files": moved_files,
        "cleaned_directories": empty_dirs,
        "new_structure": {
            "outputs/svg/": "All SVG outputs (instruments, noteheads, staff/barlines, annotated)",
            "outputs/audio/": "All audio files organized by instrument",
            "outputs/json/": "All JSON outputs (keyframes, coordination, manifests)",
            "outputs/midi/": "Individual MIDI note files"
        }
    }

    with open("outputs/migration_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Migration complete!")
    print(f"📊 Moved {len(moved_files)} files")
    print(f"🗑️  Cleaned {len(empty_dirs)} empty directories")
    print(f"📋 Report saved to: outputs/migration_report.json")

    return report

if __name__ == "__main__":
    migrate_outputs()