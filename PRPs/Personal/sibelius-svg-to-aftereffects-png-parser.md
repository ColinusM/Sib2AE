name: "Sibelius SVG to After Effects PNG Parser - Advanced Music Notation Processing"
description: |

## Purpose

Template optimized for AI agents to implement an advanced SVG parser that converts Sibelius music notation exports into organized PNG assets for After Effects animation workflows, with precise coordinate preservation and intelligent element separation.

## Core Principles

1. **Context is King**: Include ALL necessary documentation, examples, and caveats for SVG processing
2. **Validation Loops**: Provide executable tests for SVG parsing, PNG conversion, and coordinate accuracy
3. **Information Dense**: Use music notation patterns and SVG processing best practices
4. **Progressive Success**: Start with basic parsing, validate coordinates, then enhance with advanced features

---

## Goal

Build a comprehensive SVG parser that processes a single Sibelius-exported SVG file and generates organized PNG assets with preserved coordinates for After Effects animation workflows.

**Input**: Single SVG file `/Users/colinmignot/Claude Code/Sib2Ae/PRPs-agentic-eng/Base/Saint-Saens Trio No 2_0001.svg`

**Output Structure**:
- One PNG file containing only noteheads
- One PNG file containing all elements except noteheads  
- Individual PNG files for each notehead with preserved coordinates
- Separate PNG files per instrument showing only that instrument
- Per-instrument PNG files with only noteheads
- Per-instrument PNG files with all elements except noteheads
- Organized folder structure per instrument with individual notehead PNGs

## Why

- **Animation Workflow Enhancement**: Enable precise After Effects animations by separating musical elements
- **Coordinate Preservation**: Maintain exact X/Y positioning for seamless integration into animation software
- **Batch Processing Efficiency**: Automate the tedious manual process of extracting individual musical elements
- **Production Pipeline Integration**: Bridge the gap between Sibelius notation software and After Effects animation tools

## What

A Python-based SVG processing system that:

1. **Parses Sibelius SVG exports** with complex nested groups and transformations
2. **Identifies musical elements** by analyzing SVG path patterns and groupings
3. **Extracts coordinates** while preserving transformations and relative positioning
4. **Generates organized PNG assets** with configurable DPI for production quality
5. **Creates folder structures** that match animation software workflow requirements

### Success Criteria

- [ ] Successfully parses the target SVG file and identifies all musical elements
- [ ] Generates PNG files with preserved coordinate positioning (±1 pixel accuracy)
- [ ] Creates organized folder structure per instrument
- [ ] Separates noteheads from other musical elements with 95%+ accuracy
- [ ] Produces individual PNG files for each notehead with correct positioning
- [ ] Maintains visual fidelity at 300 DPI for professional animation workflows
- [ ] Completes processing in under 60 seconds for typical music notation files

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Include these in your context window
- url: https://cairosvg.org/documentation/
  why: Primary PNG conversion library with coordinate preservation
  section: "Advanced usage and coordinate handling"

- url: https://pypi.org/project/svgelements/
  why: High-fidelity SVG parsing with transformation matrix support
  critical: "Handles nested transformations and coordinate extraction"

- url: https://www.w3.org/TR/SVG/coords.html
  why: SVG coordinate system specification
  section: "Transformation matrices and nested coordinate systems"

- docfile: PRPs/ai_docs/svg_coordinate_preservation_guide.md
  why: Comprehensive guide to SVG coordinate handling and transformation matrices

- url: https://www.verovio.org/
  why: Reference for music notation SVG structure patterns
  section: "MEI to SVG conversion documentation"

- url: https://www.scoringnotes.com/tips/export-graphics-from-sibelius-in-seconds/
  why: Sibelius SVG export workflow and common issues
  critical: "Font dependencies and page layout problems"

- file: /Users/colinmignot/Claude Code/Sib2Ae/PRPs-agentic-eng/Base/Saint-Saens Trio No 2_0001.svg
  why: Target SVG file with Sibelius export structure patterns
  critical: "Nested groups, transformation matrices, and musical element organization"

- url: https://developer.mozilla.org/en-US/docs/Web/API/SVGGraphicsElement/getBBox
  why: SVG bounding box calculation reference for coordinate extraction
