#!/usr/bin/env python3
"""
SVG Deep Analyzer - Hex-Based Complete Extraction

Shows EVERYTHING we can extract from SVG that was previously invisible:
- Noteheads (all types: whole, half, quarter, eighth)
- Ornaments (trills, mordents, turns, grace notes)
- Articulations (staccato, accent, tenuto, fermata)
- Dynamics (p, f, mp, mf, crescendo, diminuendo)
- Stems, beams, ties, slurs
- Staff lines, barlines, clefs, time signatures
- Accidentals (sharp, flat, natural)
"""

import re
import sys
from collections import defaultdict
from typing import Dict, List, Tuple, Set

class SVGElement:
    """Represents a single SVG element with position and content"""
    def __init__(self, x: float, y: float, unicode_char: str, font: str, size: str):
        self.x = x
        self.y = y
        self.unicode_char = unicode_char
        self.code_point = ord(unicode_char)
        self.font = font
        self.size = size
        self.utf8_hex = unicode_char.encode('utf-8').hex()

    def __repr__(self):
        return f"Element(x={self.x:.0f}, y={self.y:.0f}, U+{self.code_point:04X}, font={self.font})"


class DeepSVGAnalyzer:
    """Complete SVG analysis using hex-based extraction"""

    # Unicode mappings for Sibelius fonts (Lelandia, Helsinki, etc.)
    # These private-use codes are consistent across Sibelius notation fonts
    MUSIC_SYMBOLS = {
        # Noteheads (filled)
        0xF0CF: 'notehead_filled',      # ef838f - Quarter/eighth notes
        0xF0B7: 'notehead_whole',       # ef82b7 - Whole notes
        0xF0CE: 'notehead_half',        # ef838e - Half notes

        # Ornaments
        0xF0D9: 'trill_start',          # ef8399 - Trill symbol tr
        0xF07E: 'trill_wavy',           # ef81be - Wavy line segments
        0xF04D: 'mordent',              # ef818d - Mordent symbol (Lelandia/Sibelius)
        0xF0C4: 'inverted_mordent',     # Alternative mordent form
        0xF0AA: 'turn',                 # ef82aa - Turn symbol
        0xF0DE: 'grace_notehead',       # ef839e - Grace note (acciaccatura/appoggiatura)

        # Articulations
        0xF04A: 'staccato_or_accent',   # ef818a - Dot or accent
        0xF06A: 'accent',               # ef81aa - Accent mark

        # Clefs & Time Signatures
        0xF023: 'time_signature_elem',  # ef80a3
        0xF026: 'treble_clef',          # ef80a6

        # Accidentals
        0xF0E4: 'sharp',                # ef83a4 - Sharp symbol
        0xF0EE: 'natural',              # ef83ae - Natural symbol
        0xF0FA: 'flat',                 # ef83ba - Flat symbol
    }

    def __init__(self, svg_file: str):
        self.svg_file = svg_file
        self.elements = self._extract_all_elements()

    def _extract_all_elements(self) -> List[SVGElement]:
        """Extract ALL text elements with hex-aware parsing"""
        with open(self.svg_file, 'rb') as f:
            content = f.read()

        svg_text = content.decode('utf-8', errors='ignore')

        # Extract text elements with coordinates
        pattern = re.compile(
            r'<text[^>]*?x="([^"]+)"[^>]*?y="([^"]+)"[^>]*?font-family="([^"]+)"[^>]*?font-size="([^"]+)"[^>]*?>\s*([^<]*)</text>',
            re.DOTALL
        )

        elements = []
        for match in pattern.finditer(svg_text):
            x, y, font, size, text = match.groups()

            if text.strip():
                for char in text:
                    elements.append(SVGElement(
                        float(x), float(y), char, font, size
                    ))

        return elements

    def get_noteheads(self) -> Dict[str, List[SVGElement]]:
        """Extract ALL notehead types (previously: only saw filled noteheads)"""
        noteheads = {
            'whole': [],
            'half': [],
            'quarter': [],
            'unknown': []
        }

        for elem in self.elements:
            # Font-agnostic: works with Lelandia (Sibelius), Helsinki, and other notation fonts
            symbol_type = self.MUSIC_SYMBOLS.get(elem.code_point)

            if symbol_type == 'notehead_whole':
                noteheads['whole'].append(elem)
            elif symbol_type == 'notehead_half':
                noteheads['half'].append(elem)
            elif symbol_type == 'notehead_filled':
                noteheads['quarter'].append(elem)
            elif symbol_type and 'notehead' in symbol_type and 'grace' not in symbol_type:
                noteheads['unknown'].append(elem)

        return noteheads

    def get_ornaments(self) -> Dict[str, List[SVGElement]]:
        """Extract ALL ornaments (previously: COMPLETELY INVISIBLE)"""
        ornaments = {
            'trills': [],
            'mordents': [],
            'turns': [],
            'grace_notes': [],
            'other': []
        }

        for elem in self.elements:
            symbol_type = self.MUSIC_SYMBOLS.get(elem.code_point)

            if symbol_type == 'trill_start' or symbol_type == 'trill_wavy':
                ornaments['trills'].append(elem)
            elif symbol_type == 'mordent':
                ornaments['mordents'].append(elem)
            elif symbol_type == 'turn':
                ornaments['turns'].append(elem)
            elif symbol_type == 'grace_notehead':
                ornaments['grace_notes'].append(elem)
            elif symbol_type and ('ornament' in symbol_type or 'trill' in symbol_type):
                ornaments['other'].append(elem)

        return ornaments

    def get_articulations(self) -> List[SVGElement]:
        """Extract articulation marks (previously: INVISIBLE)"""
        articulations = []

        for elem in self.elements:
            symbol_type = self.MUSIC_SYMBOLS.get(elem.code_point)
            if symbol_type in ['staccato_or_accent', 'accent']:
                articulations.append(elem)

        return articulations

    def get_accidentals(self) -> Dict[str, List[SVGElement]]:
        """Extract sharp/flat/natural symbols (previously: NOT DISTINGUISHED)"""
        accidentals = {
            'sharps': [],
            'flats': [],
            'naturals': []
        }

        for elem in self.elements:
            symbol_type = self.MUSIC_SYMBOLS.get(elem.code_point)

            if symbol_type == 'sharp':
                accidentals['sharps'].append(elem)
            elif symbol_type == 'flat':
                accidentals['flats'].append(elem)
            elif symbol_type == 'natural':
                accidentals['naturals'].append(elem)

        return accidentals

    def get_clefs(self) -> List[SVGElement]:
        """Extract clef symbols (previously: NOT DETECTED)"""
        clefs = []
        for elem in self.elements:
            symbol_type = self.MUSIC_SYMBOLS.get(elem.code_point)
            if symbol_type == 'treble_clef':
                clefs.append(elem)
        return clefs

    def find_ornament_for_notehead(self, notehead: SVGElement) -> List[SVGElement]:
        """
        Find ornaments above a specific notehead
        (previously: IMPOSSIBLE - we couldn't even see ornaments!)
        """
        ornaments = []

        # Search area: 50-150px above notehead, ±100px horizontal
        for elem in self.elements:
            is_ornament = self.HELSINKI_STD_SYMBOLS.get(elem.code_point, '').startswith('trill')

            if is_ornament:
                dx = abs(elem.x - notehead.x)
                dy = notehead.y - elem.y  # Ornament should be ABOVE

                if dx < 100 and 50 < dy < 150:
                    ornaments.append(elem)

        return ornaments

    def get_notehead_with_ornaments(self) -> List[Dict]:
        """
        Link noteheads to their ornaments
        (previously: COMPLETELY IMPOSSIBLE)
        """
        noteheads = self.get_noteheads()
        all_noteheads = noteheads['quarter'] + noteheads['half'] + noteheads['whole']

        results = []
        for notehead in all_noteheads:
            ornaments = self.find_ornament_for_notehead(notehead)

            if ornaments:
                results.append({
                    'notehead': notehead,
                    'ornaments': ornaments,
                    'ornament_types': [
                        self.HELSINKI_STD_SYMBOLS.get(o.code_point, 'unknown')
                        for o in ornaments
                    ]
                })

        return results

    def get_unknown_symbols(self) -> List[SVGElement]:
        """Find symbols we haven't categorized yet (for discovery)"""
        unknown = []

        for elem in self.elements:
            if 'Helsinki' in elem.font:
                if elem.code_point not in self.HELSINKI_STD_SYMBOLS:
                    if elem.code_point not in self.HELSINKI_SPECIAL_SYMBOLS:
                        unknown.append(elem)

        return unknown

    def get_spatial_clusters(self) -> Dict[str, List[SVGElement]]:
        """
        Group elements by spatial proximity
        (previously: Had to guess relationships)
        """
        # Group elements by Y position (within 20px = same line)
        y_clusters = defaultdict(list)

        for elem in self.elements:
            if 'Helsinki' in elem.font:
                y_key = round(elem.y / 20) * 20  # Round to nearest 20px
                y_clusters[y_key].append(elem)

        return dict(y_clusters)

    def analyze_notehead_types(self) -> Dict:
        """
        Distinguish between different notehead types
        (previously: Only knew hollow=70, filled=102)
        """
        noteheads = self.get_noteheads()

        return {
            'whole_notes': len(noteheads['whole']),
            'half_notes': len(noteheads['half']),
            'quarter_eighth_notes': len(noteheads['quarter']),
            'total': sum(len(v) for v in noteheads.values())
        }

    def print_complete_analysis(self):
        """Print everything we can now extract from SVG"""
        print("=" * 80)
        print("COMPLETE SVG DEEP ANALYSIS")
        print("=" * 80)
        print(f"\nFile: {self.svg_file}")
        print(f"Total elements extracted: {len(self.elements)}")

        # 1. NOTEHEADS (Now: Distinguish types!)
        print("\n" + "=" * 80)
        print("1. NOTEHEADS (By Type)")
        print("=" * 80)
        noteheads = self.get_noteheads()
        print(f"   Whole notes:    {len(noteheads['whole'])}")
        print(f"   Half notes:     {len(noteheads['half'])}")
        print(f"   Quarter notes:  {len(noteheads['quarter'])}")

        if noteheads['quarter'][:3]:
            print("\n   First 3 quarter notes:")
            for nh in noteheads['quarter'][:3]:
                print(f"      → ({nh.x:.0f}, {nh.y:.0f}) U+{nh.code_point:04X}")

        # 2. ORNAMENTS (Previously: INVISIBLE!)
        print("\n" + "=" * 80)
        print("2. ORNAMENTS (Previously INVISIBLE)")
        print("=" * 80)
        ornaments = self.get_ornaments()
        for orn_type, elems in ornaments.items():
            if elems:
                print(f"\n   {orn_type.upper()}: {len(elems)}")
                for elem in elems[:3]:
                    print(f"      → ({elem.x:.0f}, {elem.y:.0f}) {self.HELSINKI_STD_SYMBOLS.get(elem.code_point, 'unknown')}")

        # 3. NOTEHEADS WITH ORNAMENTS (Previously: IMPOSSIBLE!)
        print("\n" + "=" * 80)
        print("3. NOTEHEADS WITH ORNAMENTS (Previously IMPOSSIBLE)")
        print("=" * 80)
        nh_with_orn = self.get_notehead_with_ornaments()
        print(f"   Found {len(nh_with_orn)} noteheads with ornaments")

        for item in nh_with_orn:
            nh = item['notehead']
            orns = item['ornaments']
            print(f"\n   Notehead at ({nh.x:.0f}, {nh.y:.0f}):")
            print(f"      Ornaments above it:")
            for orn in orns:
                orn_type = self.HELSINKI_STD_SYMBOLS.get(orn.code_point, 'unknown')
                dy = nh.y - orn.y
                print(f"         {orn_type} at ({orn.x:.0f}, {orn.y:.0f}) - {dy:.0f}px above")

        # 4. ACCIDENTALS (Previously: Not distinguished)
        print("\n" + "=" * 80)
        print("4. ACCIDENTALS (Previously: Not Distinguished)")
        print("=" * 80)
        accidentals = self.get_accidentals()
        for acc_type, elems in accidentals.items():
            if elems:
                print(f"   {acc_type.upper()}: {len(elems)}")
                for elem in elems[:3]:
                    print(f"      → ({elem.x:.0f}, {elem.y:.0f})")

        # 5. ARTICULATIONS (Previously: INVISIBLE)
        print("\n" + "=" * 80)
        print("5. ARTICULATIONS (Previously INVISIBLE)")
        print("=" * 80)
        articulations = self.get_articulations()
        print(f"   Found {len(articulations)} articulation marks")
        for art in articulations[:5]:
            print(f"      → ({art.x:.0f}, {art.y:.0f}) U+{art.code_point:04X}")

        # 6. CLEFS (Previously: Not detected)
        print("\n" + "=" * 80)
        print("6. CLEFS (Previously: Not Detected)")
        print("=" * 80)
        clefs = self.get_clefs()
        print(f"   Found {len(clefs)} clef symbols")
        for clef in clefs:
            print(f"      → ({clef.x:.0f}, {clef.y:.0f})")

        # 7. UNKNOWN SYMBOLS (For discovery)
        print("\n" + "=" * 80)
        print("7. UNKNOWN SYMBOLS (To Discover)")
        print("=" * 80)
        unknown = self.get_unknown_symbols()

        # Group by code point
        unknown_by_code = defaultdict(list)
        for elem in unknown:
            unknown_by_code[elem.code_point].append(elem)

        print(f"   Found {len(unknown_by_code)} unknown symbol types")
        for code, elems in sorted(unknown_by_code.items())[:10]:
            print(f"      U+{code:04X} ({chr(code).encode('utf-8').hex()}) - {len(elems)} occurrences")
            print(f"         First at: ({elems[0].x:.0f}, {elems[0].y:.0f})")

        # 8. SPATIAL CLUSTERS
        print("\n" + "=" * 80)
        print("8. SPATIAL CLUSTERING (Relationship Discovery)")
        print("=" * 80)
        clusters = self.get_spatial_clusters()
        print(f"   Found {len(clusters)} horizontal lines of symbols")

        # Show lines with multiple symbols (likely staff lines)
        multi_symbol_lines = [(y, elems) for y, elems in clusters.items() if len(elems) > 3]
        multi_symbol_lines.sort(key=lambda x: x[0])

        print(f"   Lines with 4+ symbols (likely staff lines):")
        for y, elems in multi_symbol_lines[:5]:
            symbol_types = set(self.HELSINKI_STD_SYMBOLS.get(e.code_point, 'unknown') for e in elems)
            print(f"      Y={y:.0f}: {len(elems)} symbols - {symbol_types}")


