# SVG Parser Redesign: Hex-Based Analysis

## Current Approach (Limitations)

### How It Works Now
```python
# 1. Parse MusicXML for note data
notes = extract_xml_notes("file.musicxml")

# 2. Use hardcoded transformation constants
X_SCALE = 3.206518
X_OFFSET = 564.93
svg_x = xml_x * X_SCALE + X_OFFSET

# 3. Search SVG with regex string matching
if '<text ' in line and 'Helsinki Std' in line:
    x_match = re.search(r'x="([^"]+)"', line)
    # ... extract coordinates as strings
```

### Problems
1. **Blind to Unicode characters** - Can't see what's actually in the SVG
2. **Fragile regex matching** - Breaks if SVG format changes slightly
3. **Hardcoded transformations** - Doesn't adapt to different exports
4. **No ornament detection** - Can't identify trill symbols, accents, etc.
5. **String-based parsing** - Inefficient and error-prone

---

## What Hex Analysis Revealed

### The Trill Discovery

**Visual in terminal:**
```bash
cat file.svg | grep trill
# Output: > </text>  (appears empty!)
```

**Hex reality:**
```bash
sed -n '310p' file.svg | xxd
# Output: 00000000: 203e ef83 993c 2f74 6578 743e 0a
#                      ^^-^^-^^
#                      U+F0D9 (trill symbol)
```

### Key Findings

**1. Noteheads are Unicode characters:**
```
Hollow notehead: &#70; = U+0046 = 0x46
Filled notehead: &#102; = U+0066 = 0x66
```

**2. Ornaments are Unicode too:**
```
Trill start: U+F0D9 = 0xef8399 (UTF-8 bytes)
Trill wavy: U+F07E = 0xef819e (UTF-8 bytes)
```

**3. Font family identifies purpose:**
```
Helsinki Std = music notation symbols
Helsinki Special Std = noteheads
```

---

## New Parser Design

### Architecture

```python
class SVGHexParser:
    """Hex-aware SVG parser for music notation"""

    def __init__(self, svg_file: str):
        self.svg_file = svg_file
        self.raw_bytes = open(svg_file, 'rb').read()
        self.unicode_map = self._build_unicode_map()

    def _build_unicode_map(self) -> Dict:
        """Map Unicode characters to notation elements"""
        return {
            # Noteheads
            0x0046: 'notehead_hollow',  # Whole/half notes
            0x0066: 'notehead_filled',  # Quarter/eighth notes

            # Ornaments (Private Use Area)
            0xF0D9: 'trill_start',
            0xF07E: 'trill_wavy',
            0xF0C4: 'mordent',
            0xF0AA: 'turn',
            # ... discover more via hex analysis
        }

    def extract_elements_by_unicode(self, unicode_char: int) -> List[Dict]:
        """Find all instances of a Unicode character"""
        # Convert char to UTF-8 bytes
        utf8_bytes = chr(unicode_char).encode('utf-8')

        # Find all occurrences in raw bytes
        elements = []
        offset = 0
        while True:
            offset = self.raw_bytes.find(utf8_bytes, offset)
            if offset == -1:
                break

            # Parse backward to find <text> tag with coordinates
            element = self._parse_text_element(offset)
            if element:
                elements.append(element)

            offset += len(utf8_bytes)

        return elements

    def find_ornaments_near_notehead(self, notehead_x: int, notehead_y: int) -> List[Dict]:
        """Find ornament symbols near a notehead position"""
        ornaments = []

        # Check area above notehead (y - 50 to y - 150)
        for ornament_code in [0xF0D9, 0xF07E, 0xF0C4, 0xF0AA]:
            elements = self.extract_elements_by_unicode(ornament_code)

            for elem in elements:
                # Check if within proximity
                if (abs(elem['x'] - notehead_x) < 100 and
                    notehead_y - 150 < elem['y'] < notehead_y - 50):
                    ornaments.append({
                        'type': self.unicode_map[ornament_code],
                        'unicode': ornament_code,
                        'position': (elem['x'], elem['y'])
                    })

        return ornaments

    def reverse_engineer_transformation(self, xml_notes: List[Dict]) -> Dict:
        """Discover coordinate transformation by comparing XML to SVG"""
        # Find noteheads in SVG
        svg_noteheads = self.extract_elements_by_unicode(0x0066)  # Filled notes

        # Match with XML notes
        matches = []
        for xml_note in xml_notes:
            for svg_note in svg_noteheads:
                # Find best match (closest in relative position)
                matches.append({
                    'xml_x': xml_note['absolute_x'],
                    'svg_x': svg_note['x'],
                    'xml_y': xml_note['xml_y'],
                    'svg_y': svg_note['y']
                })

        # Calculate transformation from matches
        # Linear regression: svg_x = scale * xml_x + offset
        import numpy as np
        xml_xs = np.array([m['xml_x'] for m in matches])
        svg_xs = np.array([m['svg_x'] for m in matches])

        scale, offset = np.polyfit(xml_xs, svg_xs, 1)

        return {
            'x_scale': scale,
            'x_offset': offset,
            'confidence': self._calculate_fit_quality(matches, scale, offset)
        }
```

