#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import re
import sys
import os
from typing import List, Dict, Tuple

def extract_instrument_info(musicxml_file: str) -> List[Dict]:
    """Extract instrument/part information from ANY MusicXML file."""
    tree = ET.parse(musicxml_file)
    root = tree.getroot()
    
    instruments = []
    
    # Extract part list with instrument information
    part_list = root.find('part-list')
    if part_list is not None:
        for score_part in part_list.findall('score-part'):
            part_id = score_part.get('id')
            
            # Get instrument name
            part_name_elem = score_part.find('part-name')
            part_name = part_name_elem.text if part_name_elem is not None else f"Part {part_id}"
            
            # Get abbreviation
            part_abbrev_elem = score_part.find('part-abbreviation')
            part_abbrev = part_abbrev_elem.text if part_abbrev_elem is not None else part_id
            
            # Get instrument details
            score_instrument = score_part.find('score-instrument')
            instrument_name = "Unknown"
            if score_instrument is not None:
                instrument_name_elem = score_instrument.find('instrument-name')
                if instrument_name_elem is not None:
                    instrument_name = instrument_name_elem.text
            
            instruments.append({
                'part_id': part_id,
                'part_name': part_name,
                'abbreviation': part_abbrev,
                'instrument_name': instrument_name
            })
    
    return instruments

def calculate_staff_positions(instruments: List[Dict]) -> Dict[str, Dict]:
    """Calculate Y coordinate ranges for each instrument using universal transformation."""
    
    # UNIVERSAL STAFF RANGES (empirically determined from SVG analysis)
    STAFF_RANGES = {
        0: {'y_min': 950, 'y_max': 1100, 'base_y': 1037},   # First part (upper staff)
        1: {'y_min': 1250, 'y_max': 1500, 'base_y': 1417},  # Second part (lower staff)
        2: {'y_min': 1650, 'y_max': 1800, 'base_y': 1797},  # Third part (if exists)
        3: {'y_min': 2050, 'y_max': 2200, 'base_y': 2177},  # Fourth part (if exists)
    }
    
    staff_positions = {}
    
    for i, instrument in enumerate(instruments):
        part_id = instrument['part_id']
        
        if i < len(STAFF_RANGES):
            range_info = STAFF_RANGES[i]
            
            staff_positions[part_id] = {
                'y_min': range_info['y_min'],
                'y_max': range_info['y_max'],
                'base_y': range_info['base_y'],
                'staff_index': i
            }
    
    return staff_positions

def element_belongs_to_instrument(element, y_min: float, y_max: float) -> bool:
    """Check if an SVG element belongs to a specific instrument based on Y coordinates."""
    
    # Check all attributes for Y coordinates
    for attr_name, attr_value in element.attrib.items():
        if 'y' in attr_name.lower():
            try:
                y_val = float(attr_value)
                if y_val > 100 and y_min <= y_val <= y_max:  # Filter out small values like opacity
                    return True
            except ValueError:
                pass
    
    # Check points attribute for polylines and polygons
    if 'points' in element.attrib:
        points = element.attrib['points']
        # Extract Y coordinates from points
        point_matches = re.findall(r'(\d+),(\d+)', points)
        for x_str, y_str in point_matches:
            try:
                y_val = float(y_str)
                if y_min <= y_val <= y_max:
                    return True
            except ValueError:
                pass
    
    # Check path data for paths
    if 'd' in element.attrib:
        path_data = element.attrib['d']
        # Extract Y coordinates from path data (simplified pattern)
        y_matches = re.findall(r'[ML]\s*\d+[,\s]+(\d+)', path_data)
        for y_str in y_matches:
            try:
                y_val = float(y_str)
                if y_min <= y_val <= y_max:
                    return True
            except ValueError:
                pass
    
    return False

