import svgelements
from typing import List, Dict, Any, Optional
from pathlib import Path
from models.coordinate_system import CoordinateSystem
from models.musical_elements import TransformMatrix, BoundingBox

class SVGParser:
    def __init__(self):
        self.svg_data: Optional[svgelements.SVG] = None
        self.coordinate_system: Optional[CoordinateSystem] = None
    
    def parse_svg(self, file_path: str) -> svgelements.SVG:
        """Parse SVG file and return SVG object with elements"""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"SVG file not found: {file_path}")
        
        try:
            self.svg_data = svgelements.SVG.parse(file_path, reify=False)
            self.coordinate_system = self._extract_coordinate_system()
            return self.svg_data
        except Exception as e:
            raise ValueError(f"Failed to parse SVG file: {e}")
    
    def extract_elements(self, svg_data: svgelements.SVG) -> List[svgelements.SVGElement]:
        """Extract all elements from SVG data"""
        elements = []
        for element in svg_data.elements():
            # Skip the root SVG element and desc elements
            element_type = type(element).__name__.lower()
            if element_type not in ['svg', 'desc', 'defs']:
                elements.append(element)
        return elements
    
    def _extract_coordinate_system(self) -> CoordinateSystem:
        """Extract coordinate system information from SVG"""
        if not self.svg_data:
            raise ValueError("No SVG data loaded")
        
        # Extract viewBox
        viewbox = self.svg_data.viewbox
        if viewbox and hasattr(viewbox, '__iter__') and len(viewbox) >= 4:
            vb_x, vb_y, vb_width, vb_height = viewbox[:4]
        elif hasattr(viewbox, 'x') and hasattr(viewbox, 'y') and hasattr(viewbox, 'width') and hasattr(viewbox, 'height'):
            vb_x, vb_y, vb_width, vb_height = viewbox.x, viewbox.y, viewbox.width, viewbox.height
        else:
            vb_x = vb_y = 0
            vb_width = float(self.svg_data.width or 0)
            vb_height = float(self.svg_data.height or 0)
        
        # Extract document dimensions
        doc_width = float(self.svg_data.width or vb_width)
        doc_height = float(self.svg_data.height or vb_height)
        
        return CoordinateSystem(
            viewbox_x=vb_x,
            viewbox_y=vb_y,
            viewbox_width=vb_width,
            viewbox_height=vb_height,
            document_width=doc_width,
            document_height=doc_height
        )
    
    def extract_transform_matrix(self, element: svgelements.SVGElement) -> TransformMatrix:
        """Extract transformation matrix from SVG element"""
        if hasattr(element, 'transform') and element.transform:
            matrix = element.transform
            return TransformMatrix(
                a=matrix.a, b=matrix.b, c=matrix.c,
                d=matrix.d, e=matrix.e, f=matrix.f
            )
        else:
            # Identity matrix
            return TransformMatrix(a=1.0, b=0.0, c=0.0, d=1.0, e=0.0, f=0.0)
    
    def extract_bounding_box(self, element: svgelements.SVGElement) -> BoundingBox:
        """Extract bounding box from SVG element with transformation applied"""
        
        # For text elements, use x,y coordinates directly since bbox() may not work correctly
        if hasattr(element, 'x') and hasattr(element, 'y') and type(element).__name__.lower() == 'text':
            # Get text element coordinates directly
            x = getattr(element, 'x', 0.0)
            y = getattr(element, 'y', 0.0)
            
            # Apply transformation matrix if element has one
            transform = getattr(element, 'transform', None)
            if transform and hasattr(transform, 'd'):  # Has scaling
                # Apply same transformation as staff line detection
                transformed_x = transform.a * x + transform.c * y + transform.e
                transformed_y = transform.b * x + transform.d * y + transform.f
                
                return BoundingBox(
                    x=transformed_x, y=transformed_y,
                    width=10.0, height=10.0  # Small default size for text
                )
            else:
                return BoundingBox(x=x, y=y, width=10.0, height=10.0)
        
        # For other elements, use existing bbox logic
        elif hasattr(element, 'bbox') and element.bbox():
            bbox = element.bbox()
            raw_bbox = BoundingBox(
                x=bbox[0], y=bbox[1],
                width=bbox[2] - bbox[0],
                height=bbox[3] - bbox[1]
            )
            
            # Apply transformation matrix if element has one
            transform_matrix = self.extract_transform_matrix(element)
            if transform_matrix.a != 1.0 or transform_matrix.d != 1.0 or transform_matrix.e != 0.0 or transform_matrix.f != 0.0:
                # Transform the bounding box coordinates
                # Apply matrix transformation: x' = a*x + c*y + e, y' = b*x + d*y + f
                transformed_x = transform_matrix.a * raw_bbox.x + transform_matrix.c * raw_bbox.y + transform_matrix.e
                transformed_y = transform_matrix.b * raw_bbox.x + transform_matrix.d * raw_bbox.y + transform_matrix.f
                transformed_width = abs(transform_matrix.a * raw_bbox.width)
                transformed_height = abs(transform_matrix.d * raw_bbox.height)
                
                return BoundingBox(
                    x=transformed_x, y=transformed_y,
                    width=transformed_width, height=transformed_height
                )
            
            return raw_bbox
        else:
            # Default empty bounding box
            return BoundingBox(x=0.0, y=0.0, width=0.0, height=0.0)
    
    def get_element_attributes(self, element: svgelements.SVGElement) -> Dict[str, Any]:
        """Extract all attributes from SVG element"""
        attributes = {}
        if hasattr(element, 'values'):
            attributes.update(element.values)
        
        # Add computed properties
        attributes['element_type'] = type(element).__name__.lower()
        attributes['id'] = getattr(element, 'id', '')
        
        return attributes