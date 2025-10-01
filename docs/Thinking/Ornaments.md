Ornament Detection & Synchronization Architecture

  Current State Analysis ✅

  The tied note processor demonstrates:
  - N:1 Mapping: 3 visual noteheads → 1 MIDI note (tied sequences)
  - Proportional Timing: Calculates intermediate notehead timing based on XML
  durations
  - Confidence Scoring: Primary notes (1.0) vs calculated positions (0.9-0.3)
  - Universal ID Preservation: Each notehead maintains its own Universal ID with
  tied_group_id linkage

  Ornament Challenge: Complex N:M Relationships

  Ornament Types & Their Mapping Patterns:

  | Ornament Type | Visual Noteheads         | MIDI Notes                      |
  Complexity           |
  |---------------|--------------------------|---------------------------------|---
  -------------------|
  | Trill         | 1 notehead               | 4-8 alternating notes           |
  1:N                  |
  | Mordent       | 1 notehead + symbol      | 3 notes (main-aux-main)         |
  1:N                  |
  | Turn          | 1 notehead + symbol      | 4 notes (upper-main-lower-main) |
  1:N                  |
  | Appoggiatura  | 1 grace note + 1 main    | 2 notes                         |
  2:2 (special timing) |
  | Acciaccatura  | 1 slashed grace + 1 main | 2 notes (grace very short)      |
  2:2 (special timing) |
  | Glissando     | 2 noteheads + line       | 10-20 chromatic notes           |
  2:N                  |
  | Tremolo       | 2 noteheads + beams      | 8-16 rapid alternations         |
  2:N                  |

  ---
  📋 Proposed Architecture

  1. Ornament Detection Strategy

⏺ A. MusicXML Parsing (ornament_xml_detector.py)

  @dataclass
  class OrnamentAnnotation:
      """Detected ornament from MusicXML"""
      ornament_type: str  # "trill", "mordent", "turn", "grace", "tremolo"
      primary_note: MusicXMLNote  # The main note with the ornament
      grace_notes: List[MusicXMLNote]  # Any grace notes involved
      ornament_symbol_measure: int
      ornament_symbol_beat: float
      expected_midi_expansion: int  # How many MIDI notes we expect
      timing_strategy: str  # "rapid_alternation", "grace_steal", "proportional"
      auxiliary_pitch: Optional[str]  # For trills/mordents (e.g., "A4" trills with
   "B4")

  # MusicXML Detection Logic
  def detect_ornaments_in_xml(xml_file: Path) -> List[OrnamentAnnotation]:
      """
      Parse MusicXML for ornament symbols and grace notes
      
      Detection Methods:
      1. <ornaments> tags: <trill-mark/>, <mordent/>, <turn/>
      2. <notations><ornaments> proximity to specific notes
      3. Grace notes: <grace/> tag, duration=0
      4. Grace note types: slash attribute for acciaccatura
      5. Tremolo: <tremolo> with beam count
      6. Articulations: <wavy-line> for extended trills
      """
      ornaments = []

      # Parse XML tree
      tree = ET.parse(xml_file)
      root = tree.getroot()

      for measure in root.findall('.//measure'):
          measure_num = int(measure.get('number'))

          for note in measure.findall('.//note'):
              # Check for ornament symbols
              ornament_elem = note.find('.//ornaments')
              if ornament_elem:
                  ornament_type = detect_ornament_type(ornament_elem)
                  auxiliary_pitch = calculate_auxiliary_pitch(note, ornament_type)

                  ornament = OrnamentAnnotation(
                      ornament_type=ornament_type,
                      primary_note=extract_note_data(note),
                      grace_notes=[],
                      ornament_symbol_measure=measure_num,
                      ornament_symbol_beat=calculate_beat_position(note),
                      expected_midi_expansion=estimate_midi_notes(ornament_type),
                      timing_strategy=get_timing_strategy(ornament_type),
                      auxiliary_pitch=auxiliary_pitch
                  )
                  ornaments.append(ornament)

              # Check for grace notes
              if note.find('grace') is not None:
                  # Grace note - associate with following main note
                  # (requires look-ahead logic)
                  pass

      return ornaments

  B. SVG Symbol Detection (ornament_svg_detector.py)

  def detect_ornament_symbols_in_svg(svg_file: Path) -> Dict[str, List[Tuple[float,
   float]]]:
      """
      Detect ornament symbols in SVG by visual signature
      
      Detection Strategies:
      1. Text elements: Helsinki Special Std has ornament glyphs (U+E560-E570 
  range)
      2. Path patterns: Wavy lines (trill extension), zigzag (tremolo beams)
      3. Proximity clustering: Grace notes near main noteheads
      4. Font analysis: Specific glyph codes for mordents, turns
      5. Visual geometry: Slashed grace notes (diagonal line detection)
      
      Returns:
          Dict mapping ornament types to (x, y) positions in SVG space
      """
      svg_tree = svgelements.SVG.parse(svg_file)
      ornament_positions = defaultdict(list)

      # Ornament glyph unicode ranges (Sibelius/Helsinki Special Std)
      ORNAMENT_GLYPHS = {
          '\uE566': 'trill',
          '\uE5B9': 'mordent',
          '\uE5C4': 'turn',
          '\uE4A0': 'tremolo_1',
          '\uE4A1': 'tremolo_2',
      }

      for element in svg_tree.elements():
          if isinstance(element, svgelements.Text):
              glyph = element.text
              if glyph in ORNAMENT_GLYPHS:
                  x, y = element.transform.e, element.transform.f
                  ornament_positions[ORNAMENT_GLYPHS[glyph]].append((x, y))

          # Detect wavy lines (trill extensions)
          if isinstance(element, svgelements.Path):
              if is_wavy_line_pattern(element):
                  x, y = extract_path_start_position(element)
                  ornament_positions['trill_line'].append((x, y))

      return ornament_positions

  ---
  2. MIDI Ornament Expansion Detection

