import svgelements
from typing import Tuple
from models.musical_elements import MusicalElement, BoundingBox, TransformMatrix, Coordinate

class CoordinateExtractor:
    
    def __init__(self):
        self.precision = 2  # Decimal places for coordinate rounding
    
    def extract_coordinates(self, element: MusicalElement, 
                          svg_element: svgelements.SVGElement) -> BoundingBox:
        """Extract absolute coordinates by applying transformation matrices"""
        
        # Get the original bounding box
        original_bbox = element.original_bbox
        
        # Apply transformation matrix to get absolute coordinates
        transformed_bbox = self._apply_transform_to_bbox(
            original_bbox, element.transform_matrix
        )
        
        # Validate and quantize coordinates for precision
        transformed_bbox = self._quantize_bbox(transformed_bbox)
        
        return transformed_bbox
    
    def _apply_transform_to_bbox(self, bbox: BoundingBox, 
                                transform: TransformMatrix) -> BoundingBox:
        """Apply transformation matrix to bounding box corners"""
        
        # Define the four corners of the bounding box
        corners = [
            (bbox.x, bbox.y),                           # Top-left
            (bbox.x + bbox.width, bbox.y),              # Top-right
            (bbox.x, bbox.y + bbox.height),             # Bottom-left
            (bbox.x + bbox.width, bbox.y + bbox.height) # Bottom-right
        ]
        
        # Transform each corner
        transformed_corners = []
        for x, y in corners:
            tx, ty = self._apply_matrix_transform(x, y, transform)
            transformed_corners.append((tx, ty))
        
        # Calculate new bounding box from transformed corners
        x_coords = [corner[0] for corner in transformed_corners]
        y_coords = [corner[1] for corner in transformed_corners]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        return BoundingBox(
            x=min_x,
            y=min_y,
            width=max_x - min_x,
            height=max_y - min_y
        )
    
    def _apply_matrix_transform(self, x: float, y: float, 
                               transform: TransformMatrix) -> Tuple[float, float]:
        """Apply 2D transformation matrix to a point"""
        # Matrix transformation: [x' y' 1] = [x y 1] * [[a c e], [b d f], [0 0 1]]
        # Simplified: x' = a*x + c*y + e, y' = b*x + d*y + f
        
        transformed_x = transform.a * x + transform.c * y + transform.e
        transformed_y = transform.b * x + transform.d * y + transform.f
        
        return transformed_x, transformed_y
    
    def convert_to_absolute_coordinates(self, element: MusicalElement,
                                      parent_transform: TransformMatrix = None) -> MusicalElement:
        """Convert element coordinates to absolute coordinate system"""
        
        # If there's a parent transformation, combine it with element's transform
        if parent_transform:
            combined_transform = self._combine_transforms(parent_transform, element.transform_matrix)
        else:
            combined_transform = element.transform_matrix
        
        # Apply the combined transformation
        absolute_bbox = self._apply_transform_to_bbox(
            element.original_bbox, combined_transform
        )
        
        # Update the element with absolute coordinates
        element.transformed_bbox = absolute_bbox
        element.transform_matrix = combined_transform
        
        return element
    
    def _combine_transforms(self, parent: TransformMatrix, 
                           child: TransformMatrix) -> TransformMatrix:
        """Combine two transformation matrices (parent * child)"""
        # Matrix multiplication for 2D transforms
        # [a1 c1 e1]   [a2 c2 e2]   [a1*a2+c1*b2  a1*c2+c1*d2  a1*e2+c1*f2+e1]
        # [b1 d1 f1] * [b2 d2 f2] = [b1*a2+d1*b2  b1*c2+d1*d2  b1*e2+d1*f2+f1]
        # [0  0  1 ]   [0  0  1 ]   [0           0            1              ]
        
        return TransformMatrix(
            a=parent.a * child.a + parent.c * child.b,
            b=parent.b * child.a + parent.d * child.b,
            c=parent.a * child.c + parent.c * child.d,
            d=parent.b * child.c + parent.d * child.d,
            e=parent.a * child.e + parent.c * child.f + parent.e,
            f=parent.b * child.e + parent.d * child.f + parent.f
        )
    
    def _quantize_bbox(self, bbox: BoundingBox) -> BoundingBox:
        """Quantize coordinates to avoid floating-point precision issues"""
        return BoundingBox(
            x=round(bbox.x, self.precision),
            y=round(bbox.y, self.precision),
            width=round(bbox.width, self.precision),
            height=round(bbox.height, self.precision)
        )
    
    def calculate_coordinate_accuracy(self, original: BoundingBox, 
                                    transformed: BoundingBox) -> float:
        """Calculate coordinate preservation accuracy"""
        # Calculate the maximum deviation in any coordinate
        x_diff = abs(transformed.x - original.x)
        y_diff = abs(transformed.y - original.y)
        width_diff = abs(transformed.width - original.width)
        height_diff = abs(transformed.height - original.height)
        
        max_deviation = max(x_diff, y_diff, width_diff, height_diff)
        return max_deviation
    
    def validate_coordinate_precision(self, elements: list, tolerance: float = 1.0) -> bool:
        """Validate that coordinate transformations are within tolerance"""
        for element in elements:
            accuracy = self.calculate_coordinate_accuracy(
                element.original_bbox, element.transformed_bbox
            )
            if accuracy > tolerance:
                return False
        return True
    
    def extract_center_point(self, bbox: BoundingBox) -> Coordinate:
        """Extract center point of a bounding box"""
        return Coordinate(
            x=bbox.x + bbox.width / 2,
            y=bbox.y + bbox.height / 2
        )