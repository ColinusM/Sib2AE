# Sibelius SVG Notehead Extraction - Project Documentation

## Project Overview
Successfully extracted and recreated individual musical noteheads from a Sibelius-exported MusicXML/SVG file using proper Helsinki Special Std font character codes.

## Problem Solved
- **Challenge**: Sibelius exports contained staff lines, stems, and other elements but the actual noteheads were missing from the SVG
- **Goal**: Create a noteheads-only SVG file with proper musical notation using the correct font characters
- **Solution**: Reverse-engineered Helsinki Special Std font to find the correct notehead character codes

## Key Files Created

### 1. `SS 9 noteheads-only.svg`
- **Status**: ✅ WORKING
- **Content**: 8 individual noteheads positioned correctly
- **Font**: Helsinki Special Std
- **Coordinates**: Mapped from original MusicXML data

### 2. `HELSINKI-NOTEHEAD-CODES.md`
- **Purpose**: Permanent documentation of correct character codes
- **Critical Info**: Never forget these mappings!

## Critical Discovery: Helsinki Special Std Character Codes

### Small Noteheads
- **Code 69** (`&#69;`): Small hollow notehead (whole/half notes)
- **Code 101** (`&#101;`): Small filled notehead (quarter/eighth/sixteenth notes)

### Large Noteheads  
- **Code 70** (`&#70;`): Large hollow notehead
- **Code 102** (`&#102;`): Large filled notehead

**RULE: Always use in pairs! Small (69/101) or Large (70/102)**

## Technical Process

### Step 1: Analysis
- Read MusicXML file: `SS 9.musicxml`
- Identified 8 total notes across 2 instruments (Flute, Violin)
- Found coordinate data and note durations

### Step 2: Font Investigation
- Created comprehensive character maps for Helsinki Special Std
- Tested multiple character ranges (32-255)
- User visually identified correct elliptical notehead shapes

### Step 3: Implementation
- Mapped XML coordinates to SVG coordinate system
- Applied proper transform matrix: `matrix(0.531496,0,0,0.531496,0,0)`
- Used correct font specifications matching original

## Note Distribution
**Flute (3 noteheads):**
- A4 quarter note (filled) - Code 101
- A4 eighth note (filled) - Code 101  
- G4 quarter note (filled) - Code 101

**Violin (5 noteheads):**
- B3 dotted half note (hollow) - Code 69
- B3 quarter note (filled) - Code 101
- B3 eighth note (filled) - Code 101
- A3 quarter note (filled) - Code 101
- C4 eighth note (filled) - Code 101
- B3 quarter note (filled) - Code 101

## Technical Specifications
```xml
<text fill="#000000" fill-opacity="1" stroke="none" xml:space="preserve" 
      x="[coordinate]" y="[coordinate]" 
      font-family="Helsinki Special Std" font-size="96" font-weight="400" font-style="normal">
      &#69; <!-- or &#101; -->
</text>
```

## Key Learnings

### Font Requirements
- **Must use**: "Helsinki Special Std" (not "Helsinki Std")
- **Character format**: Decimal HTML entities (`&#69;` not `&#x45;`)
- **Shape**: Elliptical noteheads, not circular

### Coordinate System
- Original SVG uses transform matrix scaling
- Y-coordinates: Flute ~1037, Violin ~1429
- X-coordinates mapped from MusicXML measure positions

### Failed Approaches
- Unicode musical symbols (♩♪♫) - wrong shapes
- Geometric diamonds (◆◇) - wrong shapes  
- Standard circles (●○) - wrong shapes
- Wrong font variants - "Helsinki Std" vs "Helsinki Special Std"

## Success Metrics
✅ All 8 noteheads visible and correctly positioned  
✅ Proper elliptical shapes matching original Sibelius notation  
✅ Correct filled vs hollow differentiation  
✅ Accurate coordinate preservation  
✅ Valid SVG structure  

## Files for Reference
- **Source**: `SS 9.musicxml` (original MusicXML data)
- **Original SVG**: `SS 9 noteheads.svg` (had framework but no noteheads)
- **Working Result**: `SS 9 noteheads-only.svg` (✅ SUCCESS)
- **Character Tests**: `helsinki-mega-spread.svg` (character identification)
- **Documentation**: `HELSINKI-NOTEHEAD-CODES.md` (permanent reference)

## Future Applications
This methodology can be applied to:
- Any Sibelius SVG export missing noteheads
- Other music notation software using Helsinki fonts
- Automated music notation processing pipelines
- After Effects animation workflows requiring separated elements

## Critical Success Factor
**The breakthrough was identifying that Helsinki Special Std font uses specific decimal character codes (69, 70, 101, 102) for proper elliptical noteheads, and these must be used in size-matched pairs.**

---
*Project completed successfully - noteheads extraction working as intended.*