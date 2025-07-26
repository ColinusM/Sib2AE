#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import svgelements
from svg_parser.core_parser import SVGParser
from svg_parser.element_classifier import MusicalElementClassifier

def analyze_noteheads():
    """Analyze Helsinki Std elements to identify actual noteheads vs symbols"""
    
    svg_file = "Base/Saint-Saens Trio No 2_0001.svg"
    
    parser = SVGParser()
    svg_data = parser.parse_svg(svg_file)
    all_elements = parser.extract_elements(svg_data)
    
    # Set up classifier
    classifier = MusicalElementClassifier()
    classifier.detect_instruments_from_elements(all_elements)
    
    print("=== HELSINKI STD ELEMENT ANALYSIS ===")
    print(f"Staff lines: {[f'{y:.1f}' for y in classifier.staff_lines]}")
    print(f"Flute range: {classifier.instrument_ranges['instrument_1']}")
    print(f"Violin range: {classifier.instrument_ranges['instrument_2']}")
    
    # Get all Helsinki Std text elements
    helsinki_texts = [e for e in all_elements if type(e).__name__.lower() == 'text' and 
                     hasattr(e, 'font_family') and 'helsinki std' in e.font_family.lower()]
    
    print(f"\nTotal Helsinki Std elements: {len(helsinki_texts)}")
    
    # Analyze each element
    candidates = []
    for i, element in enumerate(helsinki_texts):
        x = getattr(element, 'x', 0.0)
        y = getattr(element, 'y', 0.0)
        
        # Apply transformation
        transform = getattr(element, 'transform', None)
        if transform and hasattr(transform, 'd'):
            transformed_x = transform.a * x + transform.c * y + transform.e
            transformed_y = transform.b * x + transform.d * y + transform.f
        else:
            transformed_x, transformed_y = x, y
        
        # Determine instrument
        if 162 <= transformed_y <= 196:
            instrument = "flute"
        elif 213 <= transformed_y <= 247:
            instrument = "violin"
        else:
            instrument = "other"
        
        # Get Unicode character
        unicode_char = repr(element.text) if element.text else "empty"
        
        candidates.append({
            'index': i,
            'original_x': x,
            'original_y': y,
            'transformed_x': transformed_x,
            'transformed_y': transformed_y,
            'instrument': instrument,
            'unicode': unicode_char,
            'element': element
        })
    
    # Group by instrument
    flute_elements = [c for c in candidates if c['instrument'] == 'flute']
    violin_elements = [c for c in candidates if c['instrument'] == 'violin']
    other_elements = [c for c in candidates if c['instrument'] == 'other']
    
    print(f"\nFLUTE ELEMENTS ({len(flute_elements)}):")
    for elem in sorted(flute_elements, key=lambda x: x['transformed_x']):
        print(f"  X:{elem['transformed_x']:.1f} Y:{elem['transformed_y']:.1f} Unicode:{elem['unicode']}")
    
    print(f"\nVIOLIN ELEMENTS ({len(violin_elements)}):")
    for elem in sorted(violin_elements, key=lambda x: x['transformed_x']):
        print(f"  X:{elem['transformed_x']:.1f} Y:{elem['transformed_y']:.1f} Unicode:{elem['unicode']}")
    
    print(f"\nOTHER ELEMENTS ({len(other_elements)}):")
    for elem in sorted(other_elements, key=lambda x: x['transformed_x']):
        print(f"  X:{elem['transformed_x']:.1f} Y:{elem['transformed_y']:.1f} Unicode:{elem['unicode']}")
    
    # Analyze X-coordinate patterns for noteheads
    print(f"\n=== NOTEHEAD DETECTION LOGIC ===")
    
    def find_noteheads(elements, expected_count, instrument_name):
        print(f"\n{instrument_name.upper()} ANALYSIS:")
        
        # Group by X coordinate (notes at same time position)
        x_groups = {}
        for elem in elements:
            x_rounded = round(elem['transformed_x'], 0)  # Group by rounded X
            if x_rounded not in x_groups:
                x_groups[x_rounded] = []
            x_groups[x_rounded].append(elem)
        
        print(f"  X-coordinate groups: {len(x_groups)}")
        for x, group in sorted(x_groups.items()):
            y_values = [f"{e['transformed_y']:.1f}" for e in group]
            print(f"    X={x}: {len(group)} elements at Y={y_values}")
        
        # Strategy 1: Select unique X positions (most likely noteheads)
        unique_x_elements = []
        for x, group in sorted(x_groups.items()):
            if len(group) == 1:
                unique_x_elements.extend(group)
        
        print(f"  Unique X positions: {len(unique_x_elements)} elements")
        
        # Strategy 2: Select most spaced out elements if we need more
        all_x_sorted = sorted(elements, key=lambda x: x['transformed_x'])
        
        # Try to select expected_count elements with good spacing
        if len(unique_x_elements) >= expected_count:
            selected = unique_x_elements[:expected_count]
        else:
            # Add more elements, preferring those with different X coordinates
            selected = unique_x_elements[:]
            remaining_needed = expected_count - len(selected)
            
            used_x = set(round(e['transformed_x'], 0) for e in selected)
            for elem in all_x_sorted:
                if len(selected) >= expected_count:
                    break
                x_rounded = round(elem['transformed_x'], 0)
                if x_rounded not in used_x:
                    selected.append(elem)
                    used_x.add(x_rounded)
        
        print(f"  Selected {len(selected)} noteheads:")
        for elem in sorted(selected, key=lambda x: x['transformed_x']):
            print(f"    X:{elem['transformed_x']:.1f} Y:{elem['transformed_y']:.1f}")
        
        return selected
    
    # Find noteheads for each instrument
    flute_noteheads = find_noteheads(flute_elements, 4, "flute")
    violin_noteheads = find_noteheads(violin_elements, 6, "violin")
    
    print(f"\n=== FINAL RESULT ===")
    print(f"Flute noteheads found: {len(flute_noteheads)}")
    print(f"Violin noteheads found: {len(violin_noteheads)}")
    print(f"Total noteheads: {len(flute_noteheads) + len(violin_noteheads)}")

if __name__ == '__main__':
    analyze_noteheads()