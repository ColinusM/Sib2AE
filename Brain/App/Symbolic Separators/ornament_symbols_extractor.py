#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import sys
import os
import argparse
from pathlib import Path
from typing import List, Dict, Optional

def extract_ornament_symbols(svg_file: str, output_dir: str):
    """
    Extract ornament symbols (trills, mordents, etc.) from SVG as individual files.
    Similar to individual_noteheads_creator.py but for ornament symbols.
    """
    
    print("ORNAMENT SYMBOLS EXTRACTOR")
    print("=" * 40)
    print(f"Input SVG: {svg_file}")
    print(f"Output Directory: {output_dir}")
    print()
    
    # Parse SVG
    tree = ET.parse(svg_file)
    root = tree.getroot()
    
    # Known ornament Unicode mappings
    ORNAMENT_SYMBOLS = {
        0xF0D9: 'trill_start',
        0xF07E: 'trill_wavy',
        0xF04D: 'mordent',
        0xF04E: 'inverted_mordent',
        0xF04A: 'staccato',
        0xF06A: 'accent',
        0xF04F: 'turn',
        0xF050: 'inverted_turn',
    }
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # SVG template for individual symbols
    svg_template = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="228.6mm" height="304.8mm"
 viewBox="0 0 2592 3455"
 xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.2" baseProfile="tiny">
<desc>{description}</desc>
<g fill="none" stroke="black" stroke-width="1" fill-rule="evenodd" stroke-linecap="square" stroke-linejoin="bevel">
<g transform="matrix(0.531496,0,0,0.531496,0,0)">
<text fill="#000000" fill-opacity="1" stroke="none" xml:space="preserve" x="{x}" y="{y}" font-family="{font_family}" font-size="{font_size}" font-weight="400" font-style="normal">{unicode_char}</text>
</g>
</g>
</svg>'''
    
    # Find and extract ornament symbols
    ornaments_found = {}
    
    for elem in root.iter():
        if elem.tag.endswith('text') and elem.text:
            char = elem.text.strip()
            if not char:
                continue
            
            unicode_code = ord(char[0])
            
            # Check if this is an ornament symbol
            if unicode_code in ORNAMENT_SYMBOLS:
                ornament_type = ORNAMENT_SYMBOLS[unicode_code]
                
                # Get element properties
                x = elem.get('x', '0')
                y = elem.get('y', '0')
                font_family = elem.get('font-family', 'Helsinki Std')
                font_size = elem.get('font-size', '96')
                
                # Track ornament
                if ornament_type not in ornaments_found:
                    ornaments_found[ornament_type] = []
                
                ornaments_found[ornament_type].append({
                    'unicode_code': unicode_code,
                    'char': char,
                    'x': x,
                    'y': y,
                    'font_family': font_family,
                    'font_size': font_size
                })
    
    if not ornaments_found:
        print("❌ No ornament symbols found in SVG")
        print("   SVG may not contain text-based ornaments")
        return
    
    # Create individual SVG files for each ornament
    total_count = 0
    
    for ornament_type, instances in ornaments_found.items():
        print(f"\n🎵 {ornament_type.replace('_', ' ').title()}: {len(instances)} instance(s)")
        
        for i, ornament in enumerate(instances):
            # Create filename
            filename = f"{ornament_type}_{i:03d}_U+{ornament['unicode_code']:04X}.svg"
            filepath = os.path.join(output_dir, filename)
            
            # Create SVG content
            description = f"{ornament_type.replace('_', ' ').title()} - U+{ornament['unicode_code']:04X} (decimal {ornament['unicode_code']})"
            
            svg_content = svg_template.format(
                description=description,
                x=ornament['x'],
                y=ornament['y'],
                font_family=ornament['font_family'],
                font_size=ornament['font_size'],
                unicode_char=ornament['char']
            )
            
            # Write SVG file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            print(f"   ✅ Created: {filename}")
            print(f"      Position: ({ornament['x']}, {ornament['y']})")
            print(f"      Font: {ornament['font_family']}, Size: {ornament['font_size']}")
            
            total_count += 1
    
    print(f"\n🎯 SUCCESS! Extracted {total_count} ornament symbol(s) to '{output_dir}/'")
    
    # Summary by type
    print("\nSUMMARY BY ORNAMENT TYPE:")
    for ornament_type, instances in ornaments_found.items():
        print(f"  {ornament_type.replace('_', ' ').title()}: {len(instances)} symbol(s)")


def main():
    parser = argparse.ArgumentParser(
        description="Extract ornament symbols from SVG as individual files"
    )
    parser.add_argument(
        "svg_file",
        help="SVG file to process"
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="outputs/svg/ornaments",
        help="Output directory for ornament SVG files (default: outputs/svg/ornaments)"
    )
    args = parser.parse_args()
    
    try:
        extract_ornament_symbols(args.svg_file, args.output_dir)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