⏺ A. Pattern Recognition (midi_ornament_analyzer.py)

  @dataclass
  class MIDIOrnamentCluster:
      """Group of MIDI notes detected as ornament expansion"""
      cluster_id: str
      ornament_type: str  # Detected from pattern
      midi_notes: List[MIDINote]  # All MIDI notes in the ornament
      primary_midi_note: MIDINote  # The "main" note
      auxiliary_midi_notes: List[MIDINote]  # Grace/trill/tremolo notes
      time_span_seconds: float
      pitch_pattern: List[int]  # MIDI pitch sequence [69, 71, 69, 71] for trill
      average_note_duration: float  # For rapid ornaments

  class MIDIOrnamentDetector:
      """Detect ornament patterns in MIDI note sequences"""

      def detect_ornament_clusters(self, midi_notes: List[MIDINote]) -> 
  List[MIDIOrnamentCluster]:
          """
          Analyze MIDI note patterns to detect ornament expansions
          
          Detection Heuristics:
          1. **Rapid Alternation**: 4+ notes alternating between 2 pitches in <0.5s
          2. **Grace Notes**: Very short note (duration < 0.1s) before longer note
          3. **Tremolo Pattern**: Rapid alternation between 2 specific pitches
          4. **Turn Pattern**: 4-note sequence: upper, main, lower, main
          5. **Mordent Pattern**: 3-note sequence: main, aux, main (duration < 
  0.3s)
          """
          clusters = []

          # Sort by start time
          sorted_notes = sorted(midi_notes, key=lambda n: n.start_time)

          i = 0
          while i < len(sorted_notes):
              current_note = sorted_notes[i]

              # Check for grace note pattern
              if current_note.duration < 0.1 and i + 1 < len(sorted_notes):
                  next_note = sorted_notes[i + 1]
                  time_gap = next_note.start_time - current_note.start_time

                  if time_gap < 0.15:  # Grace note steals time from main note
                      cluster = MIDIOrnamentCluster(
                          cluster_id=f"grace_{current_note.note_id}",
                          ornament_type="grace",
                          midi_notes=[current_note, next_note],
                          primary_midi_note=next_note,
                          auxiliary_midi_notes=[current_note],
                          time_span_seconds=next_note.end_time -
  current_note.start_time,
                          pitch_pattern=[current_note.pitch, next_note.pitch],
                          average_note_duration=current_note.duration
                      )
                      clusters.append(cluster)
                      i += 2
                      continue

              # Check for rapid alternation (trill/tremolo)
              rapid_sequence = self._extract_rapid_sequence(sorted_notes[i:])
              if len(rapid_sequence) >= 4:
                  if self._is_alternating_pattern(rapid_sequence):
                      cluster = self._create_trill_cluster(rapid_sequence)
                      clusters.append(cluster)
                      i += len(rapid_sequence)
                      continue

              i += 1

          return clusters

      def _extract_rapid_sequence(self, notes: List[MIDINote], max_gap: float = 
  0.1) -> List[MIDINote]:
          """Extract sequence of notes with minimal time gaps"""
          sequence = [notes[0]]

          for i in range(1, len(notes)):
              time_gap = notes[i].start_time - notes[i-1].end_time
              if time_gap > max_gap:
                  break
              sequence.append(notes[i])

          return sequence

      def _is_alternating_pattern(self, notes: List[MIDINote]) -> bool:
          """Check if notes alternate between 2 pitches"""
          if len(notes) < 4:
              return False

          unique_pitches = set(n.pitch for n in notes)
          if len(unique_pitches) != 2:
              return False

          # Check alternation
          for i in range(2, len(notes)):
              if notes[i].pitch == notes[i-1].pitch:
                  return False

          return True

  ---
  3. Universal ID Relationship System for N:M Mappings

