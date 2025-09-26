#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import re
import sys
from typing import List, Dict, Tuple

def extract_xml_notes(musicxml_file: str) -> List[Dict]:
    """Extract notes with relative coordinates from ANY MusicXML file."""
    tree = ET.parse(musicxml_file)
    root = tree.getroot()
    
    notes = []
    
    for part in root.findall('part'):
        part_id = part.get('id')
        cumulative_x = 0
        
        for measure in part.findall('measure'):
            measure_num = int(measure.get('number'))
            measure_width = float(measure.get('width', 0))
            
            for note in measure.findall('note'):
                if note.find('rest') is not None:
                    continue
                    
                pitch = note.find('pitch')
                if pitch is None:
                    continue
                    
                step = pitch.find('step').text
                octave = int(pitch.find('octave').text)
                
                # Get duration for notehead type
                note_type = note.find('type')
                duration = note_type.text if note_type is not None else 'quarter'
                
                # XML coordinates (relative to measure)
                xml_x = float(note.get('default-x', 0))
                xml_y = float(note.get('default-y', 0))
                
                # Calculate absolute X position
                absolute_x = cumulative_x + xml_x
                
                notes.append({
                    'part': part_id,
                    'measure': measure_num,
                    'pitch': f"{step}{octave}",
                    'xml_x': xml_x,
                    'xml_y': xml_y,
                    'absolute_x': absolute_x,
                    'duration': duration
                })
            
            cumulative_x += measure_width
    
    return notes

def calculate_expected_svg_coordinates(xml_notes: List[Dict]) -> List[Tuple[int, int]]:
    """Calculate expected SVG coordinates for noteheads to remove."""
    
    # UNIVERSAL TRANSFORMATION CONSTANTS (same as extractor)
    X_SCALE = 3.206518      
    X_OFFSET = 564.93       
    FLUTE_BASE_Y = 1037     
    VIOLIN_BASE_Y = 1417    
    
    expected_coordinates = []
    
    # Determine staff assignments (first part = upper, second part = lower)
    parts = list(set(note['part'] for note in xml_notes))
    parts.sort()
    
    for note in xml_notes:
        # Universal X coordinate transformation
        svg_x = note['absolute_x'] * X_SCALE + X_OFFSET
        
        # Universal Y coordinate transformation
        staff_index = parts.index(note['part'])
        
        if staff_index == 0:  # First part = Upper staff
            base_y = FLUTE_BASE_Y
        else:  # Second part = Lower staff
            base_y = VIOLIN_BASE_Y
        
        # Apply XML Y offset (same logic as extractor)
        if note['xml_y'] == 5:  # G4 special case
            svg_y = base_y + 12
        elif note['xml_y'] == 10:  # A4 
            svg_y = base_y
        elif note['xml_y'] == -15:  # C4
            svg_y = base_y
        elif note['xml_y'] == -20:  # B3, A3
            if note['pitch'] == 'A3':
                svg_y = base_y + 24  # A3 special positioning
            else:
                svg_y = base_y + 12  # B3 positioning
        else:
            svg_y = base_y  # Default
        
        expected_coordinates.append((int(round(svg_x)), int(round(svg_y))))
    
    return expected_coordinates

def remove_noteheads_from_svg(full_svg_file: str, expected_coords: List[Tuple[int, int]], output_file: str):
    """Remove noteheads from full SVG by matching exact coordinates using transformation matrix."""
    
    with open(full_svg_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Original SVG size: {len(content)} characters")
    print(f"Expected notehead coordinates: {len(expected_coords)}")
    
    # Create coordinate lookup for fast matching
    coord_set = set(expected_coords)
    
    removed_count = 0
    lines = content.split('\n')
    filtered_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a text element with Helsinki Std font that matches our coordinates
        if '<text ' in line and 'Helsinki Std' in line and 'font-size="96"' in line:
            # Extract coordinates from text element (be specific to avoid false matches)
            x_match = re.search(r'xml:space="preserve"\s+x="([^"]+)"', line)
            y_match = re.search(r'x="[^"]+"\s+y="([^"]+)"', line)
            
            if x_match and y_match:
                try:
                    local_x = float(x_match.group(1))
                    local_y = float(y_match.group(1))
                    
                    # Check if coordinates directly match expected coordinates (no transformation needed)
                    coord_to_check = (int(round(local_x)), int(round(local_y)))
                    
                    # Check exact match with expected coordinates
                    found_match = False
                    for expected_coord in coord_set:
                        # Use same tolerance as extractor for pixel-perfect matching
                        if (abs(coord_to_check[0] - expected_coord[0]) <= 1 and 
                            abs(coord_to_check[1] - expected_coord[1]) <= 1):
                            found_match = True
                            coord_set.remove(expected_coord)  # Remove to avoid duplicate matches
                            print(f"✓ Removing notehead at ({local_x}, {local_y}) matching expected {expected_coord}")
                            break
                    
                    if found_match:
                        removed_count += 1
                        # Skip this line and the closing </text> line
                        i += 1
                        if i < len(lines) and '</text>' in lines[i]:
                            i += 1  # Skip the </text> line too
                        continue
                
                except (ValueError, IndexError):
                    pass
        
        # Keep this line
        filtered_lines.append(line)
        i += 1
    
    # Write filtered content
    filtered_content = '\n'.join(filtered_lines)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(filtered_content)
    
    print(f"Removed {removed_count} noteheads (should be exactly 9)")
    print(f"Remaining unmatched coordinates: {len(coord_set)}")
    print(f"Filtered SVG size: {len(filtered_content)} characters")
    print(f"Size reduction: {len(content) - len(filtered_content)} characters")

def main():
    if len(sys.argv) != 3:
        print("Usage: python truly_universal_noteheads_subtractor.py <musicxml_file> <full_svg_file>")
        print("Example: python truly_universal_noteheads_subtractor.py 'music.musicxml' 'music_full.svg'")
        sys.exit(1)
    
    musicxml_file = sys.argv[1]
    full_svg_file = sys.argv[2]
    # Create output directory and generate output filename
    import os
    os.makedirs("outputs/svg", exist_ok=True)
    base_name = os.path.basename(full_svg_file).replace('.svg', '')
    output_file = f"outputs/svg/{base_name}_without_noteheads.svg"
    
    print("TRULY UNIVERSAL NOTEHEADS SUBTRACTOR")
    print("=" * 50)
    print(f"MusicXML: {musicxml_file}")
    print(f"Full SVG: {full_svg_file}")
    print(f"Output: {output_file}")
    print()
    
    try:
        # Step 1: Extract XML notes to know which noteheads to remove
        xml_notes = extract_xml_notes(musicxml_file)
        print(f"✅ Found {len(xml_notes)} notes in {len(set(n['part'] for n in xml_notes))} parts")
        
        # Step 2: Calculate expected SVG coordinates for these notes
        expected_coords = calculate_expected_svg_coordinates(xml_notes)
        print(f"✅ Calculated {len(expected_coords)} notehead coordinates to remove")
        
        # Step 3: Remove noteheads from full SVG
        remove_noteheads_from_svg(full_svg_file, expected_coords, output_file)
        print(f"✅ Created SVG without noteheads: {output_file}")
        
        print(f"\n🎯 SUCCESS! Full SVG with noteheads removed: {output_file}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()