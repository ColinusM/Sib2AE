#!/usr/bin/env python3
"""
Ornament Symbol Creator

Creates individual SVG files for each confirmed ornament symbol.
Only extracts ornaments that have been confirmed through XML matching.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Tuple
import sys


class OrnamentSymbolCreator:
    """Create individual SVG files for confirmed ornaments"""

    def __init__(self, ornament_registry_file: Path, full_svg_file: Path, output_dir: Path):
        self.ornament_registry_file = Path(ornament_registry_file)
        self.full_svg_file = Path(full_svg_file)
        self.output_dir = Path(output_dir)

        # Load registry
        with open(self.ornament_registry_file, 'r') as f:
            self.registry = json.load(f)

        # Parse full SVG
        self.svg_tree = ET.parse(str(self.full_svg_file))
        self.svg_root = self.svg_tree.getroot()

        # Get SVG namespace
        self.ns = {'svg': 'http://www.w3.org/2000/svg'}

    def create_all_ornament_svgs(self) -> int:
        """
        Create SVG files for all confirmed ornaments

        Returns:
            Number of ornament SVGs created
        """
        created_count = 0

        for ornament in self.registry['ornaments']:
            # Only extract XML-confirmed ornaments
            if not ornament.get('xml_confirmed', False):
                continue

            # Only extract if SVG data is present
            if not ornament.get('svg_confirmed', False):
                continue

            svg_data = ornament.get('svg_data')
            if not svg_data:
                continue

            # Create ornament SVG
            ornament_id = ornament['ornament_id']
            ornament_type = ornament['ornament_type']

            svg_file = self._create_ornament_svg(ornament_id, ornament_type, svg_data)

            if svg_file:
                created_count += 1
                print(f"✅ Created: {svg_file.name}")
                print(f"   Type: {ornament_type}")
                print(f"   Symbols: {svg_data['symbol_count']}")
                if svg_data.get('notehead_position'):
                    nh_pos = svg_data['notehead_position']
                    print(f"   Linked to notehead at ({nh_pos['x']:.0f}, {nh_pos['y']:.0f})")

        return created_count

    def _create_ornament_svg(self, ornament_id: str, ornament_type: str, svg_data: Dict) -> Path:
        """
        Create individual SVG file for an ornament

        Args:
            ornament_id: Unique ornament identifier
            ornament_type: Type of ornament (trill, mordent, etc.)
            svg_data: SVG symbol data from registry

        Returns:
            Path to created SVG file
        """
        # Get symbol positions
        symbols = svg_data['symbols']

        # Calculate bounding box for all symbols
        positions = [s['position'] for s in symbols]
        min_x = min(p['x'] for p in positions)
        max_x = max(p['x'] for p in positions)
        min_y = min(p['y'] for p in positions)
        max_y = max(p['y'] for p in positions)

        # Add padding
        padding = 20
        bbox_x = min_x - padding
        bbox_y = min_y - padding
        bbox_width = (max_x - min_x) + 2 * padding
        bbox_height = (max_y - min_y) + 2 * padding

        # Extract matching text elements from full SVG
        ornament_elements = self._find_matching_elements(symbols)

        if not ornament_elements:
            print(f"⚠️  No matching elements found for {ornament_id}")
            return None

        # Create new SVG with just the ornament symbols
        svg_ns = "http://www.w3.org/2000/svg"
        new_svg = ET.Element('{%s}svg' % svg_ns)
        new_svg.set('xmlns', svg_ns)
        new_svg.set('viewBox', f"{bbox_x} {bbox_y} {bbox_width} {bbox_height}")
        new_svg.set('width', f"{bbox_width}")
        new_svg.set('height', f"{bbox_height}")

        # Add ornament elements
        for elem in ornament_elements:
            # Clone element
            new_elem = ET.Element(elem.tag, elem.attrib)
            new_elem.text = elem.text
            new_svg.append(new_elem)

        # Save to file
        output_file = self.output_dir / f"{ornament_id}.svg"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        tree = ET.ElementTree(new_svg)
        tree.write(str(output_file), encoding='utf-8', xml_declaration=True)

        return output_file

    def _find_matching_elements(self, symbols: List[Dict]) -> List[ET.Element]:
        """
        Find SVG text elements matching the ornament symbols

        Args:
            symbols: List of symbol data with positions

        Returns:
            List of matching XML elements
        """
        matching_elements = []

        # Build position map for quick lookup
        symbol_positions = {(s['position']['x'], s['position']['y']): s for s in symbols}

        # Search all text elements in SVG
        for text_elem in self.svg_root.findall('.//svg:text', self.ns):
            # Get position
            x_str = text_elem.get('x')
            y_str = text_elem.get('y')

            if not x_str or not y_str:
                continue

            try:
                x = float(x_str)
                y = float(y_str)
            except ValueError:
                continue

            # Check if this position matches any symbol
            # Allow small tolerance for float precision
            for (sym_x, sym_y), symbol_data in symbol_positions.items():
                if abs(x - sym_x) < 1.0 and abs(y - sym_y) < 1.0:
                    matching_elements.append(text_elem)
                    break

        return matching_elements


def main():
    if len(sys.argv) != 4:
        print("Usage: python ornament_symbol_creator.py <registry_file> <full_svg_file> <output_dir>")
        sys.exit(1)

    registry_file = Path(sys.argv[1])
    full_svg_file = Path(sys.argv[2])
    output_dir = Path(sys.argv[3])

    print(f"\n{'='*80}")
    print("ORNAMENT SYMBOL CREATOR")
    print(f"{'='*80}\n")

    print(f"Registry: {registry_file}")
    print(f"Full SVG: {full_svg_file}")
    print(f"Output: {output_dir}\n")

    creator = OrnamentSymbolCreator(registry_file, full_svg_file, output_dir)
    created_count = creator.create_all_ornament_svgs()

    print(f"\n{'='*80}")
    print(f"✅ Created {created_count} ornament SVG file(s)")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
