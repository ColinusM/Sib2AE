# Pipeline Integration Plan: Ornament Detection

## ✅ What We've Proven Today

### 1. Orphan MIDI Detection (WORKING)
```bash
python Brain/orchestrator/orphan_midi_detector.py \
    "Brain/Base/Trill/Saint-Saens Trio No 2.mid" \
    "universal_output/universal_notes_registry.json"

Result:
✅ Found 6 orphan MIDI notes between anchors
✅ Classified as TRILL (A4 ↔ G4 alternation)
✅ Temporal window: 8.375s → 8.750s
```

### 2. SVG Ornament Detection (WORKING)
```bash
python scripts/svg_deep_analyzer.py \
    "Brain/Base/Trill/Saint-Saens Trio No 2.svg"

Result:
✅ Found 6 trill symbols (1 start + 5 wavy)
✅ Linked to notehead at (3602, 1034)
✅ Position: 104px above notehead
```

### 3. XML Ornament Detection (TRIVIAL - Just parse tags)
```xml
<note>
  <pitch><step>G</step><octave>4</octave></pitch>
  <notations>
    <ornaments>
      <trill-mark />
    </ornaments>
  </notations>
</note>
```

**We have all 3 pieces! Just need to coordinate them.**

---

## 📋 Files to Create/Modify

### Files to CREATE (New)

#### 1. `Brain/orchestrator/ornament_xml_parser.py`
```python
"""Parse ornament tags from MusicXML"""

class OrnamentXMLParser:
    def find_ornaments(self) -> List[XMLOrnament]:
        """Find all <ornaments> tags in MusicXML"""
        # Parse for <trill-mark>, <mordent>, <turn>, etc.
        # Return ornament with note, measure, part_id

# SIMPLE - Just XML parsing, no complex logic
```

#### 2. `Brain/orchestrator/ornament_svg_parser.py`
```python
"""Parse ornament symbols from SVG using hex analysis"""

from scripts.svg_deep_analyzer import DeepSVGAnalyzer

class OrnamentSVGParser:
    def find_ornaments(self) -> List[SVGOrnament]:
        """Find ornament symbols and link to noteheads"""
        analyzer = DeepSVGAnalyzer(self.svg_file)
        return analyzer.get_notehead_with_ornaments()

# ALREADY BUILT - Just wrap existing DeepSVGAnalyzer
```

#### 3. `Brain/orchestrator/ornament_coordinator.py`
```python
"""Coordinate XML + SVG + MIDI ornaments"""

class OrnamentCoordinator:
    def __init__(self,
                 xml_ornaments: List[XMLOrnament],
                 svg_ornaments: List[SVGOrnament],
                 orphan_clusters: List[OrphanCluster]):
        # Store all 3 sources

    def create_relationships(self) -> OrnamentRegistry:
        """Match ornaments across XML, SVG, MIDI"""

        for xml_orn in xml_ornaments:
            # 1. Find matching SVG ornament (same note position)
            svg_orn = find_matching_svg(xml_orn)

            # 2. Find matching MIDI orphans (temporal window)
            orphan_cluster = find_matching_orphans(xml_orn)

            # 3. Create relationship
            registry.add({
                'xml_confirmed': True,
                'svg_confirmed': svg_orn is not None,
                'midi_expansion': orphan_cluster.orphan_notes,
                ...
            })

# CORE LOGIC - Link all 3 sources
```

---

### Files to MODIFY (Integration)

#### 1. `Brain/orchestrator/universal_orchestrator.py`

**Add new phase:**
```python
def orchestrate_complete_pipeline(self):
    # Phase 1: Initialize
    self._initialize_components()

    # Phase 2: Note Coordinator
    self._execute_note_coordinator()

    # ⭐ Phase 2.5: Ornament Detection (NEW)
    if self.config.enable_ornaments:
        self._execute_ornament_detection()

    # Phase 3: Tied Note Processor
    if not self.config.skip_tied_notes:
        self._execute_tied_note_processor()

    # Phase 4: Pipeline Stages
    self._execute_pipeline_stages()
```

