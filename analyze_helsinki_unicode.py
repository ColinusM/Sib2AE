#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import svgelements
from svg_parser.core_parser import SVGParser
from svg_parser.element_classifier import MusicalElementClassifier

def analyze_helsinki_unicode():
    """Analyze all Helsinki Std Unicode characters to identify which are actual noteheads"""
    
    svg_file = "Base/Saint-Saens Trio No 2_0001.svg"
    
    parser = SVGParser()
    svg_data = parser.parse_svg(svg_file)
    all_elements = parser.extract_elements(svg_data)
    
    # Find all Helsinki Std text elements
    helsinki_elements = []
    for element in all_elements:
        if (type(element).__name__.lower() == 'text' and 
            hasattr(element, 'font_family') and 
            'helsinki std' in element.font_family.lower()):
            
            x = getattr(element, 'x', 0.0)
            y = getattr(element, 'y', 0.0)
            text = getattr(element, 'text', '')
            
            helsinki_elements.append({
                'x': x, 'y': y, 'text': text,
                'unicode_hex': f"U+{ord(text):04X}" if text else "N/A",
                'unicode_decimal': ord(text) if text else 0
            })
    
    print(f"=== ALL HELSINKI STD ELEMENTS ({len(helsinki_elements)}) ===")
    
    # Group by Unicode character
    unicode_groups = {}
    for elem in helsinki_elements:
        unicode_char = elem['unicode_hex']
        if unicode_char not in unicode_groups:
            unicode_groups[unicode_char] = []
        unicode_groups[unicode_char].append(elem)
    
    print(f"Unique Unicode characters found: {len(unicode_groups)}")
    
    for unicode_char, elements in sorted(unicode_groups.items()):
        print(f"\n{unicode_char}: {len(elements)} occurrences")
        print(f"  Character: {repr(elements[0]['text']) if elements[0]['text'] else 'N/A'}")
        
        # Show positions to understand musical context
        positions = [(e['x'], e['y']) for e in elements[:3]]  # First 3 positions
        print(f"  Positions: {positions}")
        
        # Analyze Y-coordinate distribution to guess element type
        y_coords = [e['y'] for e in elements]
        min_y, max_y = min(y_coords), max(y_coords)
        y_range = max_y - min_y
        
        if len(elements) == 1:
            print(f"  -> Likely: Single element (clef, key signature, or special symbol)")
        elif len(elements) >= 4 and y_range < 50:
            print(f"  -> Likely: NOTEHEADS (multiple elements in similar Y range)")
        elif y_range > 100:
            print(f"  -> Likely: Mixed elements across different staves")
        else:
            print(f"  -> Likely: Repeated symbols (articulations, dynamics)")
    
    print(f"\n=== ANALYSIS SUMMARY ===")
    print("Based on the user's knowledge that there are 4 flute + 6 violin = 10 noteheads:")
    print("Look for Unicode characters that appear ~4-6 times in similar Y ranges")

if __name__ == '__main__':
    analyze_helsinki_unicode()