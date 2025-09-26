#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import sys
import re
from typing import List, Dict, Tuple

def extract_xml_structure(musicxml_file: str) -> Dict:
    """Extract staff and measure structure from MusicXML file."""
    tree = ET.parse(musicxml_file)
    root = tree.getroot()
    
    # Extract scaling information for universal coordinate conversion
    scaling = root.find('defaults/scaling')
    if scaling is not None:
        tenths = float(scaling.find('tenths').text)
        mm = float(scaling.find('millimeters').text)
        scaling_factor = mm / tenths
    else:
        scaling_factor = 0.15  # Default scaling
    
    # Count instruments/parts
    part_list = root.find('part-list')
    instruments = []
    if part_list is not None:
        for score_part in part_list.findall('score-part'):
            part_id = score_part.get('id')
            part_name_elem = score_part.find('part-name')
            part_name = part_name_elem.text if part_name_elem is not None else f"Part {part_id}"
            instruments.append({'part_id': part_id, 'part_name': part_name})
    
    # Extract measure information from first part
    measures = []
    first_part = root.find('part')
    if first_part is not None:
        cumulative_x = 0
        for measure in first_part.findall('measure'):
            measure_num = int(measure.get('number'))
            measure_width = float(measure.get('width', 0))
            
            measures.append({
                'number': measure_num,
                'width': measure_width,
                'start_x': cumulative_x,
                'end_x': cumulative_x + measure_width
            })
            
            cumulative_x += measure_width
    
    return {
        'instruments': instruments,
        'measures': measures,
        'scaling_factor': scaling_factor,
        'staff_count': len(instruments)
    }

def identify_staff_lines(svg_content: str, staff_count: int) -> List[Dict]:
    """Identify horizontal staff lines in SVG content, excluding ledger lines."""
    
    # Universal staff Y positions
    STAFF_Y_RANGES = {
        0: {'y_min': 950, 'y_max': 1100},   # First staff (Flute)
        1: {'y_min': 1250, 'y_max': 1500}, # Second staff (Violin)
        2: {'y_min': 1650, 'y_max': 1800}, # Third staff
        3: {'y_min': 2050, 'y_max': 2200}, # Fourth staff
    }
    
    staff_lines = []
    
    # Pattern to find polyline elements with their stroke-width context
    # Look for stroke-width="2.25" which indicates staff lines (not ledger lines)
    staff_line_pattern = r'stroke-width="2\.25"[^>]*>.*?<polyline[^>]*points="([^"]+)"[^>]*/>'
    matches = re.findall(staff_line_pattern, svg_content, re.DOTALL)
    
    for points_str in matches:
        # Parse points to check if horizontal
        points = []
        point_matches = re.findall(r'(\d+),(\d+)', points_str)
        for x_str, y_str in point_matches:
            points.append((float(x_str), float(y_str)))
        
        if len(points) >= 2:
            # Check if this is a horizontal line (same Y coordinates)
            y_coords = [p[1] for p in points]
            if len(set(y_coords)) == 1:  # All Y coordinates are the same
                y_coord = y_coords[0]
                x_coords = [p[0] for p in points]
                
                # Only include FULL-WIDTH staff lines (exclude short ledger lines)
                line_width = max(x_coords) - min(x_coords)
                if line_width > 3000:  # Full staff width threshold
                    # Check if Y coordinate falls within any staff range
                    for staff_index in range(staff_count):
                        if staff_index in STAFF_Y_RANGES:
                            y_range = STAFF_Y_RANGES[staff_index]
                            if y_range['y_min'] <= y_coord <= y_range['y_max']:
                                staff_lines.append({
                                    'staff_index': staff_index,
                                    'y_coord': y_coord,
                                    'x_start': min(x_coords),
                                    'x_end': max(x_coords),
                                    'points': points_str,
                                    'type': 'staff_line',
                                    'stroke_width': '2.25'
                                })
                                break
    
    return staff_lines

def identify_barlines(svg_content: str, measures: List[Dict], staff_count: int) -> List[Dict]:
    """Identify vertical barlines in SVG content."""
    
    # Universal coordinate transformation
    X_SCALE = 3.206518
    X_OFFSET = 564.93
    
    # Calculate expected barline X positions from measures
    expected_x_positions = []
    for measure in measures:
        start_x = measure['start_x'] * X_SCALE + X_OFFSET
        end_x = measure['end_x'] * X_SCALE + X_OFFSET
        expected_x_positions.extend([start_x, end_x])
    
    barlines = []
    
    # Pattern to find polyline elements with stroke-width="5" (regular barlines) or "16" (thick end barlines)
    stroke_width_pattern = r'stroke-width="(5|16)"[^>]*>.*?<polyline[^>]*points="([^"]+)"[^>]*/>'
    stroke_matches = re.findall(stroke_width_pattern, svg_content, re.DOTALL)
    
    for stroke_width, points_str in stroke_matches:
        # Parse points to check if vertical
        points = []
        point_matches = re.findall(r'(\d+),(\d+)', points_str)
        for x_str, y_str in point_matches:
            points.append((float(x_str), float(y_str)))
        
        if len(points) >= 2:
            # Check if this is a vertical line (same X coordinates)
            x_coords = [p[0] for p in points]
            if len(set(x_coords)) == 1:  # All X coordinates are the same
                x_coord = x_coords[0]
                y_coords = [p[1] for p in points]
                
                barlines.append({
                    'x_coord': x_coord,
                    'y_start': min(y_coords),
                    'y_end': max(y_coords),
                    'points': points_str,
                    'type': 'thick_barline' if stroke_width == '16' else 'barline',
                    'stroke_width': stroke_width
                })
    
    return barlines

