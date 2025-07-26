import os
import tempfile
from typing import List, Optional
from pathlib import Path
from models.musical_elements import MusicalElement, BoundingBox

class SVGGenerator:
    
    def __init__(self):
        self.temp_dir = None
    
    def generate_filtered_svg(self, elements: List[MusicalElement], 
                            output_path: str, source_svg_path: str,
                            viewbox: Optional[BoundingBox] = None) -> bool:
        """Generate SVG containing only specified elements"""
        try:
            # Create filtered SVG with only the specified elements
            filtered_svg = self._create_filtered_svg(elements, source_svg_path, viewbox)
            
            # Write SVG to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(filtered_svg)
            
            return os.path.exists(output_path)
            
        except Exception as e:
            print(f"Error generating SVG {output_path}: {e}")
            return False
    
    def generate_individual_element_svg(self, element: MusicalElement,
                                      output_path: str, source_svg_path: str,
                                      padding: float = 10.0) -> bool:
        """Generate SVG containing only a single element with minimal bounds"""
        try:
            # Calculate tight bounding box with padding
            bbox = element.transformed_bbox
            padded_viewbox = BoundingBox(
                x=bbox.x - padding,
                y=bbox.y - padding,
                width=bbox.width + 2 * padding,
                height=bbox.height + 2 * padding
            )
            
            # Generate SVG with tight cropping
            return self.generate_filtered_svg([element], output_path, source_svg_path, padded_viewbox)
            
        except Exception as e:
            print(f"Error generating individual SVG {output_path}: {e}")
            return False
    
    def _create_filtered_svg(self, elements: List[MusicalElement], 
                           source_svg_path: str, viewbox: Optional[BoundingBox] = None) -> str:
        """Create SVG containing only specified elements"""
        
        # Read the original SVG to extract header and structure
        with open(source_svg_path, 'r', encoding='utf-8') as f:
            original_svg = f.read()
        
        # Extract SVG header (up to first <g> element)
        header_end = original_svg.find('<g')
        if header_end == -1:
            header_end = original_svg.find('>')
        svg_header = original_svg[:header_end]
        
        # Modify viewBox if specified
        if viewbox:
            svg_header = self._update_viewbox(svg_header, viewbox)
        
        # Create element content based on element types and paths
        element_content = ""
        for element in elements:
            element_svg = self._create_element_svg(element)
            if element_svg:
                element_content += element_svg + "\n"
        
        # Combine into complete SVG
        filtered_svg = f"{svg_header}>\n{element_content}</svg>"
        
        return filtered_svg
    
    def _update_viewbox(self, svg_header: str, viewbox: BoundingBox) -> str:
        """Update viewBox attribute in SVG header"""
        import re
        
        viewbox_str = f"{viewbox.x} {viewbox.y} {viewbox.width} {viewbox.height}"
        
        # Replace existing viewBox
        pattern = r'viewBox="[^"]*"'
        if re.search(pattern, svg_header):
            svg_header = re.sub(pattern, f'viewBox="{viewbox_str}"', svg_header)
        else:
            # Add viewBox if it doesn't exist
            svg_header = svg_header.replace('<svg', f'<svg viewBox="{viewbox_str}"')
        
        return svg_header
    
    def _create_element_svg(self, element: MusicalElement) -> str:
        """Create SVG representation of a single musical element"""
        
        # Extract transformation matrix
        transform = element.transform_matrix
        transform_str = f"matrix({transform.a},{transform.b},{transform.c},{transform.d},{transform.e},{transform.f})"
        
        # Handle different element types
        if element.element_type in ["notehead", "clef", "text"]:
            # Text elements (Helsinki Std symbols, regular text)
            return self._create_text_element_svg(element, transform_str)
        
        elif element.element_type in ["stem", "staff_line"] and "points=" in element.svg_path:
            # Polyline element (stem, staff line)
            return f'<g transform="{transform_str}"><polyline {element.svg_path} fill="none" stroke="black" stroke-width="1"/></g>'
        
        elif element.element_type == "notehead" and element.svg_path.startswith('M'):
            # Path element (notehead)
            return f'<g transform="{transform_str}"><path d="{element.svg_path}" fill="black" stroke="none"/></g>'
        
        else:
            # Generic element - try to reconstruct from SVG path
            if element.svg_path.startswith('M') or element.svg_path.startswith('m'):
                return f'<g transform="{transform_str}"><path d="{element.svg_path}" fill="black" stroke="black" stroke-width="1"/></g>'
            else:
                # Skip elements we can't properly reconstruct
                return ""
    
    def _create_text_element_svg(self, element: MusicalElement, transform_str: str) -> str:
        """Create SVG text element from MusicalElement"""
        
        # Extract text content and properties from svg_path
        svg_path = element.svg_path
        
        # Parse the Text object representation to extract coordinates and text content
        if "Text(" in svg_path:
            # Extract Unicode character (first parameter in quotes)
            import re
            text_match = re.search(r"Text\('([^']*)'", svg_path)
            text_content = text_match.group(1) if text_match else ""
            
            # Extract font properties
            font_family_match = re.search(r"font-family='([^']*)'", svg_path)
            font_family = font_family_match.group(1) if font_family_match else "Helsinki Std"
            
            font_size_match = re.search(r"font-size='([^']*)'", svg_path)
            if font_size_match:
                font_size = font_size_match.group(1)
            else:
                # Default font size for Helsinki Std elements
                font_size = "96" if "Helsinki" in font_family else "12"
            
            # For text elements, we need to extract original coordinates
            # The transformed coordinates are stored in the bbox, but we need original
            # Use reverse transformation to get original coordinates
            bbox = element.transformed_bbox
            transform = element.transform_matrix
            
            # Simple reverse transformation (assuming no rotation/skew for now)
            if transform.a != 0:
                original_x = (bbox.x - transform.e) / transform.a
                original_y = (bbox.y - transform.f) / transform.d
            else:
                original_x = bbox.x
                original_y = bbox.y
            
            # Create proper SVG text element with XML-encoded Unicode
            # Convert Unicode character to XML entity for proper SVG rendering
            if text_content:
                # Convert Unicode to XML entity (e.g., \uf026 -> &#xf026;)
                if len(text_content) == 1 and ord(text_content) > 127:
                    xml_text = f"&#x{ord(text_content):04x};"
                else:
                    xml_text = text_content
            else:
                xml_text = ""
            
            return f'''<g transform="{transform_str}">
    <text x="{original_x}" y="{original_y}" font-family="{font_family}" font-size="{font_size}" fill="black">{xml_text}</text>
</g>'''
        else:
            # Fallback for non-text elements
            return f'<g transform="{transform_str}"><!-- {element.element_type}: {svg_path[:50]}... --></g>'
    
    def _get_inverse_transform(self, transform):
        """Calculate inverse transformation matrix (simplified)"""
        # For now, return identity - this would need proper matrix inversion
        from models.musical_elements import TransformMatrix
        return TransformMatrix(a=1.0, b=0.0, c=0.0, d=1.0, e=0.0, f=0.0)
    
    def validate_svg_properties(self, svg_path: str) -> dict:
        """Validate SVG file properties"""
        try:
            return {
                "exists": os.path.exists(svg_path),
                "size_bytes": os.path.getsize(svg_path) if os.path.exists(svg_path) else 0,
                "valid_xml": self._is_valid_xml(svg_path) if os.path.exists(svg_path) else False
            }
        except Exception as e:
            return {
                "exists": False,
                "error": str(e)
            }
    
    def _is_valid_xml(self, svg_path: str) -> bool:
        """Check if SVG file is valid XML"""
        try:
            import xml.etree.ElementTree as ET
            ET.parse(svg_path)
            return True
        except ET.ParseError:
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)