⏺ A. Ornament Group Architecture (ornament_coordinator.py)

  @dataclass
  class OrnamentGroup:
      """
      Represents an ornament with N:M notehead-to-MIDI relationships
      
      Similar to TiedNoteGroup but handles complex multi-directional mappings
      """
      ornament_id: str  # Universal ID for the ornament group
      ornament_type: str  # "trill", "mordent", "turn", "grace", etc.

      # Visual elements (from XML/SVG)
      visual_noteheads: List[MusicXMLNote]  # Primary note + any grace notes
      ornament_symbol_universal_id: Optional[str]  # Universal ID for the symbol 
  itself

      # MIDI expansion
      midi_expansion: List[MIDINote]  # All MIDI notes generated by ornament
      primary_midi_note: MIDINote  # The "main" MIDI note for timing reference

      # Relationship tracking
      notehead_to_midi_map: Dict[str, List[str]]  # Notehead UUID -> List of MIDI 
  UUIDs
      midi_to_notehead_map: Dict[str, str]  # MIDI UUID -> Notehead UUID 
  (many-to-one)

      # Timing coordination
      ornament_start_time: float  # When ornament begins
      ornament_end_time: float  # When ornament completes
      timing_distribution: List[Tuple[str, float]]  # (MIDI UUID, start_time)

      # After Effects synchronization
      visual_display_strategy: str  # "single_notehead", "all_noteheads", 
  "symbol_only"
      animation_keyframe_assignment: str  # "primary_only", "distributed", 
  "cumulative"

  # Universal ID Enhancement
  @dataclass
  class UniversalIDRelationship:
      """
      Tracks complex relationships between visual and audio elements
      
      Extends the current 1:1 assumption to handle N:M cases
      """
      relationship_id: str  # UUID for this relationship
      relationship_type: str  # "1:1" (normal), "N:1" (tied), "1:N" (ornament), 
  "N:M" (complex)

      # Visual side (XML/SVG)
      visual_universal_ids: List[str]  # All notehead UUIDs involved
      primary_visual_id: str  # The "main" notehead

      # Audio side (MIDI)
      audio_universal_ids: List[str]  # All MIDI note UUIDs involved
      primary_audio_id: str  # The "main" MIDI note

      # Synchronization metadata
      timing_strategy: str  # How to distribute timing
      confidence: float  # Match confidence
      coordination_metadata: Dict  # Additional context

  class OrnamentCoordinator:
      """
      Coordinates ornaments across XML, SVG, and MIDI domains
      
      Integrates with existing Note Coordinator and Tied Note Processor
      """

      def __init__(self, verbose: bool = True):
          self.ornament_groups: Dict[str, OrnamentGroup] = {}
          self.universal_relationships: List[UniversalIDRelationship] = {}
          self.verbose = verbose

      def coordinate_ornaments(
          self,
          xml_ornaments: List[OrnamentAnnotation],
          svg_ornaments: Dict[str, List[Tuple[float, float]]],
          midi_clusters: List[MIDIOrnamentCluster],
          existing_registry: Dict  # From Note Coordinator
      ) -> Dict:
          """
          Three-way matching: XML ornaments ↔ SVG symbols ↔ MIDI expansions
          
          Matching Strategy:
          1. Start with XML ornaments (semantic source of truth)
          2. Match to SVG symbols by proximity (within 50px)
          3. Match to MIDI clusters by timing + pitch pattern
          4. Create OrnamentGroup for each matched triplet
          5. Generate Universal ID relationships
          """

          for xml_ornament in xml_ornaments:
              # Find matching SVG symbol
              svg_match = self._find_svg_symbol_by_proximity(
                  xml_ornament, svg_ornaments
              )

              # Find matching MIDI cluster
              midi_match = self._find_midi_cluster_by_pattern(
                  xml_ornament, midi_clusters
              )

              if svg_match and midi_match:
                  ornament_group = self._create_ornament_group(
                      xml_ornament, svg_match, midi_match
                  )
                  self.ornament_groups[ornament_group.ornament_id] = ornament_group

                  # Create Universal ID relationships
                  relationship =
  self._create_universal_relationship(ornament_group)
                  self.universal_relationships.append(relationship)

          return self._generate_ornament_registry()

      def _create_ornament_group(
          self,
          xml_ornament: OrnamentAnnotation,
          svg_symbol: Tuple[float, float],
          midi_cluster: MIDIOrnamentCluster
      ) -> OrnamentGroup:
          """
          Create unified ornament group with Universal ID assignments
          
          Universal ID Strategy:
          - Ornament group: New UUID (e.g., "ornament_trill_001")
          - Each MIDI note in expansion: Gets sub-ID (e.g., 
  "ornament_trill_001_midi_0")
          - Visual notehead: Keeps its XML-derived UUID
          - Ornament symbol: New UUID for SVG symbol element
          
          Relationship:
          1 visual notehead → N MIDI notes (all share ornament_group_id)
          """
          ornament_id = str(uuid.uuid4())

          # Assign sub-IDs to MIDI expansion notes
          midi_expansion_with_ids = []
          notehead_to_midi_map = {}
          midi_to_notehead_map = {}

          primary_notehead_uuid = xml_ornament.primary_note.universal_id
          notehead_to_midi_map[primary_notehead_uuid] = []

          for i, midi_note in enumerate(midi_cluster.midi_notes):
              # Create sub-ID for this MIDI note
              midi_sub_id = f"{ornament_id}_midi_{i}"
              midi_note.note_id = midi_sub_id  # Override original ID
              midi_expansion_with_ids.append(midi_note)

              # Establish bidirectional mapping
              notehead_to_midi_map[primary_notehead_uuid].append(midi_sub_id)
              midi_to_notehead_map[midi_sub_id] = primary_notehead_uuid

          ornament_group = OrnamentGroup(
              ornament_id=ornament_id,
              ornament_type=xml_ornament.ornament_type,
              visual_noteheads=[xml_ornament.primary_note] +
  xml_ornament.grace_notes,
              ornament_symbol_universal_id=f"{ornament_id}_symbol",
              midi_expansion=midi_expansion_with_ids,
              primary_midi_note=midi_cluster.primary_midi_note,
              notehead_to_midi_map=notehead_to_midi_map,
              midi_to_notehead_map=midi_to_notehead_map,
              ornament_start_time=midi_cluster.midi_notes[0].start_time,
              ornament_end_time=midi_cluster.midi_notes[-1].end_time,
              timing_distribution=[(n.note_id, n.start_time) for n in
  midi_expansion_with_ids],
              visual_display_strategy="single_notehead",
              animation_keyframe_assignment="cumulative"
          )

          return ornament_group

  ---
  4. After Effects Synchronization Strategy

  Keyframe Assignment Options:

  1. Single Notehead with Cumulative Audio (Recommended)
    - Visual: 1 notehead animates
    - Audio: All MIDI expansion notes' keyframes are summed/blended
    - Result: Notehead pulses with combined amplitude of trill notes
  2. Distributed Keyframe Assignment
    - Visual: 1 notehead
    - Audio: Only primary MIDI note's keyframes used
    - Ornament MIDI notes: Exported separately with ornament_group_id tag
  3. Multi-Layer Approach
    - Visual: Duplicate notehead layer for each MIDI note in expansion
    - Audio: Each layer gets individual MIDI note's keyframes
    - Result: Overlapping noteheads simulate rapid alternation

  def generate_ae_keyframes_for_ornaments(
      ornament_groups: Dict[str, OrnamentGroup]
  ) -> Dict:
      """
      Generate After Effects keyframe data with ornament synchronization
      
      Keyframe Strategy:
      - Primary notehead: Gets cumulative amplitude from all MIDI expansion notes
      - Ornament symbol: Optional animation trigger
      - Grace notes: Individual keyframes with timing offset
      """
      ae_data = {}

      for ornament_id, ornament_group in ornament_groups.items():
          if ornament_group.animation_keyframe_assignment == "cumulative":
              # Sum amplitudes from all MIDI expansion notes
              cumulative_keyframes = blend_keyframe_data(
                  [midi_note.keyframes for midi_note in
  ornament_group.midi_expansion]
              )

              ae_data[ornament_group.primary_visual_id] = {
                  'universal_id': ornament_group.primary_visual_id,
                  'ornament_group_id': ornament_id,
                  'ornament_type': ornament_group.ornament_type,
                  'keyframes': cumulative_keyframes,
                  'midi_expansion_count': len(ornament_group.midi_expansion),
                  'timing_source': 'ornament_cumulative'
              }

          elif ornament_group.animation_keyframe_assignment == "distributed":
              # Each MIDI note gets separate keyframe export
              for i, midi_note in enumerate(ornament_group.midi_expansion):
                  sub_layer_id = f"{ornament_group.primary_visual_id}_ornament_{i}"
                  ae_data[sub_layer_id] = {
                      'universal_id': sub_layer_id,
                      'ornament_group_id': ornament_id,
                      'ornament_position': i,
                      'keyframes': midi_note.keyframes,
                      'timing_source': 'ornament_distributed'
                  }

      return ae_data

  ---
  5. Implementation Architecture