```

### Current Codebase Structure

```bash
PRPs-agentic-eng/
├── Base/
│   └── Saint-Saens Trio No 2_0001.svg  # Target input file
├── PRPs/
│   ├── scripts/
│   │   └── prp_runner.py               # Python execution patterns
│   ├── ai_docs/
│   │   └── svg_coordinate_preservation_guide.md  # Technical reference
│   └── templates/
└── pyproject.toml                      # Python dependency management
```

### Desired Codebase Structure with New Files

```bash
PRPs-agentic-eng/
├── src/
│   ├── svg_parser/
│   │   ├── __init__.py
│   │   ├── core_parser.py              # Main SVG parsing logic
│   │   ├── element_classifier.py       # Musical element identification
│   │   ├── coordinate_extractor.py     # Transform matrix handling
│   │   └── png_generator.py            # PNG conversion with coordinate preservation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── musical_elements.py         # Pydantic models for musical elements
│   │   └── coordinate_system.py        # Coordinate transformation models
│   └── utils/
│       ├── __init__.py
│       ├── file_organizer.py           # Output folder structure management
│       └── validation.py               # Coordinate accuracy validation
├── output/                             # Generated PNG assets
│   ├── all_noteheads.png
│   ├── all_except_noteheads.png
│   ├── individual_noteheads/
│   ├── instruments/
│   │   ├── flute/
│   │   │   ├── flute_complete.png
│   │   │   ├── flute_noteheads.png
│   │   │   ├── flute_except_noteheads.png
│   │   │   └── individual_noteheads/
│   │   └── violin/
│   └── metadata/
│       └── coordinate_map.json         # Element positioning data
├── tests/
│   ├── test_svg_parser.py
│   ├── test_coordinate_extraction.py
│   └── test_png_generation.py
└── main.py                             # CLI entry point
```

### Known Gotchas & Library Quirks

```python
# CRITICAL: Sibelius SVG exports have font dependencies
# Solution: Process paths and shapes, ignore text elements initially

# CRITICAL: cairosvg preserves coordinates better than alternatives
# Usage: cairosvg.svg2png(url="input.svg", write_to="output.png", dpi=300)

# GOTCHA: svgelements requires explicit coordinate extraction
# Pattern: element.bbox() for untransformed bounds, apply CTM manually

# CRITICAL: Nested SVG groups accumulate transformations
# Solution: Calculate Current Transformation Matrix (CTM) for each element

# GOTCHA: Music notation elements may share identical path data
# Solution: Use transform attributes and positioning for differentiation

# CRITICAL: Sibelius exports include full page dimensions
# Solution: Extract content bounds and crop to actual music area

# PERFORMANCE: Large SVG files can exceed memory limits
# Solution: Process elements in batches, use streaming where possible

# COORDINATE SYSTEM: SVG uses different Y-axis orientation than After Effects
# Solution: Implement coordinate space conversion utilities
```

## Implementation Blueprint

### Data Models and Structure

Create core data models for type safety and coordinate handling:

```python
# File: src/models/musical_elements.py
from pydantic import BaseModel
from typing import List, Tuple, Optional, Literal

class Coordinate(BaseModel):
    x: float
    y: float

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class TransformMatrix(BaseModel):
    a: float  # x-scale
    b: float  # y-skew
    c: float  # x-skew
    d: float  # y-scale
    e: float  # x-translate
    f: float  # y-translate

class MusicalElement(BaseModel):
    element_id: str
    element_type: Literal["notehead", "stem", "staff_line", "clef", "text", "other"]
    svg_path: str
    original_bbox: BoundingBox
    transformed_bbox: BoundingBox
    transform_matrix: TransformMatrix
    instrument: Optional[str] = None
    staff_position: Optional[int] = None

class InstrumentGroup(BaseModel):
    name: str
    elements: List[MusicalElement]
    staff_lines: List[MusicalElement]
    noteheads: List[MusicalElement]
```

### List of Tasks in Implementation Order

```yaml
Task 1: Setup Project Structure and Dependencies
CREATE src/svg_parser/__init__.py:
  - EMPTY file for package initialization

CREATE pyproject.toml dependencies:
  - ADD svgelements>=1.9.0 for SVG parsing
  - ADD cairosvg>=2.7.0 for PNG conversion
  - ADD pydantic>=2.0.0 for data models
  - ADD click>=8.0.0 for CLI interface
  - ADD pytest>=7.0.0 for testing

Task 2: Core SVG Parsing Engine
CREATE src/svg_parser/core_parser.py:
  - IMPLEMENT SVGParser class with svgelements
  - PATTERN: Use svg = svgelements.SVG.parse(file_path)
  - METHOD: parse_svg() returns list of all elements
  - METHOD: extract_viewbox() for coordinate system setup
  - ERROR HANDLING: File not found, malformed SVG