def create_staff_barlines_svg(staff_lines: List[Dict], barlines: List[Dict], output_file: str):
    """Create SVG with only staff lines and barlines with correct stroke widths."""
    
    # Universal SVG header (same as other tools)
    svg_content = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="228.6mm" height="304.8mm"
 viewBox="0 0 2592 3455"
 xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.2" baseProfile="tiny">
<desc>Staff Lines and Barlines - Universal Structure</desc>
<defs>
</defs>
<g fill="none" stroke="black" stroke-width="1" fill-rule="evenodd" stroke-linecap="square" stroke-linejoin="bevel">

<!-- Staff Lines (stroke-width 2.25) -->
<g fill="#000000" fill-opacity="1" stroke="#000000" stroke-opacity="1" stroke-width="2.25" stroke-linecap="butt" stroke-linejoin="bevel" transform="matrix(0.531496,0,0,0.531496,0,0)">
'''
    
    # Add staff lines with correct stroke width
    for staff_line in staff_lines:
        svg_content += f'''<polyline fill="none" vector-effect="none" points="{staff_line['points']}" />
'''
    
    svg_content += '''</g>

<!-- Regular Barlines (stroke-width 5) -->
<g fill="none" stroke="#000000" stroke-opacity="1" stroke-width="5" stroke-linecap="butt" stroke-linejoin="bevel" transform="matrix(0.531496,0,0,0.531496,0,0)">
'''
    
    # Add regular barlines (stroke-width 5)
    for barline in barlines:
        if barline['stroke_width'] == '5':
            svg_content += f'''<polyline fill="none" vector-effect="none" points="{barline['points']}" />
'''
    
    svg_content += '''</g>

<!-- Thick End Barlines (stroke-width 16) -->
<g fill="none" stroke="#000000" stroke-opacity="1" stroke-width="16" stroke-linecap="butt" stroke-linejoin="bevel" transform="matrix(0.531496,0,0,0.531496,0,0)">
'''
    
    # Add thick end barlines (stroke-width 16)
    for barline in barlines:
        if barline['stroke_width'] == '16':
            svg_content += f'''<polyline fill="none" vector-effect="none" points="{barline['points']}" />
'''
    
    svg_content += '''</g>

</g>
</svg>'''
    
    # Write the SVG file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(svg_content)

def extract_staff_barlines(musicxml_file: str, full_svg_file: str):
    """Extract staff lines and barlines from full SVG using MusicXML structure."""
    
    print("STAFF LINES + BARLINES EXTRACTOR")
    print("=" * 50)
    print(f"MusicXML: {musicxml_file}")
    print(f"Full SVG: {full_svg_file}")
    print()
    
    # Extract structure from MusicXML
    structure = extract_xml_structure(musicxml_file)
    print(f"🎼 Found {structure['staff_count']} staves")
    print(f"📏 Found {len(structure['measures'])} measures")
    
    # Read SVG content
    with open(full_svg_file, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    # Identify staff lines
    staff_lines = identify_staff_lines(svg_content, structure['staff_count'])
    print(f"📐 Identified {len(staff_lines)} staff lines")
    
    # Identify barlines  
    barlines = identify_barlines(svg_content, structure['measures'], structure['staff_count'])
    print(f"📏 Identified {len(barlines)} barlines")
    
    # Generate output filename using proper path handling
    import os
    os.makedirs("outputs/svg/staff_barlines", exist_ok=True)
    base_name = os.path.splitext(os.path.basename(musicxml_file))[0]
    output_file = f"outputs/svg/staff_barlines/{base_name}_staff_barlines.svg"
    
    # Create staff/barlines SVG
    create_staff_barlines_svg(staff_lines, barlines, output_file)
    
    print(f"\n✅ Created staff lines and barlines SVG: {output_file}")
    
    # Summary by staff
    staff_summary = {}
    for staff_line in staff_lines:
        staff_idx = staff_line['staff_index']
        if staff_idx not in staff_summary:
            staff_summary[staff_idx] = []
        staff_summary[staff_idx].append(staff_line)
    
    print("\nSUMMARY BY STAFF:")
    for staff_idx, lines in staff_summary.items():
        instrument_name = structure['instruments'][staff_idx]['part_name'] if staff_idx < len(structure['instruments']) else f"Staff {staff_idx+1}"
        print(f"  {instrument_name}: {len(lines)} staff lines")
        for line in lines:
            print(f"    Y={line['y_coord']} (X: {line['x_start']}-{line['x_end']})")
    
    print(f"\nBARLINES:")
    for barline in barlines:
        barline_type = "THICK" if barline['stroke_width'] == '16' else "regular"
        print(f"  X={barline['x_coord']} (Y: {barline['y_start']}-{barline['y_end']}) - {barline_type} (stroke-width={barline['stroke_width']})")
    
    print(f"\n🎯 SUCCESS! Extracted {len(staff_lines)} staff lines and {len(barlines)} barlines")

def main():
    if len(sys.argv) < 3:
        print("Usage: python staff_barlines_extractor.py <musicxml_file> <full_svg_file>")
        print("Example: python staff_barlines_extractor.py 'Base/SS 9.musicxml' 'Base/SS 9 full.svg'")
        sys.exit(1)
    
    musicxml_file = sys.argv[1]
    full_svg_file = sys.argv[2]
    
    try:
        extract_staff_barlines(musicxml_file, full_svg_file)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()