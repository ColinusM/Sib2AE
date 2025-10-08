#!/usr/bin/env python3
"""
SVG Unicode Discovery Tool

Uses hex analysis to reverse engineer all Unicode characters
in an SVG file, grouped by font family and position.
"""

import re
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

def extract_text_elements(svg_file: str) -> List[Dict]:
    """Extract all <text> elements with their Unicode content"""
    with open(svg_file, 'rb') as f:
        content = f.read()

    # Convert to string for XML parsing
    svg_text = content.decode('utf-8', errors='ignore')

    # Pattern to match <text> elements with attributes
    text_pattern = re.compile(
        r'<text[^>]*?x="([^"]+)"[^>]*?y="([^"]+)"[^>]*?font-family="([^"]+)"[^>]*?font-size="([^"]+)"[^>]*?>\s*([^<]*)</text>',
        re.DOTALL
    )

    elements = []
    for match in text_pattern.finditer(svg_text):
        x, y, font_family, font_size, text_content = match.groups()

        if text_content.strip():  # Only non-empty content
            # Get Unicode code points
            unicode_chars = []
            for char in text_content:
                unicode_chars.append({
                    'char': char,
                    'code_point': ord(char),
                    'hex': f"U+{ord(char):04X}",
                    'utf8_hex': char.encode('utf-8').hex()
                })

            elements.append({
                'x': float(x),
                'y': float(y),
                'font_family': font_family,
                'font_size': font_size,
                'text': text_content,
                'unicode_chars': unicode_chars
            })

    return elements

def analyze_by_font_family(elements: List[Dict]) -> Dict:
    """Group elements by font family and analyze patterns"""
    by_font = defaultdict(list)

    for elem in elements:
        by_font[elem['font_family']].append(elem)

    analysis = {}
    for font_family, font_elements in by_font.items():
        # Collect all unique Unicode characters used
        unicode_chars = set()
        char_positions = defaultdict(list)

        for elem in font_elements:
            for uc in elem['unicode_chars']:
                unicode_chars.add(uc['code_point'])
                char_positions[uc['code_point']].append((elem['x'], elem['y']))

        analysis[font_family] = {
            'count': len(font_elements),
            'unique_chars': sorted(unicode_chars),
            'char_positions': dict(char_positions)
        }

    return analysis

def print_unicode_map(analysis: Dict):
    """Print Unicode character map for each font family"""
    print("=" * 80)
    print("SVG UNICODE CHARACTER MAP")
    print("=" * 80)

    for font_family, data in sorted(analysis.items()):
        print(f"\n📝 Font Family: {font_family}")
        print(f"   Elements: {data['count']}")
        print(f"   Unique Characters: {len(data['unique_chars'])}")
        print()

        # Print character details
        for code_point in data['unique_chars']:
            char = chr(code_point)
            utf8_hex = char.encode('utf-8').hex()
            positions = data['char_positions'][code_point]

            # Classify character
            if code_point < 128:
                category = "ASCII"
            elif 0xE000 <= code_point <= 0xF8FF:
                category = "Private Use (Music Symbol)"
            else:
                category = "Unicode"

            print(f"   {category:30s} U+{code_point:04X} (decimal {code_point:5d}) UTF-8: {utf8_hex:12s}")
            print(f"      Character: '{char}'")
            print(f"      Occurrences: {len(positions)}")

            # Show first few positions
            if len(positions) <= 3:
                for x, y in positions:
                    print(f"         → ({x:.0f}, {y:.0f})")
            else:
                print(f"         → First 3 of {len(positions)} positions:")
                for x, y in positions[:3]:
                    print(f"            ({x:.0f}, {y:.0f})")
            print()

def find_ornament_patterns(analysis: Dict) -> Dict:
    """Identify likely ornament symbols (Private Use Area characters)"""
    ornaments = {}

    for font_family, data in analysis.items():
        if 'Helsinki' in font_family:  # Music notation fonts
            private_use_chars = [
                cp for cp in data['unique_chars']
                if 0xE000 <= cp <= 0xF8FF
            ]

            if private_use_chars:
                ornaments[font_family] = private_use_chars

    return ornaments

def compare_svgs(svg_no_ornament: str, svg_with_ornament: str):
    """Compare two SVGs to find ornament-specific characters"""
    print("\n" + "=" * 80)
    print("COMPARING SVG FILES TO FIND ORNAMENT SYMBOLS")
    print("=" * 80)

    # Extract from both files
    elements_no_orn = extract_text_elements(svg_no_ornament)
    elements_with_orn = extract_text_elements(svg_with_ornament)

    # Analyze both
    analysis_no_orn = analyze_by_font_family(elements_no_orn)
    analysis_with_orn = analyze_by_font_family(elements_with_orn)

    # Find differences
    all_fonts = set(analysis_no_orn.keys()) | set(analysis_with_orn.keys())

    for font in sorted(all_fonts):
        chars_no_orn = set(analysis_no_orn.get(font, {}).get('unique_chars', []))
        chars_with_orn = set(analysis_with_orn.get(font, {}).get('unique_chars', []))

        new_chars = chars_with_orn - chars_no_orn

        if new_chars:
            print(f"\n🎵 Font: {font}")
            print(f"   NEW CHARACTERS (likely ornaments):")
            for cp in sorted(new_chars):
                char = chr(cp)
                utf8_hex = char.encode('utf-8').hex()
                positions = analysis_with_orn[font]['char_positions'][cp]

                print(f"      U+{cp:04X} (UTF-8: {utf8_hex}) - {len(positions)} occurrences")
                print(f"         First position: ({positions[0][0]:.0f}, {positions[0][1]:.0f})")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single file:   python discover_svg_unicode.py <svg_file>")
        print("  Compare files: python discover_svg_unicode.py <no_ornament.svg> <with_ornament.svg>")
        sys.exit(1)

    svg_file = sys.argv[1]

    # Single file analysis
    print(f"Analyzing: {svg_file}")
    elements = extract_text_elements(svg_file)
    analysis = analyze_by_font_family(elements)

    print(f"\nFound {len(elements)} text elements")
    print_unicode_map(analysis)

    # Find ornaments
    ornaments = find_ornament_patterns(analysis)
    if ornaments:
        print("\n" + "=" * 80)
        print("DETECTED ORNAMENT SYMBOLS (Private Use Area)")
        print("=" * 80)
        for font, chars in ornaments.items():
            print(f"\n{font}:")
            for cp in chars:
                print(f"   U+{cp:04X} = {chr(cp).encode('utf-8').hex()}")

    # Compare mode
    if len(sys.argv) == 3:
        svg_with_ornament = sys.argv[2]
        compare_svgs(svg_file, svg_with_ornament)

if __name__ == '__main__':
    main()
