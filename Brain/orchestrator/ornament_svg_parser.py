#!/usr/bin/env python3
"""
Ornament SVG Parser

Wrapper around DeepSVGAnalyzer to extract ornament symbols from SVG files.
Links ornaments to their corresponding noteheads using spatial relationships.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Import the deep analyzer
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))
from svg_deep_analyzer import DeepSVGAnalyzer, SVGElement


@dataclass
class SVGOrnamentSymbol:
    """Single ornament symbol in SVG"""
    unicode_code: int  # U+F0D9, U+F07E, etc.
    symbol_type: str  # 'trill_start', 'trill_wavy', 'mordent', etc.
    position: Tuple[float, float]  # (x, y)
    utf8_hex: str  # hex representation

    def __repr__(self):
        return f"SVGOrnamentSymbol(U+{self.unicode_code:04X} '{self.symbol_type}' at ({self.position[0]:.0f}, {self.position[1]:.0f}))"


@dataclass
class SVGOrnament:
    """Complete ornament with linked notehead"""
    ornament_type: str  # 'trill', 'mordent', 'turn', etc.
    symbols: List[SVGOrnamentSymbol]  # All symbols for this ornament
    notehead_position: Optional[Tuple[float, float]] = None
    linked_notehead: Optional[SVGElement] = None

    @property
    def primary_position(self) -> Tuple[float, float]:
        """Position of the first/main symbol"""
        if self.symbols:
            return self.symbols[0].position
        return (0, 0)

    @property
    def symbol_count(self) -> int:
        return len(self.symbols)

    def __repr__(self):
        pos = self.primary_position
        nh = f" -> notehead@({self.notehead_position[0]:.0f},{self.notehead_position[1]:.0f})" if self.notehead_position else ""
        return f"SVGOrnament({self.ornament_type}, {self.symbol_count} symbols at ({pos[0]:.0f}, {pos[1]:.0f}){nh})"


class OrnamentSVGParser:
    """Parse ornaments from SVG using hex-based analysis"""

    def __init__(self, svg_file: Path):
        self.svg_file = Path(svg_file)
        self.analyzer = DeepSVGAnalyzer(str(self.svg_file))

    def find_ornaments(self) -> List[SVGOrnament]:
        """
        Find all ornaments in SVG and link to noteheads (includes grace notes)

        Returns list of SVGOrnament objects with spatial relationships
        """
        ornaments_data = self.analyzer.get_ornaments()
        noteheads_data = self.analyzer.get_noteheads()

        # Flatten noteheads
        all_noteheads = []
        for notehead_type, notehead_list in noteheads_data.items():
            all_noteheads.extend(notehead_list)

        ornament_objects = []

        # Process trills
        if ornaments_data['trills']:
            trill_ornaments = self._group_trill_symbols(ornaments_data['trills'])
            for trill in trill_ornaments:
                # Find linked notehead
                notehead = self._find_notehead_below(trill.primary_position, all_noteheads)
                if notehead:
                    trill.linked_notehead = notehead
                    trill.notehead_position = (notehead.x, notehead.y)
                ornament_objects.append(trill)

        # Process mordents
        if ornaments_data['mordents']:
            for mordent_elem in ornaments_data['mordents']:
                symbols = [SVGOrnamentSymbol(
                    unicode_code=mordent_elem.code_point,
                    symbol_type='mordent',
                    position=(mordent_elem.x, mordent_elem.y),
                    utf8_hex=mordent_elem.utf8_hex
                )]

                ornament = SVGOrnament(ornament_type='mordent', symbols=symbols)

                # Find linked notehead
                notehead = self._find_notehead_below((mordent_elem.x, mordent_elem.y), all_noteheads)
                if notehead:
                    ornament.linked_notehead = notehead
                    ornament.notehead_position = (notehead.x, notehead.y)

                ornament_objects.append(ornament)

        # Process turns
        if ornaments_data['turns']:
            for turn_elem in ornaments_data['turns']:
                symbols = [SVGOrnamentSymbol(
                    unicode_code=turn_elem.code_point,
                    symbol_type='turn',
                    position=(turn_elem.x, turn_elem.y),
                    utf8_hex=turn_elem.utf8_hex
                )]

                ornament = SVGOrnament(ornament_type='turn', symbols=symbols)

                # Find linked notehead
                notehead = self._find_notehead_below((turn_elem.x, turn_elem.y), all_noteheads)
                if notehead:
                    ornament.linked_notehead = notehead
                    ornament.notehead_position = (notehead.x, notehead.y)

                ornament_objects.append(ornament)

        # Process grace notes
        if ornaments_data.get('grace_notes'):
            for grace_elem in ornaments_data['grace_notes']:
                symbols = [SVGOrnamentSymbol(
                    unicode_code=grace_elem.code_point,
                    symbol_type='grace_notehead',
                    position=(grace_elem.x, grace_elem.y),
                    utf8_hex=grace_elem.utf8_hex
                )]

                ornament = SVGOrnament(ornament_type='grace_note', symbols=symbols)

                # Grace notes: find main notehead to the RIGHT (grace comes before)
                notehead = self._find_notehead_right((grace_elem.x, grace_elem.y), all_noteheads)
                if notehead:
                    ornament.linked_notehead = notehead
                    ornament.notehead_position = (notehead.x, notehead.y)

                ornament_objects.append(ornament)

        return ornament_objects

    def _group_trill_symbols(self, trill_elements: List[SVGElement]) -> List[SVGOrnament]:
        """
        Group trill symbols into complete ornaments
        (1 trill_start + N trill_wavy segments)
        """
        # Sort by X position
        sorted_trills = sorted(trill_elements, key=lambda e: e.x)

        # Group consecutive symbols (within 100px horizontally)
        groups = []
        current_group = []

        for elem in sorted_trills:
            if not current_group:
                current_group.append(elem)
            else:
                # Check if close to previous element
                if abs(elem.x - current_group[-1].x) < 100:
                    current_group.append(elem)
                else:
                    # Start new group
                    groups.append(current_group)
                    current_group = [elem]

        if current_group:
            groups.append(current_group)

        # Convert groups to SVGOrnament objects
        ornaments = []
        for group in groups:
            symbols = [
                SVGOrnamentSymbol(
                    unicode_code=elem.code_point,
                    symbol_type=self.analyzer.MUSIC_SYMBOLS.get(elem.code_point, 'unknown'),
                    position=(elem.x, elem.y),
                    utf8_hex=elem.utf8_hex
                )
                for elem in group
            ]

            ornaments.append(SVGOrnament(ornament_type='trill', symbols=symbols))

        return ornaments

    def _find_notehead_below(self, ornament_pos: Tuple[float, float], noteheads: List[SVGElement]) -> Optional[SVGElement]:
        """
        Find notehead below ornament (50-150px below, ±100px horizontal)

        Args:
            ornament_pos: (x, y) position of ornament
            noteheads: List of notehead elements

        Returns:
            Closest matching notehead or None
        """
        ornament_x, ornament_y = ornament_pos

        candidates = []

        for notehead in noteheads:
            dx = abs(notehead.x - ornament_x)
            dy = notehead.y - ornament_y  # Notehead should be BELOW (positive dy)

            # Check if notehead is in search area
            if dx < 100 and 50 < dy < 150:
                # Calculate distance
                distance = (dx**2 + dy**2) ** 0.5
                candidates.append((distance, notehead))

        if candidates:
            # Return closest notehead
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]

        return None

    def _find_notehead_right(self, grace_pos: Tuple[float, float], noteheads: List[SVGElement]) -> Optional[SVGElement]:
        """
        Find main notehead to the RIGHT of grace note (20-150px right, ±50px vertical)

        Args:
            grace_pos: (x, y) position of grace note
            noteheads: List of notehead elements

        Returns:
            Closest matching notehead or None
        """
        grace_x, grace_y = grace_pos

        candidates = []

        for notehead in noteheads:
            dx = notehead.x - grace_x  # Main note should be to the RIGHT (positive dx)
            dy = abs(notehead.y - grace_y)  # Vertical alignment

            # Check if notehead is in search area (right of grace note)
            if 20 < dx < 150 and dy < 50:
                # Calculate distance
                distance = (dx**2 + dy**2) ** 0.5
                candidates.append((distance, notehead))

        if candidates:
            # Return closest notehead
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]

        return None


def main():
    if len(sys.argv) != 2:
        print("Usage: python ornament_svg_parser.py <svg_file>")
        sys.exit(1)

    svg_file = Path(sys.argv[1])

    parser = OrnamentSVGParser(svg_file)
    ornaments = parser.find_ornaments()

    print(f"\n{'='*80}")
    print(f"ORNAMENT SVG ANALYSIS")
    print(f"{'='*80}\n")

    print(f"File: {svg_file.name}")
    print(f"Total ornaments found: {len(ornaments)}\n")

    if ornaments:
        print(f"{'='*80}")
        print("ORNAMENTS:")
        print(f"{'='*80}\n")

        for idx, orn in enumerate(ornaments, 1):
            print(f"{idx}. {orn.ornament_type.upper()}")
            print(f"   Symbols: {orn.symbol_count}")
            print(f"   Position: ({orn.primary_position[0]:.0f}, {orn.primary_position[1]:.0f})")

            if orn.notehead_position:
                print(f"   Linked notehead: ({orn.notehead_position[0]:.0f}, {orn.notehead_position[1]:.0f})")
                dx = orn.primary_position[0] - orn.notehead_position[0]
                dy = orn.notehead_position[1] - orn.primary_position[1]
                print(f"   Offset: Δx={dx:.0f}px, Δy={dy:.0f}px (above notehead)")
            else:
                print(f"   ⚠️  No linked notehead found")

            print(f"\n   Symbol details:")
            for sym in orn.symbols[:5]:  # Show first 5
                print(f"      • U+{sym.unicode_code:04X} ({sym.symbol_type}) at ({sym.position[0]:.0f}, {sym.position[1]:.0f})")

            if orn.symbol_count > 5:
                print(f"      ... and {orn.symbol_count - 5} more")

            print()
    else:
        print("No ornaments found in this file.\n")


if __name__ == '__main__':
    main()
