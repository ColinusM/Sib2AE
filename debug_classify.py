#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import svgelements
from svg_parser.core_parser import SVGParser
from svg_parser.element_classifier import MusicalElementClassifier

def debug_classification():
    """Debug why only 4 Helsinki Std elements are classified as noteheads"""
    
    svg_file = "Base/Saint-Saens Trio No 2_0001.svg"
    
    parser = SVGParser()
    svg_data = parser.parse_svg(svg_file)
    all_elements = parser.extract_elements(svg_data)
    
    # Set up classifier
    classifier = MusicalElementClassifier()
    classifier.detect_instruments_from_elements(all_elements)
    
    print("=== INSTRUMENT RANGES ===")
    print(f"Staff lines: {classifier.staff_lines}")
    print(f"Instrument ranges: {classifier.instrument_ranges}")
    
    print("\n=== HELSINKI STD CLASSIFICATION ===")
    
    # Check all Helsinki Std text elements
    helsinki_texts = [e for e in all_elements if type(e).__name__.lower() == 'text' and 
                     hasattr(e, 'font_family') and 'helsinki std' in e.font_family.lower()]
    
    noteheads_found = 0
    for i, element in enumerate(helsinki_texts):
        x = getattr(element, 'x', 0.0)
        y = getattr(element, 'y', 0.0)
        
        # Get transformed coordinates (same as core_parser.py)
        transform = getattr(element, 'transform', None)
        if transform and hasattr(transform, 'd'):
            transformed_x = transform.a * x + transform.c * y + transform.e
            transformed_y = transform.b * x + transform.d * y + transform.f
        else:
            transformed_x, transformed_y = x, y
        
        # Create BoundingBox for classification
        from models.musical_elements import BoundingBox
        bbox = BoundingBox(x=transformed_x, y=transformed_y, width=10.0, height=10.0)
        
        # Manually test classification logic
        element_type = classifier._determine_element_type(element, bbox)
        
        print(f"\nHelsinki Text {i+1}:")
        print(f"  Original: x={x}, y={y}")
        print(f"  Transformed: x={transformed_x:.1f}, y={transformed_y:.1f}")
        print(f"  Text: '{element.text}'")
        print(f"  Classification: {element_type}")
        
        if element_type == "notehead":
            noteheads_found += 1
            
        # Debug the _is_notehead_text_position logic
        if hasattr(element, 'font_family') and 'helsinki std' in element.font_family.lower():
            center_y = bbox.y + bbox.height / 2
            
            # Check staff line proximity
            if classifier.staff_lines:
                # Calculate staff line spacing
                if len(classifier.staff_lines) >= 2:
                    spacings = [classifier.staff_lines[i+1] - classifier.staff_lines[i] 
                              for i in range(len(classifier.staff_lines)-1)]
                    staff_line_spacing = sorted(spacings)[len(spacings)//2]
                else:
                    staff_line_spacing = 24
                
                tolerance = staff_line_spacing * 0.3
                
                is_on_staff_line = any(abs(center_y - staff_y) < tolerance 
                                     for staff_y in classifier.staff_lines)
                
                in_any_instrument_range = any(
                    min_y <= center_y <= max_y 
                    for min_y, max_y in classifier.instrument_ranges.values()
                )
                
                print(f"  Center Y: {center_y:.1f}")
                print(f"  Staff line spacing: {staff_line_spacing:.1f}, tolerance: {tolerance:.1f}")
                print(f"  On staff line: {is_on_staff_line}")
                print(f"  In instrument range: {in_any_instrument_range}")
                
                # Check distance to each staff line
                closest_staff_distance = min(abs(center_y - staff_y) for staff_y in classifier.staff_lines)
                print(f"  Closest staff line distance: {closest_staff_distance:.1f}")
    
    print(f"\nTotal noteheads found: {noteheads_found} / {len(helsinki_texts)}")

if __name__ == '__main__':
    debug_classification()