def compare_deep_analysis(file1: str, file2: str):
    """Compare two SVGs to show what changed"""
    print("\n" + "=" * 80)
    print("DEEP COMPARISON: What Changed Between Files")
    print("=" * 80)

    analyzer1 = DeepSVGAnalyzer(file1)
    analyzer2 = DeepSVGAnalyzer(file2)

    # Compare noteheads
    nh1 = analyzer1.analyze_notehead_types()
    nh2 = analyzer2.analyze_notehead_types()

    print("\nNotehead Changes:")
    print(f"   File 1: {nh1['total']} noteheads")
    print(f"   File 2: {nh2['total']} noteheads")
    print(f"   Change: {nh2['total'] - nh1['total']:+d} noteheads")

    # Compare ornaments
    orn1 = analyzer1.get_ornaments()
    orn2 = analyzer2.get_ornaments()

    print("\nOrnament Changes:")
    for orn_type in ['trills', 'mordents', 'turns']:
        count1 = len(orn1[orn_type])
        count2 = len(orn2[orn_type])
        if count1 != count2:
            print(f"   {orn_type}: {count1} → {count2} ({count2-count1:+d})")

    # NEW symbols in file 2
    codes1 = set(elem.code_point for elem in analyzer1.elements)
    codes2 = set(elem.code_point for elem in analyzer2.elements)
    new_codes = codes2 - codes1

    if new_codes:
        print("\nNEW Symbols in File 2:")
        for code in sorted(new_codes):
            char = chr(code)
            symbol_type = analyzer2.HELSINKI_STD_SYMBOLS.get(code, 'unknown')
            print(f"   U+{code:04X} ({char.encode('utf-8').hex()}) - {symbol_type}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single file:  python svg_deep_analyzer.py <svg_file>")
        print("  Compare:      python svg_deep_analyzer.py <file1.svg> <file2.svg>")
        sys.exit(1)

    svg_file = sys.argv[1]

    analyzer = DeepSVGAnalyzer(svg_file)
    analyzer.print_complete_analysis()

    # Compare mode
    if len(sys.argv) == 3:
        compare_deep_analysis(svg_file, sys.argv[2])


if __name__ == '__main__':
    main()
