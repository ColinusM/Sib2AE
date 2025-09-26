Based on the BackAndForth.md file, here's a comprehensive summary of the features and requirements for the Sib2Ae synchronization system, organized in logical development order:

  Core Synchronization Features Summary

  Phase 1: Foundation & Data Collection

  1. XML-MIDI-SVG Context Gatherer
    - Early pipeline analysis tool that runs first
    - Collects data from MusicXML, MIDI, and SVG simultaneously
    - Creates master relationship mapping file
    - Uses existing codebase where possible
  2. XML-MIDI Matcher with Tolerance
    - Configurable tolerance (default 100ms) for unquantized MIDI
    - Pitch must match exactly (hard condition)
    - Pick closest timing match when multiple candidates exist
    - Log matches found, unquantized matches, and no-matches

  Phase 2: Tied Notes Logic

  3. Tied Notes Detection & Handling
    - Detect tied relationships from MusicXML <tie> elements only
    - Multiple visual noteheads can correspond to one MIDI note
    - First notehead (tied-from) gets actual MIDI timing and keyframes
    - Subsequent noteheads (tied-to) get calculated approximate start times but no animation
  4. Tied Notes Timing Calculation
    - Use MusicXML beat position for tied-to notes
    - Calculate proportionally based on tied-from note duration and beat positions
    - All tied notes in sequence end at the first note's MIDI end time
    - No tempo changes will occur mid-tied sequence

  Phase 3: Note Matching & Coordination

  5. Pitch-Based Chord Matching
    - Match simultaneous notes by pitch information from XML and MIDI
    - Same instrument chords get same start time
    - Sequential notes within instrument: sort SVG left-to-right, MIDI by start time
  6. Universal Start Time Assignment
    - All start times in seconds from beginning of master MIDI (t=0)
    - 30 FPS timing for After Effects compatibility
    - Keyframes trigger at MIDI note start time
    - Keyframe duration takes precedence if longer than MIDI note

  Phase 4: Pipeline Integration

  7. Coordinator System
    - New coordinator tool to orchestrate entire process
    - Parallel processing of SVG and Audio pipelines (with careful integration)
    - Build on top of existing working pipeline
    - MusicXML as source of truth for all relationships
  8. Enhanced Pipeline Flow
    - Early Analysis: XML/MIDI/SVG matcher creates relationships
    - Modified existing tools to use relationship data
    - Maintains backward compatibility with current system
    - Final synchronization merges all outputs

  Phase 5: Output & Integration

  9. Master JSON Output Format
    - Single comprehensive file with all timing and keyframe data
    - Contains note relationships, timing data, and keyframe file references
    - Optimized for minimal clicks in After Effects import
    - Maps notehead SVG files to MIDI timing and audio keyframes
  10. After Effects Integration Ready
    - All noteheads in single composition (not separate compositions)
    - Each notehead object has precise start time matching MIDI
    - Only tied-from notes animate with keyframes
    - Tied-to notes remain visible but static

  Future Edge Cases (Noted for Later)

  - Grace notes and ornaments
  - Multiple identical notes in piano scores
  - Trills and complex ornamentation
  - Visual noteheads without MIDI counterparts

  Development Constraints

  - Must maintain existing pipeline functionality
  - Use git for safe iteration and rollback capability
  - Focus on accuracy before optimization
  - Support both quantized and unquantized MIDI workflows

  This system will create perfectly synchronized music animations where each notehead SVG has precise timing data and audio-driven keyframes for After Effects integration.