Task 3: Musical Element Classification
CREATE src/svg_parser/element_classifier.py:
  - IMPLEMENT MusicalElementClassifier class
  - PATTERN: Analyze path data and grouping to identify element types
  - METHOD: classify_element(svg_element) -> MusicalElement
  - LOGIC: Noteheads = oval/circular paths with specific size ranges
  - LOGIC: Staff lines = horizontal polylines with consistent spacing
  - LOGIC: Stems = vertical lines connected to noteheads

Task 4: Coordinate Transformation Engine
CREATE src/svg_parser/coordinate_extractor.py:
  - IMPLEMENT CoordinateExtractor class
  - METHOD: extract_coordinates(element) with CTM calculation
  - PATTERN: Apply nested transformation matrices
  - METHOD: convert_to_absolute_coordinates()
  - VALIDATION: Ensure coordinate accuracy within tolerance

Task 5: PNG Generation with Coordinate Preservation
CREATE src/svg_parser/png_generator.py:
  - IMPLEMENT PNGGenerator class using cairosvg
  - METHOD: generate_filtered_png(elements, output_path, dpi=300)
  - PATTERN: Create temporary SVG with selected elements
  - METHOD: generate_individual_element_png()
  - CRITICAL: Preserve exact positioning using element transforms

Task 6: File Organization System
CREATE src/utils/file_organizer.py:
  - IMPLEMENT FileOrganizer class
  - METHOD: create_folder_structure()
  - PATTERN: Follow instrument-based hierarchy
  - METHOD: generate_metadata_json() with coordinate mapping

Task 7: Instrument Separation Logic
MODIFY src/svg_parser/element_classifier.py:
  - ADD instrument identification based on SVG grouping
  - PATTERN: Analyze group hierarchy and staff positioning
  - METHOD: assign_to_instrument(element) -> str
  - LOGIC: Use Y-coordinate ranges for staff assignment

Task 8: CLI Interface and Main Entry Point
CREATE main.py:
  - IMPLEMENT click-based CLI interface
  - PATTERN: main(input_file, output_dir, dpi, instruments)
  - INTEGRATION: Chain all components together
  - VALIDATION: Input file exists, output directory writable

Task 9: Comprehensive Testing Suite
CREATE tests/test_svg_parser.py:
  - TEST: SVG parsing with sample file
  - TEST: Element classification accuracy
  - TEST: Coordinate preservation validation
  - PATTERN: Use pytest fixtures for SVG test data

Task 10: Documentation and Usage Examples
CREATE README.md:
  - USAGE: Command-line examples
  - INTEGRATION: After Effects import workflow
  - TROUBLESHOOTING: Common issues and solutions
```

### Core Algorithm Pseudocode

```python
# Main processing workflow
def process_sibelius_svg(input_file: str, output_dir: str) -> ProcessingResult:
    # STEP 1: Parse SVG and extract all elements
    parser = SVGParser()
    svg_data = parser.parse_svg(input_file)
    all_elements = parser.extract_elements(svg_data)
    
    # STEP 2: Classify musical elements
    classifier = MusicalElementClassifier()
    classified_elements = []
    for element in all_elements:
        musical_element = classifier.classify_element(element)
        classified_elements.append(musical_element)
    
    # STEP 3: Extract and preserve coordinates
    coord_extractor = CoordinateExtractor()
    for element in classified_elements:
        element.transformed_bbox = coord_extractor.extract_coordinates(element)
    
    # STEP 4: Group by instruments
    instruments = classifier.group_by_instrument(classified_elements)
    
    # STEP 5: Generate PNG outputs
    png_generator = PNGGenerator()
    
    # Generate master files
    noteheads = [e for e in classified_elements if e.element_type == "notehead"]
    others = [e for e in classified_elements if e.element_type != "notehead"]
    
    png_generator.generate_filtered_png(noteheads, f"{output_dir}/all_noteheads.png")
    png_generator.generate_filtered_png(others, f"{output_dir}/all_except_noteheads.png")
    
    # Generate individual notehead files
    for i, notehead in enumerate(noteheads):
        png_generator.generate_individual_element_png(
            notehead, f"{output_dir}/individual_noteheads/notehead_{i:03d}.png"
        )
    
    # Generate per-instrument files
    for instrument_name, instrument_elements in instruments.items():
        instrument_dir = f"{output_dir}/instruments/{instrument_name}"
        
        # Complete instrument
        png_generator.generate_filtered_png(
            instrument_elements, f"{instrument_dir}/{instrument_name}_complete.png"
        )
        
        # Instrument noteheads only
        instrument_noteheads = [e for e in instrument_elements if e.element_type == "notehead"]
        png_generator.generate_filtered_png(
            instrument_noteheads, f"{instrument_dir}/{instrument_name}_noteheads.png"
        )
        
        # Instrument without noteheads
        instrument_others = [e for e in instrument_elements if e.element_type != "notehead"]
        png_generator.generate_filtered_png(
            instrument_others, f"{instrument_dir}/{instrument_name}_except_noteheads.png"
        )
        
        # Individual noteheads per instrument
        for i, notehead in enumerate(instrument_noteheads):
            png_generator.generate_individual_element_png(
                notehead, f"{instrument_dir}/individual_noteheads/notehead_{i:03d}.png"
            )
    
    # STEP 6: Generate metadata
    organizer = FileOrganizer()
    organizer.generate_metadata_json(classified_elements, f"{output_dir}/metadata/coordinate_map.json")
    
    return ProcessingResult(success=True, elements_processed=len(classified_elements))
