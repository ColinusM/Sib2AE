#!/usr/bin/env python3
"""
Universal Sibelius SVG Unicode Mapping

Discovered via hex analysis - works for ALL Sibelius fonts
(Helsinki, Lelandia, Opus, Norfolk, etc.)

Sibelius always exports to U+F000-F8FF range regardless of font.
"""

SIBELIUS_UNICODE_MAP = {
    # ORNAMENTS
    0xF0D9: 'trill_start',           # ef8399
    0xF07E: 'trill_wavy',            # ef81be
    0xF04A: 'accent_articulation',   # ef818a

    # NOTEHEADS
    0xF0CF: 'notehead_filled',       # ef838f (quarter/eighth notes)
    0xF0B7: 'notehead_type_1',       # ef82b7
    0xF0CE: 'notehead_type_2',       # ef838e

    # ACCIDENTALS
    0xF0E4: 'sharp',                 # ef83a4
    0xF0EE: 'natural',               # ef83ae
    0xF0FA: 'flat',                  # ef83ba

    # CLEFS & TIME SIGNATURES
    0xF023: 'time_signature_element', # ef80a3
    0xF026: 'clef',                  # ef80a6

    # DYNAMICS
    0xF06A: 'dynamic_marking',       # ef81aa

    # SPECIAL (Helsinki Special Std / Lelandia Special Std)
    0xF0AA: 'special_character',     # ef82aa
}

# UTF-8 byte sequences for direct search
TRILL_START_BYTES = b'\xef\x83\x99'  # U+F0D9
TRILL_WAVY_BYTES = b'\xef\x81\xbe'   # U+F07E
FILLED_NOTEHEAD_BYTES = b'\xef\x83\x8f'  # U+F0CF
