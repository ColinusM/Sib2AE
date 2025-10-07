#!/usr/bin/env python3
  """
  Ornament XML Detector

  Detects ornaments from MusicXML files including:
  - Trill marks, mordents, turns
  - Grace notes (acciaccaturas, appoggiaturas)
  - Tremolo markings
  - Ornament symbols and their associated notes

  Integrates with existing XMLTemporalParser patterns.
  """

      """Detected ornament from MusicXML"""
      ornament_type: str  # "trill", "mordent", "turn", "grace", "tremolo"
      ornament_id: str  # Unique identifier for this ornament
      primary_note: MusicXMLNote  # The main note with the ornament
      grace_notes: List[MusicXMLNote] = field(default_factory=list)  # Any grace 
  notes involved
      ornament_symbol_measure: int = 0
      ornament_symbol_beat: float = 0.0
      expected_midi_expansion: int = 0  # How many MIDI notes we expect
      timing_strategy: str = "unknown"  # "rapid_alternation", "grace_steal", 
  "proportional"
      auxiliary_pitch: Optional[str] = None  # For trills/mordents (e.g., "A4" 
  trills with "B4")
      ornament_attributes: Dict = field(default_factory=dict)  # Additional XML 
  attributes
      confidence: float = 1.0  # Confidence in ornament detection

      """
      Detects ornaments in MusicXML files.

      Uses the same coordinate system and parsing patterns as XMLTemporalParser.
      """

          """
          Initialize ornament detector.

          Args:
              musicxml_path: Path to MusicXML file
              verbose: Whether to print detection information
          """

          # Use XMLTemporalParser for note extraction

          # Ornament detection results

          """
          Detect all ornaments in the MusicXML file.

          Returns:
              List of OrnamentAnnotation objects
          """

          # Step 1: Detect ornament symbols (trills, mordents, turns)

          # Step 2: Detect grace notes

          # Step 3: Detect tremolo markings

          # Combine all detected ornaments

          """
          Detect ornament symbols: trills, mordents, turns.

          MusicXML Structure:
          <note>
              <notations>
                  <ornaments>
                      <trill-mark/>
                      <!-- or <mordent/>, <turn/>, etc. -->
                  </ornaments>
              </notations>
          </note>
          """

                      # Skip rest notes

                      # Check for ornament elements

                      # Detect specific ornament types

                          expected_expansion = 6  # Typical trill has ~6 
  alternations

                          expected_expansion = 3  # main-aux-main

                          expected_expansion = 4  # upper-main-lower-main

                          # Extract note data

                              # Calculate auxiliary pitch for trills/mordents

          """
          Detect grace notes (acciaccaturas, appoggiaturas).

          MusicXML Structure:
          <note>
              <grace slash="yes"/>  <!-- acciaccatura (slashed) -->
              <!-- or <grace/> for appoggiatura -->
              <pitch>...</pitch>
          </note>
          <note>  <!-- The main note follows -->
              <pitch>...</pitch>
          </note>
          """

                      # Check if this is a grace note

                          # Determine grace note type

                          # Extract grace note

                          # Find the following main note

                              # Make sure it's not another grace note

                              expected_midi_expansion=2,  # Grace + main note
                              timing_strategy="grace_steal",  # Grace steals time 
  from main

                              # Skip the main note in next iteration

          """
          Detect tremolo markings.

          MusicXML Structure:
          <note>
              <notations>
                  <ornaments>
                      <tremolo type="single">3</tremolo>  <!-- 3 beams -->
                  </ornaments>
              </notations>
          </note>
          """

                          # Calculate expected MIDI expansion based on tremolo 
  marks
                          # 3 marks = 32nd notes, typical expansion ~8-16 notes

          """Extract MusicXMLNote from XML element."""

              # Extract pitch

              # Build pitch string

              # Extract duration

              # Get default X/Y coordinates (will be refined later)

              # Create MusicXMLNote

                  beat_position=0.0,  # Will be calculated if needed

          """
          Calculate the auxiliary pitch for ornaments like trills and mordents.

          Standard convention:
          - Trill: Upper neighbor (e.g., A4 trills with B4)
          - Mordent: Lower neighbor (e.g., A4 mordents with G4)
          - Inverted mordent: Upper neighbor
          """

              # Parse primary pitch

              # Determine interval

                  # Upper neighbor (typically +2 semitones for major second)

                  # Lower neighbor

                  # Turn uses both upper and lower, return upper for reference

              # Convert back to pitch string

          """Convert MIDI number to pitch string like 'A4', 'C#3'."""

          """Get comprehensive summary of detected ornaments."""

      """CLI interface for testing ornament detection."""

          # Create detector

          # Detect ornaments

          # Get summary

          # Print results

          # Save to JSON

