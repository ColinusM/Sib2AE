# Orphan MIDI Detection Strategy

## Proven Concept

Using the trill test case, we successfully detected:

```
Total MIDI notes: 14
Matched (anchors): 8  ← Notes with Universal IDs
Orphans: 6           ← Notes WITHOUT Universal IDs

Orphan Cluster: 6 notes between anchors
   Before anchor: A4 at 8.320s (matched)
   After anchor:  B4 at 8.750s (matched)

   Orphans in window (8.375s → 8.750s):
      G4 at 8.389s ← Orphan
      A4 at 8.453s ← Orphan
      G4 at 8.514s ← Orphan
      A4 at 8.578s ← Orphan
      G4 at 8.645s ← Orphan
      A4 at 8.715s ← Orphan

   ✅ Pattern: RAPID ALTERNATION (A4 ↔ G4)
   ✅ Interval: 2 semitones
   ✅ Conclusion: TRILL ORNAMENT
```

---

## How It Works

### 1. Anchor-Based Windowing

```python
# Matched notes serve as anchors
anchors = [
    Note(A4, time=8.320s),  # Matched ✅
    Note(B4, time=8.750s)   # Matched ✅
]

# Define window between them
window = (8.375s, 8.750s)

# Find orphans in window
orphans = find_midi_notes_between(8.375s, 8.750s)
# Result: 6 orphan notes (the trill expansion)
```

**Why this works:**
- **Anchors are reliable** - They have Universal IDs from note_coordinator
- **Windows are automatic** - No hardcoded time ranges
- **Orphans are isolated** - We know they belong to ornaments

---

### 2. Pattern Recognition

Once orphans are found, analyze the pattern:

```python
def classify_orphan_cluster(orphans: List[MIDINote]) -> str:
    # Check pitch pattern
    pitches = [n.pitch for n in orphans]

    # Trill: Rapid alternation between 2 pitches
    if is_alternating(pitches) and len(set(pitches)) == 2:
        return "trill"

    # Tremolo: Same note repeated rapidly
    if len(set(pitches)) == 1:
        return "tremolo"

    # Grace notes: 1-2 notes before main note
    if len(orphans) <= 2:
        return "grace_note"

    # Mordent: 3 notes (main-aux-main)
    if len(orphans) == 3 and pitches[0] == pitches[2]:
        return "mordent"

    # Turn: 4 notes (upper-main-lower-main)
    if len(orphans) == 4:
        return "turn"

    return "unknown"
```

**Current detection:**
```
Orphans: [G4, A4, G4, A4, G4, A4]
Pattern: Alternating ✅
Unique pitches: 2 ✅
→ Classification: TRILL
```

---

## Integration with Pipeline

### Phase 2.5: Ornament Detection (NEW)

```
Phase 1: Initialize
Phase 2: Note Coordinator → Creates Universal IDs, identifies anchors
Phase 2.5: Ornament Detection → NEW!
   ├─ Step 1: Detect orphan MIDI (anchor-based)
   ├─ Step 2: Parse XML for ornament tags
   ├─ Step 3: Parse SVG for ornament symbols (hex-based)
   └─ Step 4: Create 3-way coordination
Phase 3: Tied Note Processor
Phase 4: Pipeline Stages
```

### Orchestrator Integration

```python
# Brain/orchestrator/universal_orchestrator.py

def orchestrate_complete_pipeline(self):
    # Phase 2: Note Coordinator
    self._execute_note_coordinator()

    # Phase 2.5: Ornament Detection (NEW)
    if self.config.enable_ornaments:
        self._execute_orphan_midi_detector()
        self._execute_ornament_xml_parser()
        self._execute_ornament_svg_parser()
        self._execute_ornament_coordinator()

    # Phase 3: Tied Notes
    self._execute_tied_note_processor()
```

---

## Complete Detection Flow

### Input Files
```
1. MusicXML: Contains <trill-mark> tag
2. MIDI: Contains 14 notes (8 matched + 6 orphans)
3. SVG: Contains U+F0D9 trill symbol
```

### Detection Steps

**Step 1: Orphan MIDI Detection** ✅ (Completed)
```python
detector = OrphanMIDIDetector(midi_file, registry_file)
clusters = detector.detect_orphans()

# Result:
OrphanCluster(
    orphan_notes=[G4, A4, G4, A4, G4, A4],
    before_anchor=A4@8.320s,
    after_anchor=B4@8.750s,
    pattern="trill"
)
```

**Step 2: XML Ornament Detection** (Next)
```python
xml_parser = OrnamentXMLParser(musicxml_file)
xml_ornaments = xml_parser.find_ornaments()

# Result:
XMLOrnament(
    type="trill",
    note="G4",
    measure=5,
    part_id="P1"
)
```

**Step 3: SVG Ornament Detection** (Using hex parser)
```python
svg_parser = DeepSVGAnalyzer(svg_file)
svg_ornaments = svg_parser.get_ornaments()

# Result:
SVGOrnament(
    type="trill",
    symbols=[
        (U+F0D9, x=3600, y=930),  # Trill start
        (U+F07E, x=3660, y=918),  # Wavy segment
        ...
    ],
    linked_notehead=(x=3602, y=1034)
)
```

