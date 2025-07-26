#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import svgelements
from svg_parser.core_parser import SVGParser
from svg_parser.element_classifier import MusicalElementClassifier
from svg_parser.coordinate_extractor import CoordinateExtractor

def debug_svg_elements():
    """Debug what data we have in MusicalElement objects for SVG reconstruction"""
    
    svg_file = "Base/Saint-Saens Trio No 2_0001.svg"
    
    parser = SVGParser()
    svg_data = parser.parse_svg(svg_file)
    all_svg_elements = parser.extract_elements(svg_data)
    
    # Set up classifier
    classifier = MusicalElementClassifier()
    classifier.detect_instruments_from_elements(all_svg_elements)
    
    # Classify elements
    classified_elements = []
    for svg_element in all_svg_elements:
        bbox = parser.extract_bounding_box(svg_element)
        transform = parser.extract_transform_matrix(svg_element)
        musical_element = classifier.classify_element(svg_element, bbox, transform)
        classified_elements.append(musical_element)
    
    # Apply coordinate extraction
    coord_extractor = CoordinateExtractor()
    for i, (element, svg_element) in enumerate(zip(classified_elements, all_svg_elements)):
        element.transformed_bbox = coord_extractor.extract_coordinates(element, svg_element)
    
    # Filter noteheads
    classified_elements = classifier.filter_noteheads_by_position(classified_elements)
    
    # Find noteheads and examine their data
    noteheads = [e for e in classified_elements if e.element_type == "notehead"]
    
    print(f"=== NOTEHEAD SVG DATA ANALYSIS ({len(noteheads)} noteheads) ===")
    
    for i, notehead in enumerate(noteheads[:3]):  # First 3 noteheads
        print(f"\nNotehead {i+1}:")
        print(f"  ID: {notehead.element_id}")
        print(f"  Type: {notehead.element_type}")
        print(f"  Instrument: {notehead.instrument}")
        print(f"  SVG Path: {repr(notehead.svg_path[:100])}...")
        print(f"  Transform: a={notehead.transform_matrix.a}, d={notehead.transform_matrix.d}")
        print(f"  Original bbox: x={notehead.original_bbox.x}, y={notehead.original_bbox.y}")
        print(f"  Transformed bbox: x={notehead.transformed_bbox.x}, y={notehead.transformed_bbox.y}")
        
        # Check if we can find the original SVG element
        matching_svg_elements = []
        for svg_elem in all_svg_elements:
            if (type(svg_elem).__name__.lower() == 'text' and 
                hasattr(svg_elem, 'font_family') and 
                'helsinki std' in svg_elem.font_family.lower()):
                matching_svg_elements.append(svg_elem)
        
        if matching_svg_elements and i < len(matching_svg_elements):
            svg_elem = matching_svg_elements[i]
            print(f"  Original SVG element:")
            print(f"    Type: {type(svg_elem).__name__}")
            print(f"    X: {getattr(svg_elem, 'x', 'N/A')}")
            print(f"    Y: {getattr(svg_elem, 'y', 'N/A')}")
            print(f"    Text: {repr(getattr(svg_elem, 'text', 'N/A'))}")
            print(f"    Font family: {getattr(svg_elem, 'font_family', 'N/A')}")
            print(f"    Font size: {getattr(svg_elem, 'font_size', 'N/A')}")

if __name__ == '__main__':
    debug_svg_elements()