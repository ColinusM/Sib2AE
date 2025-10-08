#!/usr/bin/env python3
"""
Ornament Coordinator

Coordinates ornament detection across XML, SVG, and MIDI sources.
Creates comprehensive ornament registry with 3-way verification.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

from .ornament_xml_parser import XMLOrnament, OrnamentXMLParser
from .ornament_svg_parser import SVGOrnament, OrnamentSVGParser
from .orphan_midi_detector import OrphanCluster, OrphanMIDIDetector


@dataclass
class OrnamentRelationship:
    """Complete ornament with 3-way coordination"""
    ornament_id: str
    ornament_type: str  # 'trill', 'mordent', 'turn', etc.
    xml_confirmed: bool
    svg_confirmed: bool
    midi_confirmed: bool

    # Optional data fields
    xml_data: Optional[Dict] = None
    svg_data: Optional[Dict] = None
    midi_data: Optional[Dict] = None

    # Relationship
    visual_noteheads: int = 1  # Usually 1 notehead
    midi_expansion: int = 0    # N orphan notes
    relationship_type: str = "1:N"

    # Confidence
    all_sources_matched: bool = False

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        return {
            'ornament_id': self.ornament_id,
            'ornament_type': self.ornament_type,
            'xml_confirmed': self.xml_confirmed,
            'xml_data': self.xml_data,
            'svg_confirmed': self.svg_confirmed,
            'svg_data': self.svg_data,
            'midi_confirmed': self.midi_confirmed,
            'midi_data': self.midi_data,
            'relationship': {
                'visual_noteheads': self.visual_noteheads,
                'midi_expansion': self.midi_expansion,
                'type': self.relationship_type
            },
            'all_sources_matched': self.all_sources_matched
        }


class OrnamentRegistry:
    """Registry of all detected ornaments"""

    def __init__(self):
        self.ornaments: List[OrnamentRelationship] = []

    def add(self, ornament: OrnamentRelationship):
        self.ornaments.append(ornament)

    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        # Count by type
        by_type = {}
        for orn in self.ornaments:
            by_type[orn.ornament_type] = by_type.get(orn.ornament_type, 0) + 1

        # Verification stats
        xml_confirmed = sum(1 for o in self.ornaments if o.xml_confirmed)
        svg_confirmed = sum(1 for o in self.ornaments if o.svg_confirmed)
        midi_confirmed = sum(1 for o in self.ornaments if o.midi_confirmed)
        all_matched = sum(1 for o in self.ornaments if o.all_sources_matched)

        return {
            'ornaments': [o.to_dict() for o in self.ornaments],
            'summary': {
                'total_ornaments': len(self.ornaments),
                'by_type': by_type,
                'verification': {
                    'xml_confirmed': xml_confirmed,
                    'svg_confirmed': svg_confirmed,
                    'midi_confirmed': midi_confirmed,
                    'all_sources_matched': all_matched
                }
            }
        }


class OrnamentCoordinator:
    """Coordinate XML + SVG + MIDI ornament sources"""

    def __init__(self,
                 xml_ornaments: List[XMLOrnament],
                 svg_ornaments: List[SVGOrnament],
                 orphan_clusters: List[OrphanCluster],
                 universal_registry: Optional[Dict] = None):
        self.xml_ornaments = xml_ornaments
        self.svg_ornaments = svg_ornaments
        self.orphan_clusters = orphan_clusters
        self.universal_registry = universal_registry or {}

    def create_relationships(self) -> OrnamentRegistry:
        """
        Create ornament relationships by matching across sources

        Strategy:
        1. Start with XML ornaments (ground truth)
        2. Find matching SVG ornament (same spatial position)
        3. Find matching MIDI orphan cluster (temporal window)
        4. Create relationship with 3-way verification
        """
        registry = OrnamentRegistry()

        ornament_id_counter = 1

        # Process each XML ornament
        for xml_orn in self.xml_ornaments:
            # Find matching SVG ornament
            svg_orn = self._find_matching_svg_ornament(xml_orn)

            # Find matching MIDI orphan cluster
            orphan_cluster = self._find_matching_orphan_cluster(xml_orn)

            # Create relationship
            ornament_id = f"orn_{xml_orn.ornament_type}_{ornament_id_counter:03d}"
            ornament_id_counter += 1

            relationship = OrnamentRelationship(
                ornament_id=ornament_id,
                ornament_type=xml_orn.ornament_type,
                xml_confirmed=True,
                xml_data={
                    'note': xml_orn.note_pitch,
                    'measure': xml_orn.measure,
                    'part_id': xml_orn.part_id,
                    'part_name': xml_orn.part_name,
                    'voice': xml_orn.voice,
                    'staff': xml_orn.staff,
                    'placement': xml_orn.placement
                },
                svg_confirmed=svg_orn is not None,
                svg_data=self._build_svg_data(svg_orn) if svg_orn else None,
                midi_confirmed=orphan_cluster is not None,
                midi_data=self._build_midi_data(orphan_cluster) if orphan_cluster else None,
                visual_noteheads=1,
                midi_expansion=orphan_cluster.size if orphan_cluster else 0,
                relationship_type="1:N" if orphan_cluster else "1:0",
                all_sources_matched=(svg_orn is not None and orphan_cluster is not None)
            )

            registry.add(relationship)

        return registry

    def _find_matching_svg_ornament(self, xml_orn: XMLOrnament) -> Optional[SVGOrnament]:
        """
        Find SVG ornament that matches XML ornament

        Currently: Simple type matching
        Future: Could use spatial matching via Universal ID registry
        """
        for svg_orn in self.svg_ornaments:
            if svg_orn.ornament_type == xml_orn.ornament_type:
                # TODO: More sophisticated matching using notehead positions
                return svg_orn

        return None

    def _find_matching_orphan_cluster(self, xml_orn: XMLOrnament) -> Optional[OrphanCluster]:
        """
        Find orphan MIDI cluster that matches XML ornament

        Strategy:
        - Find Universal ID for the XML note (the note with the ornament tag)
        - Check if orphan cluster is RIGHT AFTER this note (ornament expansion)
        """
        # Get Universal ID for this XML note
        universal_note = self._find_universal_note(xml_orn)

        if not universal_note:
            return None

        # Get MIDI timing from Universal ID
        midi_data = universal_note.get('midi_data')
        if not midi_data:
            return None

        note_end_time = midi_data['end_time_seconds']

        # Find orphan cluster that starts right after this note
        for cluster in self.orphan_clusters:
            time_window_start, time_window_end = cluster.time_window

            # Ornament expansion should start within 0.5s after note ends
            if 0 <= (time_window_start - note_end_time) <= 0.5:
                # Pattern check: Does cluster pattern match ornament type?
                if xml_orn.ornament_type == 'trill' and cluster.is_rapid_alternation:
                    return cluster
                elif xml_orn.ornament_type in ['mordent', 'turn']:
                    # TODO: Add pattern checks for mordent/turn
                    return cluster

        return None

    def _find_universal_note(self, xml_orn: XMLOrnament) -> Optional[Dict]:
        """Find Universal ID registry entry for XML ornament note"""
        if not self.universal_registry:
            return None

        notes = self.universal_registry.get('notes', [])

        for note in notes:
            xml_data = note.get('xml_data', {})

            # Match by part, measure, pitch
            if (xml_data.get('part_id') == xml_orn.part_id and
                xml_data.get('measure') == xml_orn.measure and
                xml_data.get('note_name') == xml_orn.note_pitch):
                return note

        return None

    def _build_svg_data(self, svg_orn: SVGOrnament) -> Dict:
        """Build SVG data dict for ornament"""
        symbols_data = [
            {
                'unicode': f"U+{sym.unicode_code:04X}",
                'type': sym.symbol_type,
                'position': {'x': sym.position[0], 'y': sym.position[1]}
            }
            for sym in svg_orn.symbols
        ]

        data = {
            'symbols': symbols_data,
            'symbol_count': svg_orn.symbol_count,
            'confirmed': True
        }

        if svg_orn.notehead_position:
            data['notehead_position'] = {
                'x': svg_orn.notehead_position[0],
                'y': svg_orn.notehead_position[1]
            }

        return data

    def _build_midi_data(self, cluster: OrphanCluster) -> Dict:
        """Build MIDI data dict for orphan cluster"""
        expansion_notes = [
            {
                'pitch': note.pitch,
                'pitch_name': note.pitch_name,
                'time': note.start_time_seconds,
                'velocity': note.velocity
            }
            for note in cluster.orphan_notes
        ]

        pattern = 'alternating' if cluster.is_rapid_alternation else 'other'

        return {
            'expansion_notes': expansion_notes,
            'pattern': pattern,
            'interval_semitones': cluster.pitch_interval if cluster.is_rapid_alternation else 0,
            'time_window': {
                'start': cluster.time_window[0],
                'end': cluster.time_window[1]
            },
            'before_anchor': cluster.before_anchor.universal_id,
            'after_anchor': cluster.after_anchor.universal_id,
            'confirmed': True
        }


def main():
    import sys

    if len(sys.argv) != 5:
        print("Usage: python ornament_coordinator.py <musicxml> <midi> <svg> <registry_file>")
        sys.exit(1)

    musicxml_file = Path(sys.argv[1])
    midi_file = Path(sys.argv[2])
    svg_file = Path(sys.argv[3])
    registry_file = Path(sys.argv[4])

    # Load Universal ID registry
    with open(registry_file, 'r') as f:
        universal_registry = json.load(f)

    # 1. Parse XML ornaments
    print("Step 1: Parsing XML ornaments...")
    xml_parser = OrnamentXMLParser(musicxml_file)
    xml_ornaments = xml_parser.find_ornaments()
    print(f"✅ Found {len(xml_ornaments)} XML ornaments")

    # 2. Parse SVG ornaments
    print("\nStep 2: Parsing SVG ornaments...")
    svg_parser = OrnamentSVGParser(svg_file)
    svg_ornaments = svg_parser.find_ornaments()
    print(f"✅ Found {len(svg_ornaments)} SVG ornaments")

    # 3. Detect orphan MIDI
    print("\nStep 3: Detecting orphan MIDI notes...")
    orphan_detector = OrphanMIDIDetector(midi_file, registry_file)
    orphan_clusters = orphan_detector.detect_orphans()
    print(f"✅ Found {len(orphan_clusters)} orphan clusters")

    # 4. Coordinate all sources
    print("\nStep 4: Coordinating all sources...")
    coordinator = OrnamentCoordinator(
        xml_ornaments,
        svg_ornaments,
        orphan_clusters,
        universal_registry
    )

    registry = coordinator.create_relationships()
    print(f"✅ Created {len(registry.ornaments)} ornament relationships")

    # Print results
    print(f"\n{'='*80}")
    print("ORNAMENT COORDINATION RESULTS")
    print(f"{'='*80}\n")

    for orn in registry.ornaments:
        print(f"Ornament: {orn.ornament_id}")
        print(f"  Type: {orn.ornament_type}")
        print(f"  XML: {'✅' if orn.xml_confirmed else '❌'}")
        print(f"  SVG: {'✅' if orn.svg_confirmed else '❌'}")
        print(f"  MIDI: {'✅' if orn.midi_confirmed else '❌'}")
        print(f"  Relationship: {orn.visual_noteheads}:{orn.midi_expansion}")
        print(f"  All sources matched: {'✅' if orn.all_sources_matched else '❌'}")
        print()

    # Save registry
    output_file = Path('universal_output/ornament_coordination_registry.json')
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(registry.to_dict(), f, indent=2)

    print(f"✅ Saved registry to: {output_file}")


if __name__ == '__main__':
    main()
