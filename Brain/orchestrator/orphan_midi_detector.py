#!/usr/bin/env python3
"""
Orphan MIDI Detector

Finds MIDI notes that have no Universal ID (orphans) by using matched notes as anchors.
These orphans are likely ornament expansions (trills, mordents, grace notes).

Strategy:
1. Load Universal ID registry to identify matched notes (anchors)
2. Load MIDI file to get ALL MIDI notes
3. Find orphans = MIDI notes NOT in registry
4. Group orphans by temporal windows between anchors
"""

import json
import mido
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class MIDINote:
    """MIDI note with timing"""
    pitch: int
    pitch_name: str
    start_time_seconds: float
    end_time_seconds: float
    start_time_ticks: int
    duration_ticks: int
    velocity: int
    track_index: int
    track_name: str


@dataclass
class AnchorNote:
    """Matched note that serves as anchor"""
    universal_id: str
    pitch: int
    pitch_name: str
    start_time_seconds: float
    end_time_seconds: float
    part_id: str
    measure: int


@dataclass
class OrphanCluster:
    """Group of orphan MIDI notes between two anchors"""
    orphan_notes: List[MIDINote]
    before_anchor: AnchorNote  # Anchor before the orphans
    after_anchor: AnchorNote   # Anchor after the orphans
    time_window: Tuple[float, float]  # (start, end) in seconds

    @property
    def size(self) -> int:
        return len(self.orphan_notes)

    @property
    def is_rapid_alternation(self) -> bool:
        """Check if orphans alternate pitch (trill pattern)"""
        if len(self.orphan_notes) < 2:
            return False

        pitches = [n.pitch for n in self.orphan_notes]
        # Check if alternating between 2 pitches
        unique_pitches = set(pitches)
        if len(unique_pitches) != 2:
            return False

        # Check alternation pattern
        for i in range(len(pitches) - 1):
            if pitches[i] == pitches[i + 1]:
                return False  # Same pitch twice = not alternating

        return True

    @property
    def pitch_interval(self) -> int:
        """Get interval between alternating pitches (for trills)"""
        if not self.is_rapid_alternation:
            return 0

        pitches = sorted(set(n.pitch for n in self.orphan_notes))
        return pitches[1] - pitches[0]  # Semitone interval


