#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

import svgelements
from svg_parser.core_parser import SVGParser

def debug_staff_lines():
    """Debug why staff lines aren't being detected"""
    
    svg_file = "Base/Saint-Saens Trio No 2_0001.svg"
    
    parser = SVGParser()
    svg_data = parser.parse_svg(svg_file)
    all_elements = parser.extract_elements(svg_data)
    
    print("=== ALL POLYLINE ANALYSIS ===")
    
    # Check ALL polyline elements
    polylines = [e for e in all_elements if type(e).__name__.lower() == 'polyline']
    print(f"Total polyline elements: {len(polylines)}")
    
    staff_candidates = []
    for i, element in enumerate(polylines):
        if hasattr(element, 'points'):
            points = element.points
            if len(points) >= 2:
                y1, y2 = points[0][1], points[-1][1]
                x1, x2 = points[0][0], points[-1][0]
                width = abs(x2 - x1)
                height = abs(y2 - y1)
                
                is_horizontal = height < width * 0.1
                is_long = width > 1000
                
                if is_long:  # Show all long lines
                    print(f"\nPolyline {i+1}: points={points[0]} to {points[-1]}")
                    print(f"  Width: {width}, Height: {height}")
                    print(f"  Is horizontal: {is_horizontal}, Is long: {is_long}")
                    
                    if is_horizontal:
                        transform = getattr(element, 'transform', None)
                        if transform:
                            print(f"  Transform: a={transform.a}, d={transform.d}, e={transform.e}, f={transform.f}")
                            visual_y = transform.b * x1 + transform.d * y1 + transform.f
                            print(f"  Transformed Y: {visual_y}")
                            staff_candidates.append(visual_y)
                        else:
                            print(f"  No transform, raw Y: {y1}")
                            staff_candidates.append(y1)
    
    print(f"\nStaff line candidates: {sorted(staff_candidates)}")

if __name__ == '__main__':
    debug_staff_lines()