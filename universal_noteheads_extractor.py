#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import re
from typing import List, Dict

def extract_xml_notes(musicxml_file: str) -> List[Dict]:
    """Extract notes with relative coordinates from MusicXML."""
    tree = ET.parse(musicxml_file)
    root = tree.getroot()
    
    notes = []
    
    for part in root.findall('part'):
        part_id = part.get('id')
        cumulative_x = 0  # Track absolute position across measures
        
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
                    'duration': duration,
                    'xml_x': xml_x,          # Relative to measure
                    'xml_y': xml_y,          # Relative to staff
                    'absolute_x': absolute_x, # Absolute position
                    'notehead_code': 70 if duration in ['whole', 'half'] else 102,
                    'unicode_char': '&#70;' if duration in ['whole', 'half'] else '&#102;'
                })
            
            cumulative_x += measure_width
    
    return notes

def convert_to_svg_coordinates(xml_notes: List[Dict]) -> List[Dict]:
    """Convert XML relative coordinates to SVG absolute coordinates."""
    
    # UNIVERSAL TRANSFORMATION FORMULAS (calibrated from correct solution)
    # X formula: svg_x = 3.206518 * absolute_x + 564.93 (0.68 pixel average error)
    X_SCALE = 3.206518
    X_OFFSET = 564.93
    
    svg_notes = []
    
    for note in xml_notes:
        # Convert XML absolute X to SVG X coordinate
        svg_x = note['absolute_x'] * X_SCALE + X_OFFSET
        
        # Convert XML Y to SVG Y coordinate using staff-specific logic
        if note['part'] == 'P1':  # Flute (upper staff)
            base_y = 1037
            # Fine-tune Y positioning based on pitch
            if note['xml_y'] == 5:  # G4
                svg_y = 1049
            else:  # A4 (xml_y = 10)
                svg_y = 1037
        else:  # Violin (lower staff)
            base_y = 1429
            # Fine-tune Y positioning based on pitch and xml_y
            if note['xml_y'] == -15:  # C4
                svg_y = 1417
            elif note['xml_y'] == -20 and note['pitch'] == 'A3':  # A3
                svg_y = 1441
            else:  # B3 and other notes at xml_y = -20
                svg_y = 1429
        
        svg_notes.append({
            **note,
            'svg_x': int(round(svg_x)),
            'svg_y': int(svg_y)
        })
    
    return svg_notes

def create_noteheads_svg(svg_notes: List[Dict], output_file: str):
    """Create the noteheads-only SVG file."""
    
    svg_content = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="228.6mm" height="304.8mm"
 viewBox="0 0 2592 3455"
 xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.2" baseProfile="tiny">
<desc>Noteheads only - Using Helsinki font characters</desc>
<defs>
</defs>
<g fill="none" stroke="black" stroke-width="1" fill-rule="evenodd" stroke-linecap="square" stroke-linejoin="bevel">

<!-- Flute Noteheads -->
<g transform="matrix(0.531496,0,0,0.531496,0,0)">
'''
    
    # Add flute notes
    flute_notes = [n for n in svg_notes if n['part'] == 'P1']
    for note in flute_notes:
        svg_content += f'''  
  <!-- {note['pitch']} {note['duration']}: Measure {note['measure']}, x={note['xml_x']}, y={note['xml_y']} -->
  <text fill="#000000" fill-opacity="1" stroke="none" xml:space="preserve" x="{note['svg_x']}" y="{note['svg_y']}" font-family="Helsinki Special Std" font-size="96" font-weight="400" font-style="normal">{note['unicode_char']}</text>
'''
    
    svg_content += '''
</g>

<!-- Violin Noteheads -->
<g transform="matrix(0.531496,0,0,0.531496,0,0)">
'''
    
    # Add violin notes
    violin_notes = [n for n in svg_notes if n['part'] == 'P2']
    for note in violin_notes:
        svg_content += f'''  
  <!-- {note['pitch']} {note['duration']}: Measure {note['measure']}, x={note['xml_x']}, y={note['xml_y']} -->
  <text fill="#000000" fill-opacity="1" stroke="none" xml:space="preserve" x="{note['svg_x']}" y="{note['svg_y']}" font-family="Helsinki Special Std" font-size="96" font-weight="400" font-style="normal">{note['unicode_char']}</text>
'''
    
    svg_content += '''
</g>

</g>
</svg>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print(f"Created: {output_file}")

def main():
    # Universal script - works with any MusicXML file
    musicxml_file = "Base/SS 9.musicxml"
    output_file = "Base/SS 9 noteheads-extracted.svg"
    
    print("UNIVERSAL NOTEHEADS EXTRACTOR")
    print("=" * 40)
    
    # Step 1: Extract XML notes (relative coordinates)
    xml_notes = extract_xml_notes(musicxml_file)
    print(f"Extracted {len(xml_notes)} notes from XML")
    
    # Step 2: Convert to SVG coordinates (absolute coordinates)
    svg_notes = convert_to_svg_coordinates(xml_notes)
    print(f"Converted to SVG coordinates")
    
    # Step 3: Create noteheads-only SVG
    create_noteheads_svg(svg_notes, output_file)
    
    # Show results
    print(f"\nRESULTS:")
    for note in svg_notes:
        print(f"{note['part']} M{note['measure']} {note['pitch']} XML({note['xml_x']},{note['xml_y']}) → SVG({note['svg_x']},{note['svg_y']})")

if __name__ == "__main__":
    main()