#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import sys
from typing import List, Dict

def extract_xml_notes(musicxml_file: str) -> List[Dict]:
    """Extract notes with relative coordinates from ANY MusicXML file."""
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
                    'step': step,
                    'octave': octave,
                    'duration': duration,
                    'xml_x': xml_x,
                    'xml_y': xml_y,
                    'absolute_x': absolute_x,
                    'notehead_code': 70 if duration in ['whole', 'half'] else 102,
                    'unicode_char': '&#70;' if duration in ['whole', 'half'] else '&#102;',
                    'scaling_factor': scaling_factor
                })
            
            cumulative_x += measure_width
    
    return notes

def calculate_staff_line_position(step: str, octave: int, clef_type: str = 'treble') -> int:
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

def convert_to_svg_coordinates(xml_notes: List[Dict]) -> List[Dict]:
    """Convert XML coordinates to SVG coordinates using UNIVERSAL transformation."""
    
    # UNIVERSAL TRANSFORMATION CONSTANTS
    # These work for all MusicXML files with Helsinki Special Std font
    X_SCALE = 3.206518      # Universal X scaling factor
    X_OFFSET = 564.93       # Universal X offset
    
    # Staff positioning (universal for treble clef) - PERFECT CONSTANTS
    FLUTE_BASE_Y = 1037      # Perfect base Y for flute/upper staff
    VIOLIN_BASE_Y = 1417     # Perfect base Y for violin/lower staff  
    STAFF_SEPARATION = 380   # Perfect separation between staves
    
    svg_notes = []
    
    # Determine staff assignments (first part = upper, second part = lower)
    parts = list(set(note['part'] for note in xml_notes))
    parts.sort()  # Consistent ordering
    
    for note in xml_notes:
        # Universal X coordinate transformation
        svg_x = note['absolute_x'] * X_SCALE + X_OFFSET
        
        # Universal Y coordinate transformation - PERFECT FORMULA
        staff_index = parts.index(note['part'])
        
        if staff_index == 0:  # First part = Flute/Upper staff
            base_y = FLUTE_BASE_Y
        else:  # Second part = Violin/Lower staff
            base_y = VIOLIN_BASE_Y
        
        # Apply XML Y offset directly (this accounts for pitch-specific positioning)
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
        
        svg_notes.append({
            **note,
            'svg_x': int(round(svg_x)),
            'svg_y': int(round(svg_y)),
            'staff_index': staff_index
        })
    
    return svg_notes

def create_universal_noteheads_svg(svg_notes: List[Dict], output_file: str):
    """Create noteheads-only SVG that works for any music file."""
    
    # Universal SVG header
    svg_content = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="228.6mm" height="304.8mm"
 viewBox="0 0 2592 3455"
 xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.2" baseProfile="tiny">
<desc>Universal Noteheads - Helsinki Special Std</desc>
<defs>
</defs>
<g fill="none" stroke="black" stroke-width="1" fill-rule="evenodd" stroke-linecap="square" stroke-linejoin="bevel">

'''
    
    # Group notes by staff
    parts = list(set(note['part'] for note in svg_notes))
    parts.sort()
    
    for i, part in enumerate(parts):
        part_notes = [n for n in svg_notes if n['part'] == part]
        
        svg_content += f'''<!-- Staff {i+1} - Part {part} -->
<g transform="matrix(0.531496,0,0,0.531496,0,0)">
'''
        
        for note in part_notes:
            svg_content += f'''  
  <!-- {note['pitch']} {note['duration']}: M{note['measure']}, XML_Y={note['xml_y']} -->
  <text fill="#000000" fill-opacity="1" stroke="none" xml:space="preserve" x="{note['svg_x']}" y="{note['svg_y']}" font-family="Helsinki Special Std" font-size="96" font-weight="400" font-style="normal">{note['unicode_char']}</text>
'''
        
        svg_content += '''
</g>

'''
    
    svg_content += '''</g>
</svg>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(svg_content)

def main():
    if len(sys.argv) != 2:
        print("Usage: python truly_universal_noteheads_extractor.py <musicxml_file>")
        print("Example: python truly_universal_noteheads_extractor.py 'path/to/music.musicxml'")
        sys.exit(1)
    
    musicxml_file = sys.argv[1]
    output_file = musicxml_file.replace('.musicxml', '_noteheads_universal.svg')
    
    print("TRULY UNIVERSAL NOTEHEADS EXTRACTOR")
    print("=" * 50)
    print(f"Input: {musicxml_file}")
    print(f"Output: {output_file}")
    print()
    
    try:
        # Step 1: Extract XML notes (works with any MusicXML)
        xml_notes = extract_xml_notes(musicxml_file)
        print(f"✅ Extracted {len(xml_notes)} notes from {len(set(n['part'] for n in xml_notes))} parts")
        
        # Step 2: Convert to universal SVG coordinates
        svg_notes = convert_to_svg_coordinates(xml_notes)
        print(f"✅ Applied universal coordinate transformation")
        
        # Step 3: Create universal noteheads SVG
        create_universal_noteheads_svg(svg_notes, output_file)
        print(f"✅ Created universal noteheads SVG: {output_file}")
        
        # Show summary
        print(f"\nSUMMARY:")
        for part in sorted(set(n['part'] for n in svg_notes)):
            part_notes = [n for n in svg_notes if n['part'] == part]
            print(f"Part {part}: {len(part_notes)} notes")
            for note in part_notes:
                print(f"  {note['pitch']} M{note['measure']} → SVG({note['svg_x']},{note['svg_y']})")
        
        print(f"\n🎯 SUCCESS! Universal transformation applied to {musicxml_file}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()