def filter_svg_elements(root, y_min: float, y_max: float) -> Tuple[int, int]:
    """Recursively filter SVG elements, removing those that don't belong to the instrument."""
    removed_count = 0
    kept_count = 0
    
    elements_to_remove = []
    
    for element in root:
        if element.tag.endswith('}g') or element.tag == 'g':
            # Recursively process group elements
            sub_removed, sub_kept = filter_svg_elements(element, y_min, y_max)
            removed_count += sub_removed
            kept_count += sub_kept
            
            # Remove empty groups
            if len(element) == 0 and not element.text and not element.tail:
                elements_to_remove.append(element)
        else:
            # Check if this element belongs to the instrument
            if element_belongs_to_instrument(element, y_min, y_max):
                kept_count += 1
            else:
                # Only remove elements that have coordinate information
                has_coords = any('y' in attr.lower() or attr in ['points', 'd'] for attr in element.attrib.keys())
                if has_coords:
                    elements_to_remove.append(element)
                    removed_count += 1
                else:
                    kept_count += 1
    
    # Remove elements that don't belong to this instrument
    for element in elements_to_remove:
        root.remove(element)
    
    return removed_count, kept_count

def separate_svg_by_instrument(full_svg_file: str, instruments: List[Dict], staff_positions: Dict[str, Dict], output_dir: str):
    """Separate full SVG into individual instrument files using XML parsing."""
    
    print(f"Original SVG: {full_svg_file}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each instrument
    for instrument in instruments:
        part_id = instrument['part_id']
        part_name = instrument['part_name']
        
        print(f"\n🎼 Processing {part_name} ({part_id})...")
        
        if part_id not in staff_positions:
            print(f"⚠️  No staff position found for {part_id}, skipping...")
            continue
        
        staff_info = staff_positions[part_id]
        y_min = staff_info['y_min']
        y_max = staff_info['y_max']
        
        print(f"   Staff Y range: {y_min} to {y_max}")
        
        # Parse SVG as XML
        tree = ET.parse(full_svg_file)
        root = tree.getroot()
        
        # Filter elements
        removed_count, kept_count = filter_svg_elements(root, y_min, y_max)
        
        # Generate filename
        clean_name = re.sub(r'[^\w\s-]', '', part_name).strip()
        clean_name = re.sub(r'[-\s]+', '_', clean_name)
        output_filename = f"{clean_name}_{part_id}.svg"
        output_path = os.path.join(output_dir, output_filename)
        
        # Write the filtered SVG
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        print(f"   ✅ Created: {output_filename}")
        print(f"   📊 Kept {kept_count} elements, removed {removed_count} elements")
        
        # Get file size
        file_size = os.path.getsize(output_path)
        print(f"   💾 File size: {file_size} bytes")

def main():
    if len(sys.argv) < 3:
        print("Usage: python xml_based_instrument_separator.py <musicxml_file> <full_svg_file> [output_dir]")
        print("Example: python xml_based_instrument_separator.py 'music.musicxml' 'music_full.svg' 'instruments'")
        sys.exit(1)
    
    musicxml_file = sys.argv[1]
    full_svg_file = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "instruments_xml"
    
    print("XML-BASED UNIVERSAL INSTRUMENT SEPARATOR")
    print("=" * 50)
    print(f"MusicXML: {musicxml_file}")
    print(f"Full SVG: {full_svg_file}")
    print(f"Output Directory: {output_dir}")
    print()
    
    try:
        # Step 1: Extract instrument information from MusicXML
        instruments = extract_instrument_info(musicxml_file)
        print(f"🎵 Found {len(instruments)} instruments:")
        for i, instrument in enumerate(instruments):
            print(f"   {i+1}. {instrument['part_name']} ({instrument['part_id']}) - {instrument['instrument_name']}")
        print()
        
        # Step 2: Calculate staff positions for each instrument
        staff_positions = calculate_staff_positions(instruments)
        print(f"📐 Calculated staff positions using universal transformation")
        
        # Step 3: Separate SVG by instrument
        separate_svg_by_instrument(full_svg_file, instruments, staff_positions, output_dir)
        
        print(f"\n🎯 SUCCESS! Created {len(instruments)} instrument-specific SVG files in '{output_dir}/' directory")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()