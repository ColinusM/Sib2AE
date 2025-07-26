#!/usr/bin/env python3

import re

# Test the regex pattern with actual data from debug output
test_svg_paths = [
    "Text('\uf026', font-family='Helsinki Std', font-style='normal', font-variant='normal', font-weight='400',",
    "Text('\uf023', font-family='Helsinki Std', font-style='normal', font-variant='normal', font-weight='400',",
    "Text('\uf0b7', font-family='Helsinki Std', font-style='normal', font-variant='normal', font-weight='400',"
]

print("=== TEXT EXTRACTION DEBUG ===")

for i, svg_path in enumerate(test_svg_paths):
    print(f"\nTest {i+1}:")
    print(f"Input: {svg_path}")
    
    # Test the regex pattern
    text_match = re.search(r"Text\('([^']*)'", svg_path)
    if text_match:
        text_content = text_match.group(1)
        print(f"Extracted text: {repr(text_content)}")
        print(f"Text length: {len(text_content)}")
        print(f"Unicode codepoint: {ord(text_content) if text_content else 'N/A'}")
    else:
        print("No match found!")
    
    # Test font family extraction
    font_family_match = re.search(r"font-family='([^']*)'", svg_path)
    if font_family_match:
        font_family = font_family_match.group(1)
        print(f"Font family: {font_family}")
    else:
        print("No font family found!")

print("\n=== UNICODE TEST ===")
# Test if we can display the actual Unicode characters
unicode_chars = ['\uf026', '\uf023', '\uf0b7']
for char in unicode_chars:
    print(f"Unicode {ord(char):04x}: {repr(char)}")