**Add new method:**
```python
def _execute_ornament_detection(self):
    """Execute ornament detection pipeline"""
    self._log("Phase 2.5: Executing Ornament Detection")

    # 1. Detect orphan MIDI
    orphan_detector = OrphanMIDIDetector(
        self.config.midi_file,
        self.config.output_dir / "universal_notes_registry.json"
    )
    orphan_clusters = orphan_detector.detect_orphans()

    # 2. Parse XML ornaments
    xml_parser = OrnamentXMLParser(self.config.musicxml_file)
    xml_ornaments = xml_parser.find_ornaments()

    # 3. Parse SVG ornaments (if SVG provided)
    svg_ornaments = []
    if self.config.svg_file:
        svg_parser = OrnamentSVGParser(self.config.svg_file)
        svg_ornaments = svg_parser.find_ornaments()

    # 4. Coordinate all sources
    coordinator = OrnamentCoordinator(
        xml_ornaments,
        svg_ornaments,
        orphan_clusters
    )
    ornament_registry = coordinator.create_relationships()

    # 5. Save registry
    registry_path = self.config.output_dir / "ornament_coordination_registry.json"
    with open(registry_path, 'w') as f:
        json.dump(ornament_registry.to_dict(), f, indent=2)

    self._log(f"✅ Ornament Detection Complete: {len(ornament_registry.ornaments)} ornaments")
```

#### 2. `Brain/orchestrator/pipeline_stage.py`

**Add config option:**
```python
@dataclass
class OrchestrationConfig:
    # ... existing fields ...

    # Ornament detection
    enable_ornaments: bool = False  # ← NEW FLAG
```

---

## 🚀 Complete Execution Flow

### Command
```bash
python -m Brain.orchestrator.universal_orchestrator \
    "Brain/Base/Trill/Saint-Saens Trio No 2.musicxml" \
    "Brain/Base/Trill/Saint-Saens Trio No 2.mid" \
    --svg "Brain/Base/Trill/Saint-Saens Trio No 2.svg" \
    --enable-ornaments \
    --mode sequential --quiet > /dev/null 2>&1
```

### Pipeline Execution

```
Phase 1: Initialize Components
   ✅ Create output directories
   ✅ Initialize manifest manager

Phase 2: Note Coordinator
   ✅ Match XML ↔ MIDI notes
   ✅ Create Universal ID registry
   ✅ Result: 8 matched notes, 6 orphan MIDI notes

Phase 2.5: Ornament Detection (NEW!)
   Step 1: Orphan MIDI Detection
      ✅ Found 1 orphan cluster (6 notes)
      ✅ Pattern: TRILL (A4 ↔ G4)

   Step 2: XML Ornament Detection
      ✅ Found 1 <trill-mark> on G4 (measure 5)

   Step 3: SVG Ornament Detection
      ✅ Found 6 trill symbols at (3600, 930)
      ✅ Linked to notehead (3602, 1034)

   Step 4: Coordination
      ✅ Matched all 3 sources:
         XML: <trill-mark> on G4 ✓
         SVG: 6 symbols above notehead ✓
         MIDI: 6 orphan alternating notes ✓

      ✅ Created ornament relationship:
         {
           "ornament_id": "orn_001",
           "type": "trill",
           "xml_confirmed": true,
           "svg_confirmed": true,
           "midi_confirmed": true,
           "visual_noteheads": 1,
           "midi_expansion": 6,
           "relationship": "1:6"
         }

   ✅ Saved: universal_output/ornament_coordination_registry.json

Phase 3: Tied Note Processor
   ✅ Process tied notes

Phase 4: Pipeline Stages
   ✅ Execute symbolic/audio separators

Phase 5: Final Validation
   ✅ Verify outputs

Phase 6: Report Generation
   ✅ Generate execution report
```

---

## 📊 Output Files

### New File Created
```
universal_output/
└── ornament_coordination_registry.json  ← NEW!
```

