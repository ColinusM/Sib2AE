#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import svgelements
from svg_parser.core_parser import SVGParser

def debug_elements():
    """Debug SVG elements to understand structure"""
    
    svg_file = "Base/Saint-Saens Trio No 2_0001.svg"
    
    parser = SVGParser()
    svg_data = parser.parse_svg(svg_file)
    all_elements = parser.extract_elements(svg_data)
    
    print(f"Total elements: {len(all_elements)}")
    
    # Check text elements specifically
    text_elements = [e for e in all_elements if type(e).__name__.lower() == 'text']
    print(f"Text elements found: {len(text_elements)}")
    
    for i, element in enumerate(text_elements[:10]):  # First 10 text elements
        print(f"\n--- Text Element {i+1} ---")
        print(f"Type: {type(element).__name__}")
        print(f"Dir: {[attr for attr in dir(element) if not attr.startswith('_')]}")
        
        # Check various font family attributes
        font_attrs = ['font_family', 'font-family', 'fontFamily']
        for attr in font_attrs:
            if hasattr(element, attr):
                print(f"{attr}: {getattr(element, attr)}")
        
        # Check if it's in the values dict
        if hasattr(element, 'values'):
            print(f"Values: {element.values}")
            
        # Check specific coordinates
        bbox = parser.extract_bounding_box(element)
        transform = parser.extract_transform_matrix(element)
        print(f"BBox: x={bbox.x}, y={bbox.y}, w={bbox.width}, h={bbox.height}")
        print(f"Transform: a={transform.a}, d={transform.d}, e={transform.e}, f={transform.f}")
        
        # Check text content
        if hasattr(element, 'text'):
            print(f"Text content: '{element.text}'")

if __name__ == '__main__':
    debug_elements()