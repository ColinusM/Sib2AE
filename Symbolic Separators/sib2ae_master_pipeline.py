#!/usr/bin/env python3
"""
Sib2Ae Master Pipeline - Universal MusicXML to SVG Processing

Runs the complete four-tool pipeline in sequence:
1. Noteheads Extractor - Extract noteheads from MusicXML
2. Noteheads Subtractor - Remove noteheads from full SVG
3. Instrument Separator - Separate instruments into individual SVGs
4. Individual Noteheads Creator - Create one file per notehead

Creates organized output structure with all processed files.
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def run_command(command: list, description: str):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    print(f"   Command: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"   ✅ {description} completed successfully")
        if result.stdout.strip():
            # Print summary lines only (skip verbose output)
            lines = result.stdout.strip().split('\n')
            summary_lines = [line for line in lines if '✅' in line or '🎯' in line or 'SUCCESS' in line]
            for line in summary_lines[-3:]:  # Show last 3 summary lines
                print(f"   {line}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def create_organized_output(base_name: str, output_dir: str):
    """Create instrument-focused folder structure."""
    print(f"\n📁 Creating organized output structure in '{output_dir}'...")
    
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get instrument information from separated files
    instruments = {}
    if os.path.exists("instruments_separated"):
        for file in os.listdir("instruments_separated"):
            if file.endswith(".svg"):
                # Parse instrument name from filename (e.g., "Flûte_P1.svg")
                name_part = file.replace(".svg", "")
                if "_" in name_part:
                    instrument_name = name_part.split("_")[0]
                    part_id = name_part.split("_")[1]
                    instruments[part_id] = {
                        "name": instrument_name,
                        "file": file,
                        "clean_name": instrument_name.replace("û", "u").replace("ô", "o")
                    }
    
    # Create folder for each instrument
    for part_id, info in instruments.items():
        instrument_dir = os.path.join(output_dir, info["clean_name"])
        individual_dir = os.path.join(instrument_dir, "individual_noteheads")
        os.makedirs(individual_dir, exist_ok=True)
        
        print(f"\n   🎼 Creating {info['name']} ({part_id}) folder...")
        
        # 1. Move full instrument SVG (complete with everything)
        src_full = os.path.join("instruments_separated", info["file"])
        dest_full = os.path.join(instrument_dir, f"{info['clean_name']}_full.svg")
        if os.path.exists(src_full):
            shutil.move(src_full, dest_full)
            print(f"      📄 Full: {info['clean_name']}_full.svg")
        
        # 2. Create noteheads-only version for this instrument
        noteheads_file = f"Base/{base_name}_noteheads_universal.svg"
        if os.path.exists(noteheads_file):
            # Use instrument separator on noteheads file to get per-instrument noteheads
            temp_dir = f"temp_noteheads_{part_id}"
            result = subprocess.run([
                "python", "xml_based_instrument_separator.py", 
                f"Base/{base_name}.musicxml", noteheads_file, temp_dir
            ], capture_output=True, text=True)
            
            # Move the noteheads-only file for this instrument
            temp_file = os.path.join(temp_dir, info["file"])
            if os.path.exists(temp_file):
                dest_noteheads = os.path.join(instrument_dir, f"{info['clean_name']}_noteheads_only.svg")
                shutil.move(temp_file, dest_noteheads)
                print(f"      🎵 Noteheads: {info['clean_name']}_noteheads_only.svg")
            
            # Clean up temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        
        # 3. Create without-noteheads version for this instrument
        without_noteheads_file = f"Base/{base_name} full_without_noteheads.svg"
        if os.path.exists(without_noteheads_file):
            # Use instrument separator on without-noteheads file
            temp_dir = f"temp_without_{part_id}"
            result = subprocess.run([
                "python", "xml_based_instrument_separator.py",
                f"Base/{base_name}.musicxml", without_noteheads_file, temp_dir
            ], capture_output=True, text=True)
            
            # Move the without-noteheads file for this instrument
            temp_file = os.path.join(temp_dir, info["file"])
            if os.path.exists(temp_file):
                dest_without = os.path.join(instrument_dir, f"{info['clean_name']}_without_noteheads.svg")
                shutil.move(temp_file, dest_without)
                print(f"      ✂️ Without: {info['clean_name']}_without_noteheads.svg")
            
            # Clean up temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        
        # 4. Move individual noteheads for this instrument
        if os.path.exists("individual_noteheads"):
            individual_count = 0
            for file in os.listdir("individual_noteheads"):
                if f"_{part_id}_" in file:  # Match files for this part
                    src = os.path.join("individual_noteheads", file)
                    dest = os.path.join(individual_dir, file)
                    shutil.move(src, dest)
                    individual_count += 1
            print(f"      📝 Individual: {individual_count} noteheads")
    
    # Clean up temporary directories
    if os.path.exists("instruments_separated"):
        shutil.rmtree("instruments_separated")
    if os.path.exists("individual_noteheads"):
        shutil.rmtree("individual_noteheads")
    
    # Clean up base files
    cleanup_files = [
        f"Base/{base_name}_noteheads_universal.svg",
        f"Base/{base_name} full_without_noteheads.svg"
    ]
    for file_path in cleanup_files:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"   🧹 Cleaned: {os.path.basename(file_path)}")
    
    print(f"\n   ✅ Instrument-focused structure created in '{output_dir}'")

def main():
    if len(sys.argv) < 2:
        print("SIB2AE MASTER PIPELINE")
        print("=" * 50)
        print("Usage: python sib2ae_master_pipeline.py <base_name> [output_dir]")
        print("Example: python sib2ae_master_pipeline.py 'SS 9' 'sib2ae_output'")
        print()
        print("Requirements:")
        print("  - Base/<base_name>.musicxml")
        print("  - Base/<base_name> full.svg")
        print()
        print("Output: Complete organized folder with all processed files")
        sys.exit(1)
    
    base_name = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else f"sib2ae_{base_name.replace(' ', '_')}_output"
    
    # Derive file paths
    musicxml_file = f"Base/{base_name}.musicxml"
    full_svg_file = f"Base/{base_name} full.svg"
    
    print("SIB2AE MASTER PIPELINE")
    print("=" * 50)
    print(f"📁 Base Name: {base_name}")
    print(f"🎼 MusicXML: {musicxml_file}")
    print(f"🖼️ Full SVG: {full_svg_file}")
    print(f"📂 Output Directory: {output_dir}")
    print()
    
    # Check input files exist
    if not os.path.exists(musicxml_file):
        print(f"❌ ERROR: MusicXML file not found: {musicxml_file}")
        sys.exit(1)
    
    if not os.path.exists(full_svg_file):
        print(f"❌ ERROR: SVG file not found: {full_svg_file}")
        sys.exit(1)
    
    # Pipeline steps
    steps = [
        {
            "command": ["python", "truly_universal_noteheads_extractor.py", musicxml_file],
            "description": "Step 1: Extract Noteheads"
        },
        {
            "command": ["python", "truly_universal_noteheads_subtractor.py", musicxml_file, full_svg_file],
            "description": "Step 2: Subtract Noteheads from Full SVG"
        },
        {
            "command": ["python", "xml_based_instrument_separator.py", musicxml_file, full_svg_file, "instruments_separated"],
            "description": "Step 3: Separate Instruments"
        },
        {
            "command": ["python", "individual_noteheads_creator.py", musicxml_file, "individual_noteheads"],
            "description": "Step 4: Create Individual Noteheads"
        }
    ]
    
    # Execute pipeline
    success_count = 0
    for step in steps:
        if run_command(step["command"], step["description"]):
            success_count += 1
        else:
            print(f"\n❌ Pipeline failed at: {step['description']}")
            sys.exit(1)
    
    # Create organized output structure
    create_organized_output(base_name, output_dir)
    
    # Final summary
    print(f"\n🎯 PIPELINE COMPLETE!")
    print("=" * 50)
    print(f"✅ Successfully completed {success_count}/4 steps")
    print(f"📁 All files organized in: {output_dir}/")
    print()
    print("📂 Output Structure:")
    print("   [Instrument]/")
    print("   ├── [instrument]_full.svg           - Complete instrument with all elements")
    print("   ├── [instrument]_noteheads_only.svg - Only noteheads for this instrument")
    print("   ├── [instrument]_without_noteheads.svg - Instrument without noteheads")
    print("   └── individual_noteheads/           - One SVG per notehead")
    print("       ├── notehead_000_[part]_[note]_M[measure].svg")
    print("       └── ...")
    print()
    print("🚀 Ready for After Effects import!")

if __name__ == "__main__":
    main()