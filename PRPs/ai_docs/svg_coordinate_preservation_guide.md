# SVG Coordinate Preservation and Transformation Guide

## Overview
This guide provides technical documentation for preserving X/Y positioning when processing SVG files, specifically for music notation software like Sibelius exports to After Effects animation workflows.

## Core Concepts

### SVG Coordinate Systems
- **Viewport Coordinate System**: Defined by the SVG element's width/height attributes
- **User Coordinate System**: The coordinate space for SVG content, affected by viewBox
- **Local Coordinate System**: Individual element coordinate spaces after transformations

### Transformation Matrix Handling
SVG transformations use 2D affine transformation matrices:
```
[x']   [a c e] [x]
[y'] = [b d f] [y]
[1 ]   [0 0 1] [1]
```

Where:
- `a, d`: Scaling factors for x and y
- `b, c`: Skewing factors
- `e, f`: Translation offsets for x and y

### Nested Group Transformations
The Current Transformation Matrix (CTM) is the accumulation of all transformations from the root SVG to the current element.

## Implementation Techniques

### JavaScript/Browser Methods
```javascript
// Get untransformed bounding box
const bbox = element.getBBox();

// Get current transformation matrix
const ctm = element.getCTM();

// Transform point using CTM
const svgPoint = svg.createSVGPoint();
svgPoint.x = localX;
svgPoint.y = localY;
const transformedPoint = svgPoint.matrixTransform(ctm);
```

### Python Libraries for Coordinate Preservation

#### svgelements (Recommended)
```python
from svgelements import SVG, Matrix, Point

svg = SVG.parse("notation.svg")
for element in svg.elements():
    bbox = element.bbox()  # Bounding box coordinates
    matrix = element.transform  # Transformation matrix
    
    # Apply transformations
    point = Point(x, y)
    transformed = point * matrix
```

#### lxml with Manual Processing
```python
from lxml import etree
import numpy as np

def parse_transform(transform_str):
    """Parse SVG transform attribute to matrix"""
    # Implementation for parsing matrix(a,b,c,d,e,f) strings
    pass

def apply_nested_transforms(element, root_transform=None):
    """Apply all nested transformations to get final coordinates"""
    pass
```

## Music Notation Specific Patterns

### Element Identification
- **Noteheads**: Often circular/oval paths with specific coordinate patterns
- **Staff Lines**: Horizontal polylines with consistent y-coordinates
- **Stems**: Vertical lines connecting to noteheads
- **Text Elements**: Musical symbols and dynamic markings

### Coordinate Extraction Strategy
1. Parse SVG DOM structure
2. Identify musical elements by path patterns and grouping
3. Extract base coordinates and transformation matrices
4. Calculate final world coordinates for each element
5. Preserve relative positioning for animation software

## Best Practices

### Coordinate Accuracy
- Use double-precision floating point for calculations
- Account for viewBox scaling transformations
- Validate coordinates against known reference points
- Handle edge cases like rotated or skewed elements

### Performance Optimization
- Cache transformation matrix calculations
- Process elements in batches for large files
- Use streaming parsing for extremely large SVG files
- Consider parallel processing for independent elements

### Quality Assurance
- Implement coordinate validation tests
- Compare output against visual references
- Test with various DPI settings and scaling factors
- Validate preservation across different SVG export sources

## Common Pitfalls

### Transform Chain Issues
- Forgetting to account for nested group transformations
- Applying transformations in wrong order
- Missing viewBox coordinate space conversions

### Precision Loss
- Using single-precision floating point
- Rounding coordinates too early in processing
- Not accounting for sub-pixel positioning

### Library-Specific Gotchas
- Browser differences in getBBox() calculations
- Font dependencies in text element positioning
- Platform-specific SVG rendering variations

## Integration with After Effects

### Coordinate Mapping
After Effects uses a different coordinate system:
- Origin at top-left vs SVG's configurable origin
- Y-axis direction may be inverted
- Different units (pixels vs user units)

### Animation Preservation
- Maintain relative positioning between elements
- Preserve timing relationships in coordinate changes
- Account for keyframe interpolation requirements
- Consider layer hierarchy and parenting relationships

## Reference Implementation
See the main PRP for a complete implementation example using svgelements and cairosvg for optimal coordinate preservation in Sibelius to After Effects workflows.