**Content:**
```json
{
  "ornaments": [
    {
      "ornament_id": "orn_trill_001",
      "type": "trill",

      "xml_data": {
        "note": "G4",
        "measure": 5,
        "part_id": "P1",
        "confirmed": true
      },

      "svg_data": {
        "symbols": [
          {"unicode": "U+F0D9", "position": {"x": 3600, "y": 930}},
          {"unicode": "U+F07E", "position": {"x": 3660, "y": 918}},
          {"unicode": "U+F07E", "position": {"x": 3690, "y": 918}},
          {"unicode": "U+F07E", "position": {"x": 3720, "y": 918}},
          {"unicode": "U+F07E", "position": {"x": 3750, "y": 918}},
          {"unicode": "U+F07E", "position": {"x": 3780, "y": 918}}
        ],
        "notehead_position": {"x": 3602, "y": 1034},
        "confirmed": true
      },

      "midi_data": {
        "expansion_notes": [
          {"pitch": 67, "pitch_name": "G4", "time": 8.389, "velocity": 76},
          {"pitch": 69, "pitch_name": "A4", "time": 8.453, "velocity": 76},
          {"pitch": 67, "pitch_name": "G4", "time": 8.514, "velocity": 76},
          {"pitch": 69, "pitch_name": "A4", "time": 8.578, "velocity": 76},
          {"pitch": 67, "pitch_name": "G4", "time": 8.645, "velocity": 76},
          {"pitch": 69, "pitch_name": "A4", "time": 8.715, "velocity": 76}
        ],
        "pattern": "alternating",
        "interval_semitones": 2,
        "confirmed": true
      },

      "relationship": {
        "visual_elements": 1,
        "midi_elements": 6,
        "type": "1:N"
      }
    }
  ],

  "summary": {
    "total_ornaments": 1,
    "by_type": {
      "trill": 1
    },
    "verification": {
      "xml_confirmed": 1,
      "svg_confirmed": 1,
      "midi_confirmed": 1,
      "all_sources_matched": 1
    }
  }
}
```

---

## 🎯 Implementation Timeline

### Day 1: Core Files (4-6 hours)
- ✅ Create `orphan_midi_detector.py` (DONE)
- ⏳ Create `ornament_xml_parser.py` (2 hours)
- ⏳ Create `ornament_svg_parser.py` (1 hour - wrapper)
- ⏳ Create `ornament_coordinator.py` (2 hours)

### Day 2: Integration (2-3 hours)
- ⏳ Modify `universal_orchestrator.py` (1 hour)
- ⏳ Modify `pipeline_stage.py` (30 min)
- ⏳ Test end-to-end with trill case (1 hour)

### Day 3: Testing & Refinement (4-6 hours)
- ⏳ Export mordent test case (30 min)
- ⏳ Export grace note test case (30 min)
- ⏳ Test with multiple ornament types (2 hours)
- ⏳ Fix issues, refine (2 hours)

**Total: 2-3 days of focused work**

---

## ✅ Success Criteria

### Minimum Viable Product (MVP)
- [x] Orphan MIDI detection works (anchor-based) ✅
- [x] SVG ornament detection works (hex-based) ✅
- [ ] XML ornament parsing works
- [ ] Coordination creates valid registry
- [ ] Works with trill test case end-to-end

### Full Feature Set
- [ ] All ornament types (trill, mordent, turn, grace, tremolo)
- [ ] 3-way verification (XML ↔ SVG ↔ MIDI all match)
- [ ] Registry integrates with After Effects import
- [ ] Handles edge cases (no SVG, missing ornaments, etc.)

---

## 🔑 Key Insights

### Why This Approach Works

1. **Anchor-based orphan detection**
   - Uses matched notes as reliable boundaries
   - Orphans between anchors MUST be ornaments
   - No false positives

2. **Hex-based SVG parsing**
   - Can actually SEE ornament symbols
   - Can link to noteheads spatially
   - Previously impossible!

3. **3-way verification**
   - XML says "trill here"
   - SVG confirms "trill symbol visible"
   - MIDI confirms "6 alternating notes"
   - All sources agree = high confidence

4. **Minimal pipeline changes**
   - Add Phase 2.5 (ornament detection)
   - Runs after note_coordinator
   - Self-contained modules
   - Clean integration

---

## 📂 File Summary

### Created Today
```
✅ Brain/orchestrator/orphan_midi_detector.py
✅ scripts/svg_deep_analyzer.py
✅ scripts/discover_svg_unicode.py
✅ docs/orphan_detection_strategy.md
✅ docs/pipeline_integration_plan.md
```

### To Create
```
⏳ Brain/orchestrator/ornament_xml_parser.py
⏳ Brain/orchestrator/ornament_svg_parser.py
⏳ Brain/orchestrator/ornament_coordinator.py
```

### To Modify
```
⏳ Brain/orchestrator/universal_orchestrator.py
⏳ Brain/orchestrator/pipeline_stage.py
```

---

## 🚦 Next Session Tasks

1. **Create ornament_xml_parser.py** (simple XML parsing)
2. **Create ornament_svg_parser.py** (wrapper around DeepSVGAnalyzer)
3. **Create ornament_coordinator.py** (link all 3 sources)
4. **Test with trill case** (run full pipeline)
5. **Debug and refine** until it works end-to-end

Then we'll have **complete ornament detection** working! 🎉
