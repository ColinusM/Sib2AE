#!/usr/bin/env python3
"""
Ornament XML Parser

Parses ornament tags from MusicXML files.
Extracts ornament types (trill, mordent, turn, etc.) with their note positions.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class XMLOrnament:
    """Ornament from MusicXML with position data"""
    ornament_type: str  # 'trill', 'mordent', 'turn', 'grace_acciaccatura', 'grace_appoggiatura', etc.
    note_pitch: str  # e.g., 'G4'
    note_step: str  # e.g., 'G'
    note_octave: int  # e.g., 4
    measure: int
    part_id: str
    part_name: str
    voice: int
    staff: int

    # Optional attributes
    placement: Optional[str] = None  # 'above' or 'below'
    is_grace_note: bool = False  # True for grace notes (acciaccatura/appoggiatura)
    has_slash: Optional[bool] = None  # True=acciaccatura, False=appoggiatura

    def __repr__(self):
        return f"XMLOrnament({self.ornament_type} on {self.note_pitch}, m{self.measure}, {self.part_id})"


class OrnamentXMLParser:
    """Parse ornament tags from MusicXML"""

    SUPPORTED_ORNAMENTS = {
        'trill-mark': 'trill',
        'mordent': 'mordent',
        'inverted-mordent': 'inverted_mordent',
        'turn': 'turn',
        'inverted-turn': 'inverted_turn',
        'tremolo': 'tremolo',
        'shake': 'shake',
        'schleifer': 'schleifer',
    }

    def __init__(self, musicxml_file: Path):
        self.musicxml_file = Path(musicxml_file)
        self.tree = ET.parse(str(self.musicxml_file))
        self.root = self.tree.getroot()

        # Build part ID to name mapping
        self.part_names = self._build_part_names()

    def find_ornaments(self) -> List[XMLOrnament]:
        """Find all ornaments in MusicXML file (including grace notes)"""
        ornaments = []

        # Iterate through all parts
        for part in self.root.findall('.//part'):
            part_id = part.get('id', 'unknown')
            part_name = self.part_names.get(part_id, 'Unknown')

            # Iterate through measures
            for measure in part.findall('.//measure'):
                measure_num = int(measure.get('number', 0))

                # Iterate through notes
                for note_elem in measure.findall('.//note'):
                    # Extract note pitch (needed for both ornaments and grace notes)
                    pitch_elem = note_elem.find('pitch')
                    if pitch_elem is None:
                        continue  # Rest or unpitched note

                    step = pitch_elem.find('step').text
                    octave = int(pitch_elem.find('octave').text)
                    alter_elem = pitch_elem.find('alter')
                    alter = int(alter_elem.text) if alter_elem is not None else 0

                    # Build pitch name
                    pitch_name = self._build_pitch_name(step, octave, alter)

                    # Extract voice and staff
                    voice_elem = note_elem.find('voice')
                    voice = int(voice_elem.text) if voice_elem is not None else 1

                    staff_elem = note_elem.find('staff')
                    staff = int(staff_elem.text) if staff_elem is not None else 1

                    # CHECK 1: Is this a grace note? (acciaccatura/appoggiatura)
                    grace_elem = note_elem.find('grace')
                    if grace_elem is not None:
                        has_slash = grace_elem.get('slash') == 'yes'
                        ornament_type = 'grace_acciaccatura' if has_slash else 'grace_appoggiatura'

                        ornaments.append(XMLOrnament(
                            ornament_type=ornament_type,
                            note_pitch=pitch_name,
                            note_step=step,
                            note_octave=octave,
                            measure=measure_num,
                            part_id=part_id,
                            part_name=part_name,
                            voice=voice,
                            staff=staff,
                            is_grace_note=True,
                            has_slash=has_slash
                        ))
                        continue  # Grace notes don't have additional ornaments

                    # CHECK 2: Does note have ornaments? (trill, mordent, turn, etc.)
                    notations = note_elem.find('notations')
                    if notations is None:
                        continue

                    ornaments_elem = notations.find('ornaments')
                    if ornaments_elem is None:
                        continue

                    # Find all ornament types in this note
                    for ornament_tag, ornament_type in self.SUPPORTED_ORNAMENTS.items():
                        ornament_elem = ornaments_elem.find(ornament_tag)
                        if ornament_elem is not None:
                            placement = ornament_elem.get('placement')

                            ornaments.append(XMLOrnament(
                                ornament_type=ornament_type,
                                note_pitch=pitch_name,
                                note_step=step,
                                note_octave=octave,
                                measure=measure_num,
                                part_id=part_id,
                                part_name=part_name,
                                voice=voice,
                                staff=staff,
                                placement=placement,
                                is_grace_note=False
                            ))

        return ornaments

    def _build_part_names(self) -> Dict[str, str]:
        """Build mapping of part IDs to instrument names"""
        part_names = {}

        for part_list in self.root.findall('.//part-list/score-part'):
            part_id = part_list.get('id')
            part_name_elem = part_list.find('part-name')
            if part_name_elem is not None:
                part_names[part_id] = part_name_elem.text

        return part_names

    def _build_pitch_name(self, step: str, octave: int, alter: int) -> str:
        """Build pitch name from step, octave, alter"""
        accidental = ''
        if alter == 1:
            accidental = '#'
        elif alter == -1:
            accidental = 'b'
        elif alter == 2:
            accidental = '##'
        elif alter == -2:
            accidental = 'bb'

        return f"{step}{accidental}{octave}"


def main():
    import sys

    if len(sys.argv) != 2:
        print("Usage: python ornament_xml_parser.py <musicxml_file>")
        sys.exit(1)

    musicxml_file = Path(sys.argv[1])

    parser = OrnamentXMLParser(musicxml_file)
    ornaments = parser.find_ornaments()

    print(f"\n{'='*80}")
    print(f"ORNAMENT XML ANALYSIS")
    print(f"{'='*80}\n")

    print(f"File: {musicxml_file.name}")
    print(f"Total ornaments found: {len(ornaments)}\n")

    if ornaments:
        print(f"{'='*80}")
        print("ORNAMENTS:")
        print(f"{'='*80}\n")

        for idx, orn in enumerate(ornaments, 1):
            print(f"{idx}. {orn.ornament_type.upper()}")
            print(f"   Note: {orn.note_pitch}")
            print(f"   Measure: {orn.measure}")
            print(f"   Part: {orn.part_name} ({orn.part_id})")
            print(f"   Voice: {orn.voice}, Staff: {orn.staff}")
            if orn.is_grace_note:
                slash_info = "with slash (acciaccatura)" if orn.has_slash else "no slash (appoggiatura)"
                print(f"   Grace note: {slash_info}")
            if orn.placement:
                print(f"   Placement: {orn.placement}")
            print()
    else:
        print("No ornaments found in this file.\n")


if __name__ == '__main__':
    main()