class OrphanMIDIDetector:
    """Detect orphan MIDI notes between matched anchors"""

    def __init__(self, midi_file: Path, registry_file: Path):
        self.midi_file = Path(midi_file)
        self.registry_file = Path(registry_file)

        self.all_midi_notes = []
        self.anchor_notes = []
        self.orphan_notes = []
        self.orphan_clusters = []

    def detect_orphans(self) -> List[OrphanCluster]:
        """Main detection pipeline"""

        # 1. Load all MIDI notes
        self.all_midi_notes = self._load_all_midi_notes()
        print(f"✅ Loaded {len(self.all_midi_notes)} MIDI notes")

        # 2. Load anchors from registry
        self.anchor_notes = self._load_anchor_notes()
        print(f"✅ Loaded {len(self.anchor_notes)} anchor notes (matched)")

        # 3. Identify orphans
        self.orphan_notes = self._identify_orphans()
        print(f"✅ Found {len(self.orphan_notes)} orphan MIDI notes")

        # 4. Group orphans by temporal windows
        self.orphan_clusters = self._cluster_orphans_by_anchors()
        print(f"✅ Grouped into {len(self.orphan_clusters)} orphan clusters")

        return self.orphan_clusters

    def _load_all_midi_notes(self) -> List[MIDINote]:
        """Load ALL MIDI notes from file"""
        mid = mido.MidiFile(str(self.midi_file))
        ticks_per_beat = mid.ticks_per_beat

        # Assume 120 BPM (or extract from tempo events)
        seconds_per_tick = 0.5 / ticks_per_beat  # 120 BPM = 0.5 sec/beat

        all_notes = []

        for track_idx, track in enumerate(mid.tracks):
            track_name = track.name if hasattr(track, 'name') else f'Track {track_idx}'

            time = 0
            active_notes = {}

            for msg in track:
                time += msg.time

                if msg.type == 'note_on' and msg.velocity > 0:
                    active_notes[msg.note] = {
                        'start_tick': time,
                        'velocity': msg.velocity
                    }

                elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
                    if msg.note in active_notes:
                        start_tick = active_notes[msg.note]['start_tick']
                        velocity = active_notes[msg.note]['velocity']
                        duration_ticks = time - start_tick

                        # Convert to seconds
                        start_sec = start_tick * seconds_per_tick
                        end_sec = time * seconds_per_tick

                        # Pitch name
                        pitch_name = self._midi_to_pitch_name(msg.note)

                        all_notes.append(MIDINote(
                            pitch=msg.note,
                            pitch_name=pitch_name,
                            start_time_seconds=start_sec,
                            end_time_seconds=end_sec,
                            start_time_ticks=start_tick,
                            duration_ticks=duration_ticks,
                            velocity=velocity,
                            track_index=track_idx,
                            track_name=track_name
                        ))

                        del active_notes[msg.note]

        # Sort by start time
        all_notes.sort(key=lambda n: n.start_time_seconds)
        return all_notes

    def _load_anchor_notes(self) -> List[AnchorNote]:
        """Load matched notes from registry as anchors"""
        with open(self.registry_file, 'r') as f:
            registry = json.load(f)

        anchors = []

        for note_data in registry.get('notes', []):
            midi_data = note_data.get('midi_data')
            xml_data = note_data.get('xml_data')

            if midi_data:  # Has MIDI match
                anchors.append(AnchorNote(
                    universal_id=note_data['universal_id'],
                    pitch=midi_data['pitch_midi'],
                    pitch_name=midi_data['pitch_name'],
                    start_time_seconds=midi_data['start_time_seconds'],
                    end_time_seconds=midi_data['end_time_seconds'],
                    part_id=xml_data.get('part_id', 'unknown'),
                    measure=xml_data.get('measure', 0)
                ))

        # Sort by time
        anchors.sort(key=lambda a: a.start_time_seconds)
        return anchors

    def _identify_orphans(self) -> List[MIDINote]:
        """Find MIDI notes NOT in registry (orphans)"""

        # Build set of matched MIDI note identifiers
        matched_identifiers = set()
        for anchor in self.anchor_notes:
            # Use pitch + start_time as identifier (rounded to avoid float precision issues)
            identifier = (anchor.pitch, round(anchor.start_time_seconds, 3))
            matched_identifiers.add(identifier)

        # Find orphans
        orphans = []
        for midi_note in self.all_midi_notes:
            identifier = (midi_note.pitch, round(midi_note.start_time_seconds, 3))
            if identifier not in matched_identifiers:
                orphans.append(midi_note)

        return orphans

    def _cluster_orphans_by_anchors(self) -> List[OrphanCluster]:
        """Group orphans by temporal windows between anchors"""

        clusters = []

        # For each consecutive pair of anchors
        for i in range(len(self.anchor_notes) - 1):
            before_anchor = self.anchor_notes[i]
            after_anchor = self.anchor_notes[i + 1]

            # Define temporal window
            # Start: after before_anchor ends
            # End: before after_anchor starts
            window_start = before_anchor.end_time_seconds
            window_end = after_anchor.start_time_seconds

            # Find orphans in this window
            orphans_in_window = [
                orphan for orphan in self.orphan_notes
                if window_start <= orphan.start_time_seconds < window_end
            ]

            # Only create cluster if orphans found
            if orphans_in_window:
                clusters.append(OrphanCluster(
                    orphan_notes=orphans_in_window,
                    before_anchor=before_anchor,
                    after_anchor=after_anchor,
                    time_window=(window_start, window_end)
                ))

        return clusters

    def _midi_to_pitch_name(self, midi_note: int) -> str:
        """Convert MIDI note number to pitch name"""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note = notes[midi_note % 12]
        return f"{note}{octave}"

    def print_analysis(self):
        """Print detailed analysis of orphan clusters"""

        print("\n" + "=" * 80)
        print("ORPHAN MIDI ANALYSIS")
        print("=" * 80)

        print(f"\nTotal MIDI notes: {len(self.all_midi_notes)}")
        print(f"Matched (anchors): {len(self.anchor_notes)}")
        print(f"Orphans: {len(self.orphan_notes)}")

        print(f"\n{len(self.orphan_clusters)} Orphan Clusters Found:")
        print("=" * 80)

        for idx, cluster in enumerate(self.orphan_clusters, 1):
            print(f"\n📍 Cluster {idx}: {cluster.size} orphans")
            print(f"   Time window: {cluster.time_window[0]:.3f}s → {cluster.time_window[1]:.3f}s")

            # Show anchors
            print(f"\n   Before anchor:")
            print(f"      {cluster.before_anchor.pitch_name} at {cluster.before_anchor.start_time_seconds:.3f}s")
            print(f"      Universal ID: {cluster.before_anchor.universal_id[:8]}...")

            print(f"\n   After anchor:")
            print(f"      {cluster.after_anchor.pitch_name} at {cluster.after_anchor.start_time_seconds:.3f}s")
            print(f"      Universal ID: {cluster.after_anchor.universal_id[:8]}...")

            # Show orphans
            print(f"\n   Orphan notes ({cluster.size}):")
            for orphan in cluster.orphan_notes[:10]:  # Show first 10
                print(f"      {orphan.pitch_name} at {orphan.start_time_seconds:.3f}s (vel {orphan.velocity})")

            if cluster.size > 10:
                print(f"      ... and {cluster.size - 10} more")

            # Pattern analysis
            if cluster.is_rapid_alternation:
                print(f"\n   ✅ Pattern: RAPID ALTERNATION (likely trill/tremolo)")
                print(f"      Interval: {cluster.pitch_interval} semitones")
                pitches = sorted(set(n.pitch_name for n in cluster.orphan_notes))
                print(f"      Alternating: {' ↔ '.join(pitches)}")
            else:
                print(f"\n   ⚠️  Pattern: Non-alternating (grace notes? other ornament?)")


def main():
    import sys

    if len(sys.argv) != 3:
        print("Usage: python orphan_midi_detector.py <midi_file> <registry_file>")
        sys.exit(1)

    midi_file = Path(sys.argv[1])
    registry_file = Path(sys.argv[2])

    detector = OrphanMIDIDetector(midi_file, registry_file)
    clusters = detector.detect_orphans()
    detector.print_analysis()


if __name__ == '__main__':
    main()
