# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Sibelius to After Effects (Sib2Ae) converter** that extracts and processes musical notation from SVG exports. The project implements a universal MusicXML to SVG processing pipeline for separating noteheads and instruments from musical scores.

### Core Architecture

**Four Universal Tools Pipeline:**
1. **Noteheads Extractor** (`truly_universal_noteheads_extractor.py`) - Extracts noteheads from MusicXML
2. **Noteheads Subtractor** (`truly_universal_noteheads_subtractor.py`) - Removes noteheads from full SVG 
3. **Instrument Separator** (`xml_based_instrument_separator.py`) - Separates instruments into individual SVG files
4. **Staff/Barlines Extractor** (`staff_barlines_extractor.py`) - Extracts structural framework (staff lines + barlines)

**Key Principle: MusicXML-First Approach**
- Always analyze MusicXML before processing SVG
- Use universal coordinate transformation system for pixel-perfect accuracy
- Maintain proper XML/SVG structure throughout processing

## Development Commands

### Running the Pipeline
```bash
# Extract noteheads only
python truly_universal_noteheads_extractor.py "Base/SS 9.musicxml"

# Remove noteheads from full score  
python truly_universal_noteheads_subtractor.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"

# Separate instruments
python xml_based_instrument_separator.py "Base/SS 9.musicxml" "Base/SS 9 full.svg" "output_dir"

# Extract staff lines and barlines
python staff_barlines_extractor.py "Base/SS 9.musicxml" "Base/SS 9 full.svg"

# Full workflow: Extract → Separate
python truly_universal_noteheads_extractor.py "Base/SS 9.musicxml"
python xml_based_instrument_separator.py "Base/SS 9.musicxml" "Base/SS 9_noteheads_universal.svg" "noteheads_separated"
```

### Testing & Validation
```bash
# Install dependencies
uv sync

# Run tests (if implemented)
uv run pytest

# Validate SVG output (manual)
# Open generated SVG files in browser to verify structure
```

## Universal Coordinate System

### Staff Position Mappings
- **Staff 0** (Upper): Y 950-1100 (base: 1037) 
- **Staff 1** (Lower): Y 1250-1500 (base: 1417)
- **Staff 2** (Third): Y 1650-1800 (base: 1797)
- **Staff 3** (Fourth): Y 2050-2200 (base: 2177)

### Helsinki Special Std Notehead Codes
- **Code 70**: `\u0046` (hollow notehead - half/whole notes)
- **Code 102**: `\u0066` (full notehead - quarter/eighth/sixteenth notes)

### Staff/Barlines Structure Recognition
- **Staff lines**: stroke-width="2.25", full-width horizontal lines (>3000 pixels)
- **Ledger lines**: stroke-width="3.75", short horizontal lines (<3000 pixels) - EXCLUDED
- **Regular barlines**: stroke-width="5", vertical lines connecting staves
- **Thick end barlines**: stroke-width="16", final double barline effect

## File Structure

```
/
├── Base/                          # Input files
│   ├── SS 9.musicxml             # MusicXML score data
│   ├── SS 9 full.svg             # Complete SVG score
│   └── SS 9_noteheads_universal.svg # Extracted noteheads
├── truly_universal_noteheads_extractor.py    # Tool 1: Extract noteheads
├── truly_universal_noteheads_subtractor.py   # Tool 2: Remove noteheads  
├── xml_based_instrument_separator.py         # Tool 3: Separate instruments
├── staff_barlines_extractor.py               # Tool 4: Extract staff/barlines
├── PRPs/                         # PRP methodology and templates
└── noteheads_separated/          # Output: separated noteheads by instrument
```

## Critical Implementation Details

### XML Processing Requirements
- Use `xml.etree.ElementTree` for proper XML/SVG structure preservation
- Never use text-based line processing for SVG manipulation
- Maintain XML namespaces (ns0:svg, ns0:g) in output files

### Coordinate Handling
- MusicXML coordinates are relative to measures
- SVG coordinates are absolute pixel positions
- Use empirically determined staff ranges for instrument separation
- Filter out small Y values (< 100) to avoid opacity conflicts

### Error Prevention
- Validate MusicXML structure before processing
- Check for `<part-list>` with `<score-part>` elements
- Ensure all tools maintain pixel-perfect coordinate accuracy
- Always verify output SVG files render correctly

## PRP Integration

This project uses the **Product Requirement Prompt (PRP)** methodology. Use `/create-base-prp` and `/execute-base-prp` commands for feature development.

**PRP Directory:** `/PRPs/`
**Templates:** Use `prp_base.md` for comprehensive feature development