```

### Integration Points

```yaml
DEPENDENCIES:
  - svgelements: High-fidelity SVG parsing with coordinate extraction
  - cairosvg: SVG to PNG conversion with DPI control
  - pydantic: Data model validation and type safety
  - click: CLI interface for user interaction

COORDINATE_SYSTEM:
  - input: SVG coordinate space with transformations
  - processing: Absolute coordinates with preserved positioning
  - output: PNG files with metadata for After Effects import

FILE_STRUCTURE:
  - pattern: Hierarchical organization by instrument and element type
  - naming: Consistent naming convention for automation scripts
  - metadata: JSON files with coordinate mapping for animation software

VALIDATION:
  - coordinate_accuracy: ±1 pixel tolerance for positioning
  - element_classification: 95%+ accuracy for notehead identification
  - visual_fidelity: No loss of quality at 300 DPI output
```

## Validation Loop

### Level 1: Syntax & Style

```bash
# Run these FIRST - fix any errors before proceeding
ruff check src/ --fix                   # Auto-fix formatting and imports
mypy src/                               # Type checking with strict mode
pytest tests/test_models.py -v          # Validate data model structure

# Expected: No errors. If errors exist, read and fix systematically.
```

### Level 2: Unit Tests - SVG Processing Components

```python
# CREATE tests/test_svg_parser.py
def test_svg_parsing_basic():
    """Test basic SVG file parsing"""
    parser = SVGParser()
    result = parser.parse_svg("Base/Saint-Saens Trio No 2_0001.svg")
    assert result is not None
    assert len(result.elements) > 0

def test_element_classification_noteheads():
    """Test notehead identification accuracy"""
    classifier = MusicalElementClassifier()
    # Load known notehead elements from test data
    test_elements = load_test_svg_elements()
    noteheads = [e for e in test_elements if classifier.classify_element(e).element_type == "notehead"]
    # Validate against manual classification
    assert len(noteheads) >= 10  # Minimum expected noteheads

def test_coordinate_preservation():
    """Test coordinate accuracy within tolerance"""
    extractor = CoordinateExtractor()
    test_element = create_test_element_with_known_coordinates()
    extracted_coords = extractor.extract_coordinates(test_element)
    expected_coords = get_expected_coordinates()
    
    assert abs(extracted_coords.x - expected_coords.x) <= 1.0
    assert abs(extracted_coords.y - expected_coords.y) <= 1.0

def test_png_generation_quality():
    """Test PNG output quality and file creation"""
    generator = PNGGenerator()
    test_elements = load_test_elements()
    output_path = "test_output.png"
    
    generator.generate_filtered_png(test_elements, output_path, dpi=300)
    
    assert os.path.exists(output_path)
    # Validate PNG properties (size, DPI, etc.)
    validate_png_properties(output_path)
```

```bash
# Run and iterate until passing:
pytest tests/ -v --tb=short
# If failing: Read error messages, understand root cause, fix code, re-run
```

### Level 3: Integration Test - Full Pipeline

```bash
# Test complete processing pipeline
python main.py --input "Base/Saint-Saens Trio No 2_0001.svg" --output "test_output" --dpi 300

# Validate output structure
ls -la test_output/
# Expected structure:
# test_output/
# ├── all_noteheads.png
# ├── all_except_noteheads.png
# ├── individual_noteheads/
# ├── instruments/
# │   ├── flute/
# │   └── violin/
# └── metadata/

# Validate PNG file properties
file test_output/all_noteheads.png
# Expected: PNG image data, 300 DPI