> '/Users/colinmignot/Claude 
Code/Sib2Ae/Brain/orchestrator/midi_ornament_analyzer.py''/Users/colinmignot/Claude
 Code/Sib2Ae/Brain/orchestrator/ornament_coordinator.py'\
smae thing for these two 

⏺ Read(Brain/orchestrator/midi_ornament_analyzer.py)
  ⎿  Read 598 lines (ctrl+o to expand)

⏺ Read(Brain/orchestrator/ornament_coordinator.py)
  ⎿  Read 544 lines (ctrl+o to expand)

⏺ midi_ornament_analyzer.py

  #!/usr/bin/env python3
  """
  MIDI Ornament Analyzer

  Detects ornament patterns in MIDI note sequences using heuristic pattern 
  recognition:
  - Rapid alternations (trills, tremolos)
  - Grace note patterns (short notes before longer notes)
  - Turn and mordent patterns
  - Cluster analysis for ornament expansions

  Integrates with existing MIDIMatcher patterns.
  """

      """Group of MIDI notes detected as ornament expansion"""
      cluster_id: str
      ornament_type: str  # Detected from pattern: "trill", "tremolo", "grace", 
  "mordent", "turn"
      midi_notes: List[MIDINote]  # All MIDI notes in the ornament
      primary_midi_note: MIDINote  # The "main" note
      auxiliary_midi_notes: List[MIDINote] = field(default_factory=list)  # 
  Grace/trill/tremolo notes
      time_span_seconds: float = 0.0
      pitch_pattern: List[int] = field(default_factory=list)  # MIDI pitch sequence
   [69, 71, 69, 71] for trill
      average_note_duration: float = 0.0  # For rapid ornaments
      confidence: float = 1.0  # Confidence in ornament detection
      detection_heuristics: Dict = field(default_factory=dict)  # Heuristic details

      """
      Detect ornament patterns in MIDI note sequences.

      Uses heuristic analysis to identify ornament expansions based on:
      - Timing patterns (rapid succession, grace note stealing)
      - Pitch patterns (alternation, neighbor tones)
      - Duration patterns (very short notes)
      """

      # Heuristic thresholds
      GRACE_NOTE_MAX_DURATION = 0.1  # seconds
      GRACE_NOTE_MAX_GAP = 0.15  # seconds
      RAPID_NOTE_MAX_GAP = 0.1  # seconds
      RAPID_MIN_NOTES = 4  # Minimum notes for trill/tremolo
      MORDENT_MAX_DURATION = 0.3  # seconds total
      TURN_MAX_DURATION = 0.5  # seconds total

          """
          Initialize MIDI ornament detector.

          Args:
              verbose: Whether to print detection information
          """

          """
          Analyze MIDI note patterns to detect ornament expansions.

          Detection Heuristics:
          1. **Rapid Alternation**: 4+ notes alternating between 2 pitches in <0.5s
          2. **Grace Notes**: Very short note (duration < 0.1s) before longer note
          3. **Tremolo Pattern**: Rapid alternation between 2 specific pitches
          4. **Turn Pattern**: 4-note sequence: upper, main, lower, main
          5. **Mordent Pattern**: 3-note sequence: main, aux, main (duration < 
  0.3s)

          Args:
              midi_notes: List of MIDI notes from MIDI file

          Returns:
              List of detected MIDIOrnamentCluster objects
          """

          # Sort by start time

              # Check for grace note pattern

                  # Mark processed indices

              # Check for rapid alternation (trill/tremolo)

                  # Mark processed indices

              # Check for turn pattern

                  # Mark processed indices

              # Check for mordent pattern

                  # Mark processed indices

          """
          Detect grace note pattern: very short note before longer note.

          Pattern: Short note (< 0.1s) followed by longer note with minimal gap
          """

          # Check grace note characteristics

          # Ensure notes are from same instrument/track

          # Detected grace note pattern

          # Determine if acciaccatura (very short) or appoggiatura

          """
          Detect rapid alternation pattern (trill/tremolo).

          Pattern: 4+ notes alternating between 2 pitches with minimal gaps
          """
          # Extract rapid sequence

          # Check if alternating pattern

          # Determine if trill or tremolo based on interval

          # Primary note is typically the first or most common pitch

          """
          Detect turn pattern: 4-note sequence (upper neighbor, main, lower 
  neighbor, main).

          Pattern: Main note with upper and lower neighbor notes
          """

          # Extract 4-note sequence

          # Check time span

          # Check instrument consistency

          # Check pitch pattern: should have 3 unique pitches with main appearing 
  twice

          # Find the main pitch (appears twice)

          # Check if it forms upper-main-lower-main or similar pattern
          # (allowing some flexibility in order)

          """
          Detect mordent pattern: 3-note sequence (main, auxiliary, main).

          Pattern: Quick alternation between main note and neighbor
          """

          # Extract 3-note sequence

          # Check time span

          # Check instrument consistency

          # Check pitch pattern: first and last should be same pitch

          # Check interval (should be small, typically 1-2 semitones)

          # Check for rapid succession

          """Extract sequence of notes with minimal time gaps."""

              # Check instrument consistency

          """Check if notes alternate between 2 pitches."""

          # Check alternation (no two consecutive notes should have same pitch)

          """Get comprehensive summary of detected clusters."""

      """CLI interface for testing MIDI ornament detection."""

          # Load MIDI file and extract notes

          # Simple MIDI note extraction (for testing)

          # Create detector

          # Detect ornament clusters

          # Get summary

          # Print results

          # Save to JSON

  ornament_coordinator.py

  #!/usr/bin/env python3
  """
  Ornament Coordinator

  Coordinates ornaments across XML, SVG, and MIDI domains, creating N:M 
  relationships
  between visual noteheads and MIDI expansion notes. Extends the Universal ID 
  system
  to handle complex ornament mappings.

  Integrates with:
  - OrnamentXMLDetector: Detects ornaments in MusicXML
  - MIDIOrnamentDetector: Detects ornament patterns in MIDI
  - Note Coordinator: Base Universal ID registry

  Key Responsibilities:
  - Match XML ornaments with MIDI clusters
  - Create OrnamentGroup objects with sub-IDs
  - Generate UniversalIDRelationship mappings (1:N, N:M)
  - Enhance existing registry with ornament metadata
  """

      """
      Represents an ornament with N:M notehead-to-MIDI relationships.

      Similar to TiedNoteGroup but handles complex multi-directional mappings where
      1 visual notehead can generate N MIDI notes (trill), or N visual noteheads
      can generate M MIDI notes (complex grace note sequences).
      """
      ornament_id: str  # Universal ID for the ornament group
      ornament_type: str  # "trill", "mordent", "turn", "grace", "tremolo"

      # Visual elements (from XML/SVG)
      visual_noteheads: List[MusicXMLNote]  # Primary note + any grace notes
      ornament_symbol_universal_id: Optional[str] = None  # Universal ID for the 
  symbol itself

      # MIDI expansion
      midi_expansion: List[MIDINote] = field(default_factory=list)  # All MIDI 
  notes generated by ornament
      primary_midi_note: Optional[MIDINote] = None  # The "main" MIDI note for 
  timing reference

      # Relationship tracking
      notehead_to_midi_map: Dict[str, List[str]] = field(default_factory=dict)  # 
  Notehead UUID -> List of MIDI UUIDs
      midi_to_notehead_map: Dict[str, str] = field(default_factory=dict)  # MIDI 
  UUID -> Notehead UUID (many-to-one)

      # Timing coordination
      ornament_start_time: float = 0.0  # When ornament begins
      ornament_end_time: float = 0.0  # When ornament completes
      timing_distribution: List[Tuple[str, float]] = field(default_factory=list)  #
   (MIDI UUID, start_time)

      # After Effects synchronization
      visual_display_strategy: str = "single_notehead"  # "single_notehead", 
  "all_noteheads", "symbol_only"
      animation_keyframe_assignment: str = "cumulative"  # "primary_only", 
  "distributed", "cumulative"

      # Matching metadata
      match_confidence: float = 1.0  # Confidence in XML-MIDI matching
      match_method: str = "unknown"  # "timing_proximity", "pitch_pattern", 
  "manual"

      """
      Tracks complex relationships between visual and audio elements.

      Extends the current 1:1 assumption to handle N:M cases for ornaments.
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
      timing_strategy: str  # How to distribute timing: "cumulative", 
  "distributed", "primary_only"
      confidence: float  # Match confidence (0.0-1.0)
      coordination_metadata: Dict = field(default_factory=dict)  # Additional 
  context

      """
      Coordinates ornaments across XML, SVG, and MIDI domains.

      Integrates with existing Note Coordinator and Tied Note Processor,
      extending the Universal ID system to handle ornament N:M relationships.
      """

          """
          Initialize ornament coordinator.

          Args:
              verbose: Whether to print coordination information
          """

          """
          Three-way matching: XML ornaments ↔ MIDI expansions ↔ Universal ID 
  registry.

          Matching Strategy:
          1. Start with XML ornaments (semantic source of truth)
          2. Match to MIDI clusters by timing + pitch pattern + ornament type
          3. Create OrnamentGroup for each matched pair
          4. Generate Universal ID relationships with sub-IDs
          5. Enhance existing registry with ornament metadata

          Args:
              xml_ornaments: Detected XML ornaments from OrnamentXMLDetector
              midi_clusters: Detected MIDI clusters from MIDIOrnamentDetector
              existing_registry: Base Universal ID registry from Note Coordinator

          Returns:
              Enhanced registry with ornament groups and relationships
          """

          # Match XML ornaments with MIDI clusters

                  # Create Universal ID relationship

          # Generate ornament registry

          """
          Match XML ornament with MIDI cluster using multiple heuristics.

          Matching Criteria (scored):
          1. Ornament type similarity (trill → trill, mordent → mordent)
          2. Timing proximity (MIDI cluster near XML ornament timing)
          3. Pitch pattern consistency (primary pitches match)
          4. Duration compatibility (MIDI cluster duration matches expectations)

          Returns best match above confidence threshold (0.7).
          """

              # 1. Ornament type matching (weight: 0.3)

              # 2. Timing proximity (weight: 0.4)
              timing_score = max(0, 1.0 - (time_diff / 2.0))  # Within 2s = 1.0, 
  beyond = 0.0

              # 3. Pitch pattern consistency (weight: 0.2)

              # 4. Duration compatibility (weight: 0.1)

          """
          Calculate similarity between XML and MIDI ornament types.

          Some ornaments are detected as different types but are compatible:
          - acciaccatura/appoggiatura (MIDI) → grace (XML)
          - trill/tremolo (MIDI) → trill (XML) with different intervals
          """
          # Exact match

          # Compatible type mappings

              "trill": ["tremolo"],  # Similar rapid alternation

          """
          Create unified ornament group with Universal ID assignments.

          Universal ID Strategy:
          - Ornament group: New UUID (e.g., "5a3f2b1c-...")
          - Each MIDI note in expansion: Gets sub-ID (e.g., "5a3f2b1c-..._midi_0")
          - Visual notehead: Keeps its XML-derived UUID (from existing registry)
          - Ornament symbol: New UUID for SVG symbol element

          Relationship:
          1 visual notehead → N MIDI notes (all share ornament_group_id)
          """

          # Assign sub-IDs to MIDI expansion notes

          # Get or create Universal ID for primary notehead
          # (In real implementation, this would come from existing registry)

          # Process MIDI expansion notes

              # Create sub-ID for this MIDI note

              # Create a copy of the MIDI note with new ID

                  note_id=midi_sub_id  # New ornament sub-ID

              # Establish bidirectional mapping

          # Create timing distribution

          # Create OrnamentGroup

          """
          Create UniversalIDRelationship from OrnamentGroup.

          Determines relationship type:
          - 1:N if single visual notehead with N MIDI notes
          - N:M if multiple visual noteheads (grace notes) with M MIDI notes
          """

          # Extract Universal IDs

          """Generate comprehensive ornament registry for pipeline integration."""

          # Add ornament groups

              # Update type counts

          # Add universal relationships

          """Get comprehensive summary of ornament coordination."""

      """CLI interface for testing ornament coordination."""

          # Step 1: Detect XML ornaments

          # Step 2: Detect MIDI clusters
          # (For testing, would need to load MIDI notes first)
          # Placeholder: midi_detector = MIDIOrnamentDetector(verbose=False)
          # midi_clusters = midi_detector.detect_ornament_clusters(midi_notes)
          midi_clusters = []  # Placeholder for now

          # Step 3: Coordinate ornaments

          # Placeholder registry

          # Save results

          # Print summary