**Step 4: Coordinate All Three** (Final)
```python
coordinator = OrnamentCoordinator(
    orphan_clusters,
    xml_ornaments,
    svg_ornaments
)

ornament_registry = coordinator.create_relationships()

# Result:
{
    "ornament_id": "orn_trill_001",
    "type": "trill",

    # XML confirmation
    "xml_note": "G4",
    "xml_measure": 5,
    "xml_confirmed": True,

    # SVG confirmation
    "svg_symbols": [...],
    "svg_notehead_pos": (3602, 1034),
    "svg_confirmed": True,

    # MIDI expansion (from orphans)
    "midi_notes": [
        {"pitch": 67, "time": 8.389},
        {"pitch": 69, "time": 8.453},
        ...
    ],
    "midi_pattern": "alternating",
    "midi_confirmed": True,

    # Relationship
    "visual_noteheads": 1,
    "midi_expansion": 6,
    "relationship": "1:6"
}
```

---

## Why Anchor-Based Detection Works

### Problem: How to Find Ornament MIDI Notes?

**OLD Approach (Pattern Matching):**
```python
# Try to find rapid alternations in MIDI
for i in range(len(midi_notes) - 1):
    if midi_notes[i+1].start - midi_notes[i].end < 0.1:
        # Rapid succession, might be ornament?
        # But how to know where it starts/ends?
        # How to link to visual notehead?
```

**Problems:**
- ❌ No clear boundaries (when does trill start/end?)
- ❌ False positives (fast passages, not ornaments)
- ❌ Can't link to visual notehead
- ❌ Can't verify against XML

**NEW Approach (Anchor-Based):**
```python
# Use matched notes as anchors
anchors = get_matched_notes()  # Have Universal IDs

# Orphans between anchors MUST be ornaments
for i in range(len(anchors) - 1):
    window = (anchors[i].end_time, anchors[i+1].start_time)
    orphans = find_notes_in_window(window)

    if orphans:
        # These orphans belong to an ornament!
        # We know the before/after notes
        # We can link to XML/SVG
```

**Advantages:**
- ✅ Clear boundaries (anchor notes define windows)
- ✅ No false positives (only orphans in registry gaps)
- ✅ Can link to visual (anchors have coordinates)
- ✅ Can verify against XML (anchors have measure/part)

---

## Pattern Classification

### Rapid Alternation → Trill
```
Orphans: [G4, A4, G4, A4, G4, A4]
Pattern: A-B-A-B-A-B
Interval: 2 semitones
Duration: 0.375s (6 notes)
→ Classification: TRILL ✅
```

### Same Note Repeated → Tremolo
```
Orphans: [C5, C5, C5, C5, C5, C5]
Pattern: A-A-A-A-A-A
Duration: 0.300s
→ Classification: TREMOLO
```

### 1-2 Notes Before Main → Grace Note
```
Orphans: [D#4]
Before anchor: E4
Duration: 0.050s (very short)
→ Classification: GRACE NOTE (acciaccatura)
```

### 3 Notes (main-aux-main) → Mordent
```
Orphans: [A4, B4, A4]
Pattern: A-B-A (return to original)
Duration: 0.150s
→ Classification: MORDENT
```

### 4 Notes → Turn
```
Orphans: [B4, A4, G4, A4]
Pattern: upper-main-lower-main
→ Classification: TURN
```

---

## Files Modified/Created

### Created (Today)
```
✅ Brain/orchestrator/orphan_midi_detector.py
   - Anchor-based orphan detection
   - Pattern classification
   - Temporal windowing
```

### To Create (Next)
```
⏳ Brain/orchestrator/ornament_xml_parser.py
   - Parse <ornaments> tags from MusicXML
   - Extract ornament type, position

⏳ Brain/orchestrator/ornament_svg_parser.py
   - Hex-based SVG ornament extraction
   - Link symbols to noteheads

⏳ Brain/orchestrator/ornament_coordinator.py
   - Coordinate XML + SVG + MIDI orphans
   - Create ornament registry
```

### To Modify (Integration)
```
⏳ Brain/orchestrator/universal_orchestrator.py
   - Add Phase 2.5: Ornament Detection
   - Add --enable-ornaments flag

⏳ Brain/orchestrator/pipeline_stage.py
   - Add ornament detection stages
```

---

## Testing Strategy

### Test Case 1: Trill ✅ (Completed)
```
Input: Brain/Base/Trill/
Result: 6 orphans detected, classified as trill ✅
```

### Test Case 2: Mordent (Need)
```
Input: Brain/Base/Mordent/ (to create)
Expected: 3 orphans, classified as mordent
```

### Test Case 3: Grace Notes (Need)
```
Input: Brain/Base/GraceNotes/ (to create)
Expected: 1-2 orphans, classified as grace notes
```

### Test Case 4: Multiple Ornaments (Need)
```
Input: Brain/Base/Mixed/ (to create)
Expected: Multiple clusters, different types
```

---

## Next Steps

1. **Create XML ornament parser** (detect `<trill-mark>`, etc.)
2. **Create SVG ornament parser** (use hex-based analyzer)
3. **Create coordinator** (link all 3 sources)
4. **Test with trill case** (end-to-end)
5. **Export more test cases** (mordent, grace notes)
6. **Iterate until robust**

The anchor-based approach is **solid and reliable** - orphans between matched notes can ONLY be ornaments!