# Validate coordinate metadata
python -c "import json; data=json.load(open('test_output/metadata/coordinate_map.json')); print(f'Elements: {len(data)}'); print('Sample:', data[0] if data else 'No data')"
# Expected: JSON with element coordinates and metadata
```

### Level 4: Visual and Coordinate Validation

```python
# CREATE tests/visual_validation.py
def test_visual_coordinate_accuracy():
    """Validate coordinate preservation through visual comparison"""
    import PIL.Image
    
    # Load original SVG-rendered image
    original = render_svg_to_image("Base/Saint-Saens Trio No 2_0001.svg")
    
    # Load generated notehead overlay
    generated = PIL.Image.open("test_output/all_noteheads.png")
    
    # Compare notehead positions (pixel-level accuracy)
    coordinate_differences = compare_notehead_positions(original, generated)
    
    # Validate positioning accuracy
    max_difference = max(coordinate_differences)
    assert max_difference <= 2.0, f"Coordinate difference too large: {max_difference}"

def test_after_effects_compatibility():
    """Test compatibility with After Effects import workflow"""
    # This would ideally test actual AE import, but we'll simulate
    metadata = json.load(open("test_output/metadata/coordinate_map.json"))
    
    # Validate metadata structure for AE compatibility
    for element in metadata:
        assert "x" in element and "y" in element
        assert "width" in element and "height" in element
        assert "element_type" in element
        assert isinstance(element["x"], (int, float))
        assert isinstance(element["y"], (int, float))

def test_performance_benchmark():
    """Validate processing performance meets requirements"""
    import time
    
    start_time = time.time()
    
    # Run full processing pipeline
    result = subprocess.run([
        "python", "main.py", 
        "--input", "Base/Saint-Saens Trio No 2_0001.svg",
        "--output", "benchmark_output"
    ], capture_output=True, text=True)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    assert result.returncode == 0, f"Processing failed: {result.stderr}"
    assert processing_time < 60.0, f"Processing too slow: {processing_time:.2f}s"
```

```bash
# Run visual validation tests
pytest tests/visual_validation.py -v -s

# Performance benchmark
python tests/performance_test.py
# Expected: Processing completes in <60 seconds
```

## Final Validation Checklist

- [ ] All unit tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check src/`
- [ ] No type errors: `mypy src/`
- [ ] SVG parsing successful: `python main.py --input Base/Saint-Saens\ Trio\ No\ 2_0001.svg --output validation_output`
- [ ] PNG files generated with correct structure and quality
- [ ] Coordinate preservation within ±1 pixel accuracy
- [ ] Individual notehead extraction with preserved positioning
- [ ] Instrument separation functioning correctly
- [ ] Metadata JSON generated with complete coordinate mapping
- [ ] Processing completes within 60 seconds for target file
- [ ] Output compatible with After Effects import workflow

---

## Quality Score Evaluation

**Confidence Level for One-Pass Implementation Success: 8.5/10**

**Rationale:**
- **High Context Coverage (9/10)**: Comprehensive research into SVG parsing libraries, coordinate preservation techniques, and music notation patterns
- **Clear Implementation Path (9/10)**: Well-defined task breakdown with specific technical approaches and proven libraries
- **Robust Validation (8/10)**: Multi-level testing strategy including coordinate accuracy validation and performance benchmarks
- **Technical Feasibility (8/10)**: Using established libraries (svgelements, cairosvg) with documented coordinate preservation capabilities
- **Edge Case Handling (8/10)**: Addresses known Sibelius SVG export issues and transformation matrix complications

**Potential Risk Areas:**
- Complex nested transformations in Sibelius exports may require iterative debugging
- Element classification accuracy depends on consistent SVG patterns from Sibelius
- Performance optimization may be needed for very large notation files

**Success Factors:**
- Leverages proven SVG processing libraries with coordinate preservation
- Comprehensive testing strategy with measurable success criteria
- Clear separation of concerns with modular architecture
- Detailed documentation of music notation SVG patterns and gotchas

## Anti-Patterns to Avoid

- ❌ Don't ignore transformation matrices - they're critical for coordinate accuracy
- ❌ Don't use simplified SVG parsing libraries that lose coordinate precision
- ❌ Don't process all elements at once - use batching for memory efficiency
- ❌ Don't hardcode instrument detection - use flexible pattern matching
- ❌ Don't skip coordinate validation tests - positioning accuracy is crucial
- ❌ Don't assume consistent SVG structure across different Sibelius versions
- ❌ Don't forget to handle edge cases like rotated or scaled notation elements