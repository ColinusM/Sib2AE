import cairosvg
import tempfile
import os
from typing import List, Optional
from models.musical_elements import MusicalElement, BoundingBox

class PNGGenerator:
    
    def __init__(self, dpi: float = 300.0):
        self.dpi = dpi
        self.temp_dir = None
    
    def generate_filtered_png(self, elements: List[MusicalElement], 
                            output_path: str, source_svg_path: str,
                            viewbox: Optional[BoundingBox] = None) -> bool:
        """Generate PNG containing only specified elements"""
        try:
            # Create filtered SVG with only the specified elements
            filtered_svg = self._create_filtered_svg(elements, source_svg_path, viewbox)
            
            # Convert to PNG using cairosvg
            cairosvg.svg2png(
                bytestring=filtered_svg.encode('utf-8'),
                write_to=output_path,
                dpi=self.dpi
            )
            
            return os.path.exists(output_path)
            
        except Exception as e:
            print(f"Error generating PNG {output_path}: {e}")
            return False
    
    def generate_individual_element_png(self, element: MusicalElement,
                                      output_path: str, source_svg_path: str,
                                      padding: float = 10.0) -> bool:
        """Generate PNG containing only a single element with minimal bounds"""
        try:
            # Calculate tight bounding box with padding
            bbox = element.transformed_bbox
            padded_viewbox = BoundingBox(
                x=bbox.x - padding,
                y=bbox.y - padding,
                width=bbox.width + 2 * padding,
                height=bbox.height + 2 * padding
            )
            
            # Generate PNG with tight cropping
            return self.generate_filtered_png([element], output_path, source_svg_path, padded_viewbox)
            
        except Exception as e:
            print(f"Error generating individual PNG {output_path}: {e}")
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
        
        # Create SVG element based on type
        if element.element_type == "notehead" and element.svg_path.startswith('M'):
            # Path element (notehead)
            return f'<g transform="{transform_str}"><path d="{element.svg_path}" fill="black" stroke="none"/></g>'
        
        elif element.element_type in ["stem", "staff_line"] and "points=" in element.svg_path:
            # Polyline element (stem, staff line)
            points = element.svg_path.replace('points="', '').replace('"', '')
            return f'<g transform="{transform_str}"><polyline {element.svg_path} fill="none" stroke="black" stroke-width="1"/></g>'
        
        elif element.element_type == "text":
            # Text element
            return f'<g transform="{transform_str}"><text>{element.svg_path}</text></g>'
        
        else:
            # Generic element - try to reconstruct from SVG path
            if element.svg_path.startswith('M') or element.svg_path.startswith('m'):
                return f'<g transform="{transform_str}"><path d="{element.svg_path}" fill="black" stroke="black" stroke-width="1"/></g>'
            else:
                # Fallback for other element types
                return f'<g transform="{transform_str}"><!-- {element.element_type}: {element.svg_path[:50]}... --></g>'
    
    def validate_png_properties(self, png_path: str) -> dict:
        """Validate PNG file properties using PIL"""
        try:
            from PIL import Image
            
            with Image.open(png_path) as img:
                return {
                    "exists": True,
                    "width": img.width,
                    "height": img.height,
                    "dpi": img.info.get('dpi', (self.dpi, self.dpi)),
                    "mode": img.mode,
                    "format": img.format
                }
        except Exception as e:
            return {
                "exists": False,
                "error": str(e)
            }
    
    def create_comparison_overlay(self, original_svg: str, generated_pngs: List[str],
                                output_path: str) -> bool:
        """Create overlay comparison for visual validation"""
        try:
            from PIL import Image
            
            # Convert original SVG to PNG for comparison
            temp_original = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            cairosvg.svg2png(url=original_svg, write_to=temp_original.name, dpi=self.dpi)
            
            # Open original image
            original_img = Image.open(temp_original.name)
            
            # Create overlay with generated elements
            overlay = Image.new('RGBA', original_img.size, (255, 255, 255, 0))
            
            for png_path in generated_pngs:
                if os.path.exists(png_path):
                    element_img = Image.open(png_path)
                    overlay.paste(element_img, (0, 0), element_img if element_img.mode == 'RGBA' else None)
            
            # Combine original and overlay
            combined = Image.alpha_composite(original_img.convert('RGBA'), overlay)
            combined.save(output_path, 'PNG')
            
            # Cleanup
            os.unlink(temp_original.name)
            
            return True
            
        except Exception as e:
            print(f"Error creating comparison overlay: {e}")
            return False
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)