⏺ New Orchestrator Integration:

  Brain/orchestrator/
  ├── note_coordinator.py          # Existing 1:1 coordination
  ├── tied_note_processor.py       # Existing N:1 coordination
  ├── ornament_coordinator.py      # NEW: 1:N and N:M coordination
  ├── ornament_xml_detector.py     # NEW: MusicXML ornament detection
  ├── ornament_svg_detector.py     # NEW: SVG symbol detection
  ├── midi_ornament_analyzer.py    # NEW: MIDI pattern recognition
  └── universal_relationship.py    # NEW: Generalized N:M relationship tracking

  Pipeline Execution Flow:

  1. Note Coordinator (Existing)
     ↓
     Creates base Universal ID registry (1:1 mappings)

  2. Tied Note Processor (Existing)
     ↓
     Enhances registry with N:1 relationships (tied notes)

  3. Ornament Coordinator (NEW)
     ↓
     Detects ornaments in XML/SVG/MIDI
     ↓
     Matches ornament patterns across domains
     ↓
     Creates 1:N relationships (ornament expansions)
     ↓
     Generates OrnamentGroup objects with sub-IDs
     ↓
     Enhances Universal ID registry with N:M relationships

  4. Audio Pipeline (Enhanced)
     ↓
     MIDI separator: Respects ornament groupings
     ↓
     Audio renderer: Processes ornament MIDI notes
     ↓
     Keyframe generator: Applies cumulative/distributed strategies

  5. After Effects Import (Enhanced)
     ↓
     Single notehead + cumulative keyframes
     OR
     Multi-layer with distributed keyframes

  ---
  🎯 Key Design Principles

  1. Backward Compatibility: Existing 1:1 and N:1 (tied) logic remains unchanged
  2. Modular Detection: XML, SVG, MIDI ornament detection are independent modules
  3. Confidence Scoring: Similar to tied notes, ornament matches have confidence
  levels
  4. Universal ID Hierarchy: Ornament groups have parent IDs, MIDI expansions have
  sub-IDs
  5. Flexible Keyframe Strategies: Cumulative vs distributed AE synchronization
  6. Graceful Fallbacks: If ornament detection fails, falls back to 1:1 processing

  ---
  📊 Expected Output Examples

  Trill Example:

  {
    "ornament_group": {
      "ornament_id": "b5f3a8c2-...",
      "ornament_type": "trill",
      "visual_noteheads": [
        {"universal_id": "2584802d-...", "pitch": "A4", "measure": 5}
      ],
      "midi_expansion": [
        {"universal_id": "b5f3a8c2-..._midi_0", "pitch": 69, "start": 7.50},
        {"universal_id": "b5f3a8c2-..._midi_1", "pitch": 71, "start": 7.62},
        {"universal_id": "b5f3a8c2-..._midi_2", "pitch": 69, "start": 7.75},
        {"universal_id": "b5f3a8c2-..._midi_3", "pitch": 71, "start": 7.87}
      ],
      "animation_strategy": "cumulative",
      "ae_keyframes": {
        "notehead_A4_M5": [
          [0, 42],  // Cumulative amplitude from 4 rapid notes
          [1, 68],
          [2, 55],
          [3, 71]
        ]
      }
    }
  }

  ---
  💡 Implementation Priorities

  Phase 1: Detection Infrastructure
  - MusicXML ornament parser
  - MIDI pattern recognizer
  - Basic ornament type classification

  Phase 2: Coordination System
  - OrnamentGroup data structure
  - Universal ID relationship tracking
  - Three-way matching logic

  Phase 3: Keyframe Strategies
  - Cumulative amplitude blending
  - Distributed layer export
  - AE integration testing

  Phase 4: Production Hardening
  - Confidence scoring refinement
  - Edge case handling (nested ornaments, cross-staff)
  - Performance optimization

  ---
  This architecture leverages your existing tied note processor's elegant pattern
  while extending it to handle the complex world of musical ornaments. The key
  insight is treating ornaments as "inverse tied notes" - where tied notes are N
  visual → 1 audio, ornaments are 1 visual → N audio, unified under a generalized
  N:M relationship framework.

  What aspects would you like to explore deeper or start prototyping?