---

## Usage Examples

### 1. Extract All Noteheads
```python
parser = SVGHexParser("score.svg")

# Find all filled noteheads (quarter notes)
filled = parser.extract_elements_by_unicode(0x0066)
print(f"Found {len(filled)} filled noteheads")

# Find all hollow noteheads (whole/half notes)
hollow = parser.extract_elements_by_unicode(0x0046)
print(f"Found {len(hollow)} hollow noteheads")
```

### 2. Detect Ornaments
```python
# Get notehead position from XML
notehead_x, notehead_y = 3602, 1034

# Find ornaments above it
ornaments = parser.find_ornaments_near_notehead(notehead_x, notehead_y)

if ornaments:
    print(f"Found ornaments: {[o['type'] for o in ornaments]}")
    # Output: ['trill_start', 'trill_wavy', 'trill_wavy']
```

### 3. Reverse Engineer Transformations
```python
xml_notes = extract_xml_notes("score.musicxml")
transformation = parser.reverse_engineer_transformation(xml_notes)

print(f"Discovered transformation:")
print(f"  X scale: {transformation['x_scale']}")
print(f"  X offset: {transformation['x_offset']}")
print(f"  Confidence: {transformation['confidence']}%")
```

---

## Benefits for Ornament Detection

### Current Problem
```python
# Can't detect this in XML → SVG → Ornament relationship
xml: <note> with <trill-mark>
svg: ???  (invisible to string parser)
```

### New Solution
```python
# 1. Parse XML for trill
has_trill = note.find('.//ornaments/trill-mark') is not None

# 2. Get expected notehead position
svg_x, svg_y = transform_coordinates(note)

# 3. Search for trill Unicode near that position
parser = SVGHexParser("score.svg")
trills = parser.find_ornaments_near_notehead(svg_x, svg_y)

# 4. Confirm match
if has_trill and trills:
    print(f"✓ Trill confirmed: XML + SVG matched")
    print(f"  Trill symbols: {[hex(t['unicode']) for t in trills]}")
```

---

## Implementation Plan

### Phase 1: Unicode Discovery Tool
```python
# Tool to scan SVG and report all Unicode characters used
def discover_unicode_chars(svg_file: str):
    """Find all unique Unicode characters in SVG"""
    with open(svg_file, 'rb') as f:
        content = f.read()

    # Parse for all <text> elements
    # Extract Unicode values
    # Group by font-family
    # Report findings
```

### Phase 2: Hex-Based Element Extractor
- Extract noteheads by Unicode
- Extract ornaments by Unicode
- Extract dynamics, articulations, etc.

### Phase 3: Smart Coordinate Matching
- Auto-discover transformations
- Adaptive matching algorithms
- Confidence scoring

### Phase 4: Integration with Pipeline
- Replace regex-based parsers
- Add ornament detection stage
- Enhance Universal ID system

---

## Next Steps

1. **Run Unicode discovery** on existing SVG files
2. **Build Unicode map** for all notation symbols
3. **Prototype hex-based extractor** for noteheads
4. **Test with trill detection** as proof of concept
5. **Expand to full parser** replacement

This approach makes the SVG parser:
- **Robust** - Works with actual bytes, not fragile regex
- **Discoverable** - Can reverse engineer unknown patterns
- **Extensible** - Easy to add new symbol types
- **Debuggable** - Can see exactly what's in the file
