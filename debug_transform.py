#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import svgelements
from svg_parser.core_parser import SVGParser

def debug_transforms():
    """Debug transformation matrices to understand coordinate calculations"""
    
    svg_file = "Base/Saint-Saens Trio No 2_0001.svg"
    
    parser = SVGParser()
    svg_data = parser.parse_svg(svg_file)
    all_elements = parser.extract_elements(svg_data)
    
    print("=== STAFF LINE ANALYSIS ===")
    
    # Check polyline elements (staff lines)
    polylines = [e for e in all_elements if type(e).__name__.lower() == 'polyline']
    print(f"Polyline elements found: {len(polylines)}")
    
    staff_lines = []
    for i, element in enumerate(polylines[:5]):  # First 5 polylines
        if hasattr(element, 'points'):
            points = element.points
            if len(points) >= 2:
                y1, y2 = points[0][1], points[-1][1]
                x1, x2 = points[0][0], points[-1][0]
                width = abs(x2 - x1)
                height = abs(y2 - y1)
                
                print(f"\n--- Polyline {i+1} ---")
                print(f"Points: {points[:2]}...{points[-2:]}")
                print(f"Raw: x1={x1}, y1={y1}, width={width}, height={height}")
                
                is_horizontal = height < width * 0.1
                is_long = width > 1000
                print(f"Is horizontal: {is_horizontal}, Is long: {is_long}")
                
                if is_horizontal and is_long:
                    transform = getattr(element, 'transform', None)
                    if transform:
                        print(f"Transform: a={transform.a}, b={transform.b}, c={transform.c}, d={transform.d}, e={transform.e}, f={transform.f}")
                        
                        # Old method (just scaling)
                        old_y = transform.d * y1 + transform.f
                        # New method (full transform)
                        new_y = transform.b * x1 + transform.d * y1 + transform.f
                        
                        print(f"Old transform Y: {old_y}")
                        print(f"New transform Y: {new_y}")
                        
                        staff_lines.append(new_y)
    
    print(f"\nFinal staff lines: {sorted(staff_lines)}")
    
    print("\n=== HELSINKI STD TEXT ANALYSIS ===")
    
    # Check Helsinki Std text elements
    helsinki_texts = [e for e in all_elements if type(e).__name__.lower() == 'text' and 
                     hasattr(e, 'font_family') and 'helsinki std' in e.font_family.lower()]
    print(f"Helsinki Std text elements found: {len(helsinki_texts)}")
    
    for i, element in enumerate(helsinki_texts[:10]):  # First 10
        x = getattr(element, 'x', 0.0)
        y = getattr(element, 'y', 0.0)
        
        print(f"\n--- Helsinki Text {i+1} ---")
        print(f"Original: x={x}, y={y}")
        print(f"Text content: '{element.text}'")
        
        transform = getattr(element, 'transform', None)
        if transform:
            print(f"Transform: a={transform.a}, b={transform.b}, c={transform.c}, d={transform.d}, e={transform.e}, f={transform.f}")
            
            # Apply transformation
            transformed_x = transform.a * x + transform.c * y + transform.e
            transformed_y = transform.b * x + transform.d * y + transform.f
            
            print(f"Transformed: x={transformed_x}, y={transformed_y}")
            
            # Check if in staff ranges
            staff_ranges = [
                (162.09586886489365, 196.11163123336138),  # instrument_1
                (213.11951241759527, 247.135274786063)     # instrument_2
            ]
            
            for j, (min_y, max_y) in enumerate(staff_ranges):
                if min_y <= transformed_y <= max_y:
                    print(f"  -> IN INSTRUMENT {j+1} RANGE!")
                    break
            else:
                print(f"  -> NOT in any instrument range")

if __name__ == '__main__':
    debug_transforms()