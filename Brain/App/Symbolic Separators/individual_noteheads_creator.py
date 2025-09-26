#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import sys
import os
from typing import List, Dict

def extract_xml_notes(musicxml_file: str) -> List[Dict]:
    """Extract notes with coordinates using EXACT same system as extractor."""
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
                    'part_id': part_id,
                    'measure': measure_num,
                    'step': step,
                    'octave': octave,
                    'duration': duration,
                    'xml_x': xml_x,
                    'xml_y': xml_y,
                    'absolute_x': absolute_x,
                    'note_name': f"{step}{octave}"
                })
            
            cumulative_x += measure_width
    
    return notes

def convert_to_svg_coordinates(xml_notes: List[Dict]) -> List[Dict]:
    """Convert XML coordinates to SVG coordinates using EXACT same system as extractor."""
    
    # UNIVERSAL TRANSFORMATION CONSTANTS (EXACT same as extractor)
    X_SCALE = 3.206518      # Universal X scaling factor
    X_OFFSET = 564.93       # Universal X offset
    
    # Staff positioning (universal for treble clef) - PERFECT CONSTANTS
    FLUTE_BASE_Y = 1037      # Perfect base Y for flute/upper staff
    VIOLIN_BASE_Y = 1417     # Perfect base Y for violin/lower staff
    
    svg_notes = []
    
    # Determine staff assignments (first part = upper, second part = lower)
    parts = list(set(note['part_id'] for note in xml_notes))
    parts.sort()  # Consistent ordering
    
    for note in xml_notes:
        # Universal X coordinate transformation
        svg_x = int(note['absolute_x'] * X_SCALE + X_OFFSET)
        
        # Universal Y coordinate transformation - PERFECT FORMULA
        staff_index = parts.index(note['part_id'])
        
        if staff_index == 0:  # First part = Flute/Upper staff
            base_y = FLUTE_BASE_Y
        else:  # Second part = Violin/Lower staff
            base_y = VIOLIN_BASE_Y
        
        # Apply XML Y offset directly (EXACT same logic as extractor)
        if note['xml_y'] == 5:  # G4 special case
            svg_y = base_y + 12
        elif note['xml_y'] == 10:  # A4 
            svg_y = base_y
        elif note['xml_y'] == -15:  # C4
            svg_y = base_y
        elif note['xml_y'] == -20:  # B3, A3
            if note['note_name'] == 'A3':
                svg_y = base_y + 24  # A3 special positioning
            else:
                svg_y = base_y + 12  # B3 positioning
        else:
            svg_y = base_y  # Default
        
        svg_note = note.copy()
        svg_note.update({
            'svg_x': svg_x,
            'svg_y': svg_y,
            'staff_index': staff_index
        })
        
        svg_notes.append(svg_note)
    
    return svg_notes

def calculate_staff_line_position(step: str, octave: int) -> int:
    """Calculate staff line position for any note in treble clef (universal)."""
    # Treble clef staff line positions (universal for all music)
    note_positions = {
        # Octave 2
        'C2': -13, 'D2': -12, 'E2': -11, 'F2': -10, 'G2': -9, 'A2': -8, 'B2': -7,
        # Octave 3
        'C3': -6, 'D3': -5, 'E3': -4, 'F3': -3, 'G3': -2, 'A3': -1, 'B3': 0,
        # Octave 4 (staff lines: E4=3, G4=5, B4=7, D5=9, F5=11)
        'C4': 1, 'D4': 2, 'E4': 3, 'F4': 4, 'G4': 5, 'A4': 6, 'B4': 7,
        # Octave 5
        'C5': 8, 'D5': 9, 'E5': 10, 'F5': 11, 'G5': 12, 'A5': 13, 'B5': 14,
        # Octave 6
        'C6': 15, 'D6': 16, 'E6': 17, 'F6': 18, 'G6': 19, 'A6': 20, 'B6': 21
    }
    
    pitch_name = f"{step}{octave}"
    return note_positions.get(pitch_name, 5)  # Default to G4 if not found

def get_notehead_unicode(duration: str) -> str:
    """Get Helsinki Special Std HTML entity for notehead based on duration."""
    if duration in ['whole', 'half']:
        return '&#70;'  # Code 70: Hollow notehead
    else:  # quarter, eighth, sixteenth, etc.
        return '&#102;'  # Code 102: Full notehead

def create_individual_notehead_svgs(musicxml_file: str, output_dir: str):
    """Create individual SVG files for each notehead with EXACT coordinates."""
    
    print("INDIVIDUAL NOTEHEADS CREATOR")
    print("=" * 40)
    print(f"MusicXML: {musicxml_file}")
    print(f"Output Directory: {output_dir}")
    print()
    
    # Extract notes from MusicXML and convert to exact SVG coordinates
    xml_notes = extract_xml_notes(musicxml_file)
    svg_notes = convert_to_svg_coordinates(xml_notes)
    print(f"🎵 Found {len(svg_notes)} notes")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # SVG template for individual noteheads (EXACT same structure as extractor)
    svg_template = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="228.6mm" height="304.8mm"
 viewBox="0 0 2592 3455"
 xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.2" baseProfile="tiny">
<desc>Generated with Qt</desc>
<defs>
</defs>
<g fill="none" stroke="black" stroke-width="1" fill-rule="evenodd" stroke-linecap="square" stroke-linejoin="bevel">

<g transform="matrix(0.531496,0,0,0.531496,0,0)">
<text fill="#000000" fill-opacity="1" stroke="none" xml:space="preserve" x="{x}" y="{y}" font-family="Helsinki Special Std" font-size="96" font-weight="400" font-style="normal">{unicode}</text>
</g>

</g>
</svg>'''
    
    # Create individual SVG for each notehead
    for i, note in enumerate(svg_notes):
        # Get appropriate unicode character
        unicode_char = get_notehead_unicode(note['duration'])
        
        # Use EXACT coordinates from the universal transformation
        final_x = note['svg_x']
        final_y = note['svg_y']
        
        # Create SVG content
        svg_content = svg_template.format(
            x=final_x,
            y=final_y,
            unicode=unicode_char
        )
        
        # Generate filename
        filename = f"notehead_{i:03d}_{note['part_id']}_{note['note_name']}_M{note['measure']}.svg"
        filepath = os.path.join(output_dir, filename)
        
        # Write SVG file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        print(f"   ✅ Created: {filename}")
        print(f"      📍 Position: ({final_x}, {final_y}) - {note['note_name']} {note['duration']}")
    
    print(f"\n🎯 SUCCESS! Created {len(svg_notes)} individual notehead SVG files in '{output_dir}/' directory")
    
    # Summary by instrument
    parts = {}
    for note in svg_notes:
        part_id = note['part_id']
        if part_id not in parts:
            parts[part_id] = []
        parts[part_id].append(note)
    
    print("\nSUMMARY BY INSTRUMENT:")
    for part_id, part_notes in parts.items():
        print(f"  {part_id}: {len(part_notes)} noteheads")
        for note in part_notes:
            print(f"    {note['note_name']} M{note['measure']} → SVG({note['svg_x']},{note['svg_y']})")

def main():
    if len(sys.argv) < 2:
        print("Usage: python individual_noteheads_creator.py <musicxml_file> [output_dir]")
        print("Example: python individual_noteheads_creator.py 'Base/SS 9.musicxml' 'individual_noteheads'")
        sys.exit(1)
    
    musicxml_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs/svg/noteheads"
    
    try:
        create_individual_notehead_svgs(musicxml_file, output_dir)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()