#!/usr/bin/env python3
"""
Browser-based SVG viewer with hover functionality using pywebview
Provides Chrome-quality SVG rendering with JavaScript hover interactions
"""

import webview
import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import threading
import time

class SVGViewerWebView:
    def __init__(self, parent_callback=None):
        self.svg_file_path = None
        self.parent_callback = parent_callback
        self.settings_file = "svg_viewer_webview_settings.json"  # Use unique filename
        self.window = None
        self.midi_mappings = {}  # Store MIDI timing data for noteheads

        # Load previous window settings
        self.load_settings()

    def load_settings(self):
        """Load window position and size settings"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    # Validate coordinates to avoid pywebview positioning errors
                    x = settings.get('x', 100)
                    y = settings.get('y', 100)

                    # Ensure coordinates are reasonable (avoid negative or extreme values)
                    self.window_x = max(0, min(x, 3000))  # Limit to reasonable screen bounds
                    self.window_y = max(0, min(y, 2000))
                    self.window_width = max(400, min(settings.get('width', 1000), 4000))
                    self.window_height = max(300, min(settings.get('height', 800), 3000))
                    self.last_svg_file = settings.get('last_svg_file', None)
            else:
                self.window_x = 100
                self.window_y = 100
                self.window_width = 1000
                self.window_height = 800
                self.last_svg_file = None
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.window_x = 100
            self.window_y = 100
            self.window_width = 1000
            self.window_height = 800
            self.last_svg_file = None

    def save_settings(self):
        """Save current window position and size"""
        try:
            settings = {
                'x': self.window_x,
                'y': self.window_y,
                'width': self.window_width,
                'height': self.window_height,
                'last_svg_file': self.svg_file_path
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_midi_mappings(self, musicxml_path=None, midi_path=None):
        """Load MIDI mappings using context gatherer for enhanced hover tooltips"""
        try:
            if not musicxml_path or not midi_path:
                print("No MusicXML or MIDI paths provided - using basic hover tooltips")
                return

            # Import context gatherer components
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'PRPs-agentic-eng', 'App', 'Synchronizer 19-26-28-342'))

            from context_gatherer import ContextGatherer

            print(f"Loading MIDI mappings from: {midi_path}")

            # Create context gatherer and analyze relationships
            gatherer = ContextGatherer(
                musicxml_path=Path(musicxml_path),
                midi_path=Path(midi_path),
                svg_path=Path(self.svg_file_path)
            )

            context_analysis = gatherer.analyze_and_create_relationships()

            # Extract MIDI mappings from synchronized notes
            for sync_note in context_analysis.synchronized_notes:
                if sync_note.midi_note and sync_note.svg_noteheads:
                    midi_data = {
                        'start_time': sync_note.master_start_time_seconds,
                        'end_time': sync_note.master_end_time_seconds,
                        'velocity': sync_note.midi_note.velocity,
                        'pitch': sync_note.midi_note.pitch,
                        'confidence': sync_note.match_confidence,
                        'timing_source': sync_note.timing_source
                    }

                    # Map to SVG coordinates
                    for svg_notehead in sync_note.svg_noteheads:
                        coord_key = f"{int(svg_notehead.coordinates[0])}_{int(svg_notehead.coordinates[1])}"
                        self.midi_mappings[coord_key] = midi_data

            print(f"✅ Loaded {len(self.midi_mappings)} MIDI mappings for hover tooltips")
            if self.parent_callback:
                self.parent_callback(f"🎹 MIDI mappings loaded: {len(self.midi_mappings)} notes")

        except Exception as e:
            print(f"⚠️ Could not load MIDI mappings: {e}")
            if self.parent_callback:
                self.parent_callback(f"⚠️ MIDI mapping error: {e}")
            self.midi_mappings = {}  # Use empty mappings as fallback

    def parse_svg_for_hover(self, svg_path):
        """Parse SVG and extract element data for hover functionality"""
        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()

            elements_data = []

            def process_element(elem, parent_transform=""):
                elem_data = {
                    'tag': elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag,
                    'attrib': dict(elem.attrib),
                    'text': elem.text.strip() if elem.text and elem.text.strip() else None
                }

                # Classify element type for music notation
                element_type = self.classify_element(elem_data)
                elem_data['music_type'] = element_type

                # Extract coordinates based on element type
                coords = self.extract_coordinates(elem_data)
                if coords:
                    elem_data['coords'] = coords
                    elements_data.append(elem_data)

                # Process children
                for child in elem:
                    process_element(child, parent_transform)

            process_element(root)
            return elements_data

        except Exception as e:
            print(f"Error parsing SVG: {e}")
            return []

    def classify_element(self, elem_data):
        """Classify SVG elements for music notation context"""
        tag = elem_data['tag']
        attrib = elem_data['attrib']

        if tag == 'text':
            text_content = elem_data.get('text', '')
            font_family = attrib.get('font-family', '')

            if 'helsinki' in font_family.lower():
                if text_content in ['4', '2', '1', '8']:
                    return f"Time signature: {text_content}"
                elif text_content in ['?', 'p', 'f', 'mp', 'mf']:
                    return f"Dynamic marking: {text_content}"
                else:
                    return f"Musical symbol: {text_content}"
            else:
                return f"Text: {text_content}"

        elif tag == 'polyline':
            points = attrib.get('points', '')
            if len(points.split()) > 10:
                return "Staff lines"
            else:
                return "Barline or stem"

        elif tag == 'path':
            path_data = attrib.get('d', '')
            if 'C' in path_data or 'c' in path_data:
                return "Slur or tie (curved line)"
            else:
                return "Musical path element"

        elif tag == 'circle':
            return "Notehead (circle)"

        elif tag == 'ellipse':
            return "Notehead (ellipse)"

        else:
            return f"SVG {tag} element"

    def extract_coordinates(self, elem_data):
        """Extract coordinates from various SVG elements"""
        tag = elem_data['tag']
        attrib = elem_data['attrib']

        try:
            if tag == 'text':
                x = float(attrib.get('x', 0))
                y = float(attrib.get('y', 0))
                return {'x': x, 'y': y, 'type': 'point'}

            elif tag == 'polyline':
                points = attrib.get('points', '')
                if points:
                    coords = []
                    for point in points.split():
                        if ',' in point:
                            x, y = point.split(',')
                            coords.append({'x': float(x), 'y': float(y)})
                    return {'points': coords, 'type': 'polyline'}

            elif tag in ['circle', 'ellipse']:
                cx = float(attrib.get('cx', 0))
                cy = float(attrib.get('cy', 0))
                return {'x': cx, 'y': cy, 'type': 'point'}

            elif tag == 'path':
                # For paths, we'll use the first point if available
                d = attrib.get('d', '')
                if d.startswith('M'):
                    coords = d.split()[1].split(',')
                    if len(coords) >= 2:
                        return {'x': float(coords[0]), 'y': float(coords[1]), 'type': 'point'}

        except (ValueError, IndexError):
            pass

        return None

    def create_html_content(self, svg_path):
        """Create HTML content with embedded SVG and JavaScript hover functionality"""

        # Read SVG content
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()

        # Parse elements for hover data
        elements_data = self.parse_svg_for_hover(svg_path)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>SVG Viewer - {os.path.basename(svg_path)}</title>
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                }}

                .svg-container {{
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: auto;
                }}

                svg {{
                    max-width: 100%;
                    height: auto;
                    cursor: crosshair;
                }}

                .tooltip {{
                    position: absolute;
                    background-color: #333;
                    color: white;
                    padding: 8px 12px;
                    border-radius: 5px;
                    font-size: 12px;
                    pointer-events: none;
                    z-index: 1000;
                    max-width: 300px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    display: none;
                }}

                .info-panel {{
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    background-color: rgba(255,255,255,0.95);
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 11px;
                    max-width: 250px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                }}

                .save-position-btn {{
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    cursor: pointer;
                    font-size: 11px;
                    margin-top: 5px;
                    width: 100%;
                }}

                .save-position-btn:hover {{
                    background-color: #45a049;
                }}

                svg * {{
                    pointer-events: all;
                }}
            </style>
        </head>
        <body>
            <div class="info-panel">
                <strong>SVG Viewer</strong><br>
                File: {os.path.basename(svg_path)}<br>
                Hover over elements for details<br>
                <span style="font-size: 9px; color: #666;">⌘+Click to copy • ⌘+Wheel to zoom</span>
            </div>

            <div id="coordsDisplay" style="position: fixed; bottom: 10px; left: 10px; background: rgba(0,0,0,0.8); color: white; padding: 4px 8px; border-radius: 3px; font-family: monospace; font-size: 11px; pointer-events: none; z-index: 1000;">
                SVG: (0, 0)
            </div>

            <div class="svg-container">
                {svg_content}
            </div>

            <div class="tooltip" id="tooltip"></div>

            <script>
                const elementsData = {json.dumps(elements_data, indent=2)};
                let midiMappings = {json.dumps(self.midi_mappings, indent=2)};
                const tooltip = document.getElementById('tooltip');

                // Function to update MIDI mappings without page reload
                function updateMidiMappings(newMappings) {{
                    midiMappings = newMappings;
                    console.log('🎹 MIDI mappings updated:', Object.keys(midiMappings).length, 'notes');
                }}

                // Expose function globally for external access
                window.updateMidiMappings = updateMidiMappings;

                // Save position from manual input
                function saveManualPosition() {{
                    console.log('Manual save position clicked');

                    if (!window.pywebview || !window.pywebview.api) {{
                        alert('PyWebView API not available');
                        return;
                    }}

                    try {{
                        const input = document.getElementById('manualCoords');
                        const coords = input.value.trim();

                        if (!coords) {{
                            alert('Please enter coordinates as: x,y,width,height\\nExample: 500,200,1000,800\\n\\nPosition this window where you want it, then estimate the coordinates.');
                            return;
                        }}

                        // Parse coordinates
                        const parts = coords.split(',').map(s => parseInt(s.trim()));
                        if (parts.length !== 4 || parts.some(isNaN)) {{
                            alert('Please enter coordinates as: x,y,width,height\\nExample: 500,200,1000,800');
                            return;
                        }}

                        const [x, y, width, height] = parts;
                        console.log(`Saving position: x=${{x}}, y=${{y}}, w=${{width}}, h=${{height}}`);

                        // Call the Python API method
                        const result = window.pywebview.api.save_position_with_coords(x, y, width, height);
                        console.log('Save result:', result);

                        // Show visual feedback
                        const btn = event.target;
                        const originalText = btn.innerHTML;
                        btn.innerHTML = '✅ Saved!';
                        btn.style.backgroundColor = '#28a745';
                        setTimeout(() => {{
                            btn.innerHTML = originalText;
                            btn.style.backgroundColor = '#4CAF50';
                        }}, 2000);

                        // Clear the input after successful save
                        input.value = '';

                    }} catch (e) {{
                        console.error('Error saving position:', e);
                        alert('Error: ' + e.message);

                        // Show error feedback
                        const btn = event.target;
                        const originalText = btn.innerHTML;
                        btn.innerHTML = '❌ Error';
                        btn.style.backgroundColor = '#dc3545';
                        setTimeout(() => {{
                            btn.innerHTML = originalText;
                            btn.style.backgroundColor = '#4CAF50';
                        }}, 2000);
                    }}
                }}

                // Copy element info to clipboard on Cmd+Click
                function copyElementInfo(element, index, debugInfo = '') {{
                    try {{
                        const tagName = element.tagName.toLowerCase();

                        // For group elements, drill down to find the actual leaf element
                        let targetElement = element;
                        if (tagName === 'g') {{
                            // Recursively find the deepest non-group element
                            function findLeafElement(el) {{
                                const children = Array.from(el.children);

                                // Look for direct non-group children first
                                const nonGroupChildren = children.filter(child => {{
                                    const childTag = child.tagName.toLowerCase();
                                    return ['text', 'circle', 'ellipse', 'path', 'polyline', 'rect'].includes(childTag);
                                }});

                                if (nonGroupChildren.length > 0) {{
                                    // Prefer text elements for noteheads, then geometric shapes
                                    const textChild = nonGroupChildren.find(c => c.tagName.toLowerCase() === 'text');
                                    if (textChild) return textChild;

                                    const shapeChild = nonGroupChildren.find(c =>
                                        ['circle', 'ellipse', 'path'].includes(c.tagName.toLowerCase())
                                    );
                                    if (shapeChild) return shapeChild;

                                    return nonGroupChildren[0]; // Return first non-group child
                                }}

                                // If only group children, recurse into the first group
                                const groupChildren = children.filter(child =>
                                    child.tagName.toLowerCase() === 'g'
                                );

                                if (groupChildren.length > 0) {{
                                    return findLeafElement(groupChildren[0]);
                                }}

                                return el; // Return original if no children found
                            }}

                            const leafElement = findLeafElement(element);
                            if (leafElement !== element) {{
                                targetElement = leafElement;
                                console.log('Drilled down to leaf element:', targetElement.tagName, targetElement);
                            }}
                        }}

                        const finalTagName = targetElement.tagName.toLowerCase();
                        const matchingData = findMatchingElementData(targetElement);

                        let infoText = `=== SVG Element Info ===\\n`;
                        infoText += `Tag: ${{finalTagName.toUpperCase()}}\\n`;

                        if (matchingData) {{
                            infoText += `Type: ${{matchingData.music_type}}\\n`;

                            if (matchingData.text) {{
                                infoText += `Text: "${{matchingData.text}}"\\n`;
                            }}

                            if (matchingData.coords) {{
                                if (matchingData.coords.type === 'point') {{
                                    infoText += `Position: (${{Math.round(matchingData.coords.x)}}, ${{Math.round(matchingData.coords.y)}})\\n`;
                                }}
                            }}

                            // Add all attributes
                            infoText += `\\nAttributes:\\n`;
                            const attrs = Object.keys(matchingData.attrib);
                            attrs.forEach(attr => {{
                                const value = matchingData.attrib[attr];
                                infoText += `  ${{attr}}: ${{value}}\\n`;
                            }});
                        }} else {{
                            // Fallback for unmatched elements
                            infoText += `Index: ${{index}}\\n`;
                            const rect = targetElement.getBoundingClientRect();
                            infoText += `Screen pos: (${{Math.round(rect.left)}}, ${{Math.round(rect.top)}})\\n`;

                            // For text elements, show text content with more detail
                            if (finalTagName === 'text') {{
                                const cleanText = targetElement.textContent ? targetElement.textContent.trim() : '';
                                const innerHTML = targetElement.innerHTML || '';
                                const nodeValue = targetElement.firstChild ? targetElement.firstChild.nodeValue : '';

                                infoText += `Text Content: "${{cleanText}}"\\n`;
                                infoText += `Inner HTML: "${{innerHTML}}"\\n`;
                                infoText += `Node Value: "${{nodeValue}}"\\n`;

                                // Check for Unicode codepoints - including invisible ones
                                let allText = cleanText || nodeValue || innerHTML;
                                if (allText) {{
                                    const codePoints = Array.from(allText).map(char => {{
                                        const code = char.codePointAt(0);
                                        return 'U+' + code.toString(16).toUpperCase().padStart(4, '0') + ' (' + char + ')';
                                    }}).join(' ');
                                    infoText += `Unicode: ${{codePoints}}\\n`;
                                }} else {{
                                    // Try to extract from DOM more aggressively
                                    const allNodes = targetElement.childNodes;
                                    let foundChars = [];
                                    for (let node of allNodes) {{
                                        if (node.nodeValue) {{
                                            for (let char of node.nodeValue) {{
                                                const code = char.codePointAt(0);
                                                foundChars.push('U+' + code.toString(16).toUpperCase().padStart(4, '0') + ' (' + char + ')');
                                            }}
                                        }}
                                    }}
                                    if (foundChars.length > 0) {{
                                        infoText += `Unicode (deep scan): ${{foundChars.join(' ')}}\\n`;
                                    }} else {{
                                        infoText += `Unicode: No text content found\\n`;
                                    }}
                                }}

                                // Check if this is a Helsinki font notehead
                                const fontFamily = targetElement.getAttribute('font-family') || '';
                                if (fontFamily.includes('Helsinki')) {{
                                    infoText += `Helsinki font detected - this is likely a musical symbol\\n`;
                                }}

                                // Get SVG coordinates
                                const svg = targetElement.closest('svg');
                                if (svg) {{
                                    const rect = targetElement.getBoundingClientRect();
                                    const svgRect = svg.getBoundingClientRect();
                                    const svgX = rect.left - svgRect.left;
                                    const svgY = rect.top - svgRect.top;
                                    infoText += `SVG coords: (${{Math.round(svgX)}}, ${{Math.round(svgY)}})\\n`;
                                }}
                            }}
                            // For group elements, show count of children
                            else if (finalTagName === 'g') {{
                                infoText += `Children: ${{targetElement.children.length}} elements\\n`;
                                const childTags = Array.from(targetElement.children).map(c => c.tagName.toLowerCase());
                                const uniqueTags = [...new Set(childTags)].slice(0, 5); // Show first 5 unique tags
                                infoText += `Child types: ${{uniqueTags.join(', ')}}\\n`;
                            }}

                            // Add DOM attributes (limited to avoid huge output)
                            infoText += `\\nDOM Attributes:\\n`;
                            const attrs = Array.from(targetElement.attributes).slice(0, 10); // Limit to first 10 attributes
                            for (let attr of attrs) {{
                                let value = attr.value;
                                if (value.length > 50) value = value.substring(0, 47) + '...';
                                infoText += `  ${{attr.name}}: ${{value}}\\n`;
                            }}
                        }}

                        // Add debug info if provided
                        if (debugInfo) {{
                            infoText += debugInfo;
                        }}

                        // Copy to clipboard using Python API
                        if (window.pywebview && window.pywebview.api) {{
                            const success = window.pywebview.api.copy_to_clipboard(infoText);
                            if (success) {{
                                showCopyFeedback(element);
                                console.log('Element info copied to clipboard via Python API');
                            }} else {{
                                alert('Failed to copy to clipboard. Element info:\\n\\n' + infoText);
                            }}
                        }} else {{
                            // Fallback: show info in alert if API not available
                            alert('Element info:\\n\\n' + infoText);
                        }}

                    }} catch (e) {{
                        console.error('Error copying element info:', e);
                        alert('Error copying element info: ' + e.message);
                    }}
                }}

                // Show visual feedback when element info is copied
                function showCopyFeedback(element) {{
                    const rect = element.getBoundingClientRect();
                    const feedback = document.createElement('div');
                    feedback.textContent = '📋 Copied!';
                    feedback.style.cssText = `
                        position: fixed;
                        top: ${{rect.top - 30}}px;
                        left: ${{rect.left}}px;
                        background: #28a745;
                        color: white;
                        padding: 4px 8px;
                        border-radius: 3px;
                        font-size: 12px;
                        z-index: 9999;
                        pointer-events: none;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                    `;
                    document.body.appendChild(feedback);

                    setTimeout(() => {{
                        if (feedback.parentNode) {{
                            feedback.parentNode.removeChild(feedback);
                        }}
                    }}, 1500);
                }}

                // Mouse coordinate tracking and zoom
                let currentZoom = 1.0;
                const coordsDisplay = document.getElementById('coordsDisplay');

                // Initialize SVG dimensions on load
                document.addEventListener('DOMContentLoaded', function() {{
                    const svg = document.querySelector('svg');
                    if (svg && !svg.dataset.originalWidth) {{
                        // Store original dimensions
                        let originalWidth, originalHeight;
                        try {{
                            originalWidth = parseFloat(svg.getAttribute('width')) ||
                                          (svg.viewBox && svg.viewBox.baseVal ? svg.viewBox.baseVal.width : null) ||
                                          2592;
                            originalHeight = parseFloat(svg.getAttribute('height')) ||
                                           (svg.viewBox && svg.viewBox.baseVal ? svg.viewBox.baseVal.height : null) ||
                                           3455;
                        }} catch (e) {{
                            originalWidth = 2592;
                            originalHeight = 3455;
                        }}

                        svg.dataset.originalWidth = originalWidth;
                        svg.dataset.originalHeight = originalHeight;
                        currentZoom = 1.0; // Reset zoom to 1.0
                        console.log('SVG initialized with dimensions:', originalWidth, 'x', originalHeight);
                    }}
                }});

                // Update SVG coordinates on mouse move
                document.addEventListener('mousemove', function(e) {{
                    const svg = document.querySelector('svg');
                    if (svg) {{
                        const rect = svg.getBoundingClientRect();
                        const svgX = ((e.clientX - rect.left) / currentZoom);
                        const svgY = ((e.clientY - rect.top) / currentZoom);

                        if (coordsDisplay) {{
                            coordsDisplay.textContent = `SVG: (${{Math.round(svgX)}}, ${{Math.round(svgY)}}) | Zoom: ${{(currentZoom * 100).toFixed(0)}}%`;
                        }}
                    }}
                }});

                // Cmd+Wheel zooming using proper SVG scaling (no quality loss)
                document.addEventListener('wheel', function(e) {{
                    if (e.metaKey || e.ctrlKey) {{
                        e.preventDefault();

                        const svg = document.querySelector('svg');
                        if (svg) {{
                            const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
                            currentZoom *= zoomFactor;

                            // Limit zoom range
                            currentZoom = Math.max(0.1, Math.min(10, currentZoom));

                            // Use SVG width/height scaling instead of CSS transform for crisp rendering
                            let originalWidth, originalHeight;

                            // Try to get original dimensions safely
                            try {{
                                originalWidth = parseFloat(svg.getAttribute('width')) ||
                                              (svg.viewBox && svg.viewBox.baseVal ? svg.viewBox.baseVal.width : null) ||
                                              2592;
                                originalHeight = parseFloat(svg.getAttribute('height')) ||
                                               (svg.viewBox && svg.viewBox.baseVal ? svg.viewBox.baseVal.height : null) ||
                                               3455;
                            }} catch (e) {{
                                console.log('Using fallback dimensions');
                                originalWidth = 2592;
                                originalHeight = 3455;
                            }}

                            // Use stored original dimensions for consistent scaling
                            const baseWidth = parseFloat(svg.dataset.originalWidth) || originalWidth;
                            const baseHeight = parseFloat(svg.dataset.originalHeight) || originalHeight;

                            // Store if not already stored
                            if (!svg.dataset.originalWidth) {{
                                svg.dataset.originalWidth = baseWidth;
                                svg.dataset.originalHeight = baseHeight;
                            }}

                            const newWidth = baseWidth * currentZoom;
                            const newHeight = baseHeight * currentZoom;

                            console.log(`Zoom: ${{currentZoom.toFixed(2)}} | Base: ${{baseWidth}}x${{baseHeight}} | New: ${{newWidth.toFixed(0)}}x${{newHeight.toFixed(0)}}`);

                            svg.setAttribute('width', newWidth);
                            svg.setAttribute('height', newHeight);

                            // Update container scrollable area
                            const container = svg.parentElement;
                            if (container) {{
                                container.style.overflow = 'auto';
                                container.style.width = '100%';
                                container.style.height = '100%';
                            }}
                        }}
                    }}
                }});

                // Add event listeners to all SVG elements
                document.addEventListener('DOMContentLoaded', function() {{
                    const svgElements = document.querySelectorAll('svg *');

                    svgElements.forEach((element, index) => {{
                        element.addEventListener('mouseenter', function(e) {{
                            showTooltip(e, element, index);
                        }});

                        element.addEventListener('mousemove', function(e) {{
                            updateTooltipPosition(e);
                        }});

                        element.addEventListener('mouseleave', function(e) {{
                            hideTooltip();
                        }});

                        // Add click handler for Cmd+Click to copy element info
                        element.addEventListener('click', function(e) {{
                            if (e.metaKey || e.ctrlKey) {{ // Cmd on Mac, Ctrl on Windows/Linux
                                e.preventDefault();

                                // Find the most specific element at the click point
                                const clickX = e.clientX;
                                const clickY = e.clientY;
                                const elementsAtPoint = document.elementsFromPoint(clickX, clickY);

                                // Filter to SVG elements and find the smallest/most specific one
                                const svgElements = elementsAtPoint.filter(el =>
                                    el.tagName && ['text', 'circle', 'ellipse', 'path', 'polyline', 'rect', 'g'].includes(el.tagName.toLowerCase())
                                );

                                // Prefer non-group elements, or the smallest group
                                let bestElement = element;
                                for (let el of svgElements) {{
                                    if (el.tagName.toLowerCase() !== 'g') {{
                                        bestElement = el;
                                        break; // Prefer any non-group element
                                    }} else if (el.children.length < bestElement.children.length) {{
                                        bestElement = el; // Prefer smaller groups
                                    }}
                                }}

                                console.log('Elements at click point:', svgElements.map(el => el.tagName));
                                console.log('Selected best element:', bestElement.tagName, bestElement);

                                // Add debug info about all elements at click point
                                let debugInfo = `\\n=== DEBUG: All elements at click point ===\\n`;
                                svgElements.slice(0, 5).forEach((el, i) => {{
                                    debugInfo += `${{i+1}}. ${{el.tagName.toUpperCase()}}`;
                                    if (el.textContent && el.textContent.trim()) {{
                                        debugInfo += ` - Text: "${{el.textContent.trim()}}"`;
                                    }}
                                    if (el.getAttribute('font-family')) {{
                                        debugInfo += ` - Font: ${{el.getAttribute('font-family')}}`;
                                    }}
                                    debugInfo += `\\n`;
                                }});

                                copyElementInfo(bestElement, index, debugInfo);
                            }}
                        }});
                    }});
                }});

                function showTooltip(event, element, index) {{
                    const tagName = element.tagName.toLowerCase();
                    let content = `<strong>${{tagName.toUpperCase()}}</strong><br>`;

                    // Find matching element data
                    const matchingData = findMatchingElementData(element);

                    if (matchingData) {{
                        content += `Type: ${{matchingData.music_type}}<br>`;

                        if (matchingData.text) {{
                            content += `Text: "${{matchingData.text}}"<br>`;
                        }}

                        if (matchingData.coords) {{
                            if (matchingData.coords.type === 'point') {{
                                content += `Position: (${{Math.round(matchingData.coords.x)}}, ${{Math.round(matchingData.coords.y)}})<br>`;

                                // Check for MIDI mapping based on coordinates
                                const coordKey = `${{Math.round(matchingData.coords.x)}}_${{Math.round(matchingData.coords.y)}}`;
                                let midi = midiMappings[coordKey];

                                console.log(`🔍 Searching for MIDI at: ${{coordKey}}`);
                                console.log(`📊 Available keys:`, Object.keys(midiMappings));

                                // If no exact match, try nearby coordinates for coordinate transformation offset
                                if (!midi) {{
                                    console.log(`❌ No exact match, searching nearby...`);
                                    for (let dx = -5; dx <= 5 && !midi; dx++) {{
                                        for (let dy = -500; dy <= 500; dy += 5) {{
                                            const nearKey = `${{Math.round(matchingData.coords.x) + dx}}_${{Math.round(matchingData.coords.y) + dy}}`;
                                            if (midiMappings[nearKey]) {{
                                                console.log(`✅ Found match at: ${{nearKey}}`);
                                                midi = midiMappings[nearKey];
                                                break;
                                            }}
                                        }}
                                    }}
                                    if (!midi) {{
                                        console.log(`❌ No nearby matches found within tolerance`);
                                    }}
                                }}

                                if (midi) {{
                                    content += `<br><strong>🎹 MIDI Data:</strong><br>`;
                                    content += `Start: ${{midi.start_time.toFixed(2)}}s<br>`;
                                    if (midi.end_time) {{
                                        content += `End: ${{midi.end_time.toFixed(2)}}s<br>`;
                                        content += `Duration: ${{(midi.end_time - midi.start_time).toFixed(2)}}s<br>`;
                                    }}
                                    content += `Velocity: ${{midi.velocity}}<br>`;
                                    content += `Pitch: ${{midi.pitch}}<br>`;
                                    content += `Confidence: ${{(midi.confidence * 100).toFixed(1)}}%<br>`;
                                    content += `Source: ${{midi.timing_source}}<br>`;
                                }}
                            }}
                        }}

                        // Add attributes
                        const attrs = Object.keys(matchingData.attrib);
                        if (attrs.length > 0) {{
                            content += '<br><strong>Attributes:</strong><br>';
                            attrs.slice(0, 3).forEach(attr => {{
                                let value = matchingData.attrib[attr];
                                if (value.length > 30) value = value.substring(0, 30) + '...';
                                content += `${{attr}}: ${{value}}<br>`;
                            }});
                        }}
                    }} else {{
                        // Fallback for unmatched elements
                        content += `Index: ${{index}}<br>`;
                        const rect = element.getBoundingClientRect();
                        content += `Screen pos: (${{Math.round(rect.left)}}, ${{Math.round(rect.top)}})<br>`;

                        if (element.textContent && element.textContent.trim()) {{
                            content += `Text: "${{element.textContent.trim()}}"<br>`;
                        }}

                        // For fallback elements, try to find MIDI data by proximity
                        const svgCoords = getSVGCoordinates(element);
                        if (svgCoords) {{
                            content += `SVG coords: (${{Math.round(svgCoords.x)}}, ${{Math.round(svgCoords.y)}})<br>`;

                            // Check for exact match first
                            const exactKey = `${{Math.round(svgCoords.x)}}_${{Math.round(svgCoords.y)}}`;
                            let midi = midiMappings[exactKey];

                            // If no exact match, try nearby coordinates (within 500 pixels for coordinate transformation offset)
                            if (!midi) {{
                                for (let dx = -5; dx <= 5 && !midi; dx++) {{
                                    for (let dy = -500; dy <= 500; dy += 5) {{
                                        const nearKey = `${{Math.round(svgCoords.x) + dx}}_${{Math.round(svgCoords.y) + dy}}`;
                                        if (midiMappings[nearKey]) {{
                                            midi = midiMappings[nearKey];
                                            content += `🎯 MIDI match found nearby<br>`;
                                            break;
                                        }}
                                    }}
                                }}
                            }}

                            if (midi) {{
                                content += `<br><strong>🎹 MIDI Data:</strong><br>`;
                                content += `Start: ${{midi.start_time.toFixed(2)}}s<br>`;
                                if (midi.end_time) {{
                                    content += `End: ${{midi.end_time.toFixed(2)}}s<br>`;
                                    content += `Duration: ${{(midi.end_time - midi.start_time).toFixed(2)}}s<br>`;
                                }}
                                content += `Velocity: ${{midi.velocity}}<br>`;
                                content += `Pitch: ${{midi.pitch}}<br>`;
                                content += `Confidence: ${{(midi.confidence * 100).toFixed(1)}}%<br>`;
                                content += `Source: ${{midi.timing_source}}<br>`;
                            }} else {{
                                // Debug: Show available MIDI coordinates for troubleshooting
                                content += `<br><strong>🔍 Debug Info:</strong><br>`;
                                content += `Looking for: ${{exactKey}}<br>`;
                                const availableKeys = Object.keys(midiMappings).slice(0, 5);
                                if (availableKeys.length > 0) {{
                                    content += `Available coords: ${{availableKeys.join(', ')}}<br>`;
                                }}
                                content += `Total MIDI mappings: ${{Object.keys(midiMappings).length}}<br>`;
                            }}
                        }}
                    }}

                    tooltip.innerHTML = content;
                    tooltip.style.display = 'block';
                    updateTooltipPosition(event);
                }}

                // Helper function to get SVG coordinates from any element
                function getSVGCoordinates(element) {{
                    try {{
                        const svg = element.closest('svg');
                        if (!svg) return null;

                        const rect = element.getBoundingClientRect();
                        const svgRect = svg.getBoundingClientRect();

                        const svgX = (rect.left + rect.width/2) - svgRect.left;
                        const svgY = (rect.top + rect.height/2) - svgRect.top;

                        // Account for zoom level
                        return {{
                            x: svgX / currentZoom,
                            y: svgY / currentZoom
                        }};
                    }} catch (e) {{
                        return null;
                    }}
                }}

                function findMatchingElementData(element) {{
                    const tagName = element.tagName.toLowerCase();

                    // Try to match by tag and attributes with more specific matching
                    for (let data of elementsData) {{
                        if (data.tag === tagName) {{
                            // For text elements, match by content and position
                            if (tagName === 'text' && element.textContent) {{
                                const elementText = element.textContent.trim();
                                if (data.text === elementText) {{
                                    // Additional check: also match by position if available
                                    const elementX = element.getAttribute('x');
                                    const elementY = element.getAttribute('y');
                                    if (elementX && elementY && data.attrib.x && data.attrib.y) {{
                                        if (Math.abs(parseFloat(elementX) - parseFloat(data.attrib.x)) < 1.0 &&
                                            Math.abs(parseFloat(elementY) - parseFloat(data.attrib.y)) < 1.0) {{
                                            return data;
                                        }}
                                    }} else {{
                                        return data; // Match by text if no position data
                                    }}
                                }}
                            }}
                            // For other elements, try to match by attributes
                            else if (tagName !== 'text') {{
                                // Try to match by key attributes like x, y, points, d, etc.
                                let attributeMatch = false;

                                if (tagName === 'polyline' && element.getAttribute('points')) {{
                                    const elementPoints = element.getAttribute('points');
                                    if (data.attrib.points === elementPoints) {{
                                        return data;
                                    }}
                                }}
                                else if (tagName === 'path' && element.getAttribute('d')) {{
                                    const elementPath = element.getAttribute('d');
                                    if (data.attrib.d === elementPath) {{
                                        return data;
                                    }}
                                }}
                                else if ((tagName === 'circle' || tagName === 'ellipse') && element.getAttribute('cx')) {{
                                    const elementCx = element.getAttribute('cx');
                                    const elementCy = element.getAttribute('cy');
                                    if (data.attrib.cx === elementCx && data.attrib.cy === elementCy) {{
                                        return data;
                                    }}
                                }}
                                // Enhanced attribute matching for elements with x,y coordinates
                                else if (element.getAttribute('x') && element.getAttribute('y')) {{
                                    const elementX = element.getAttribute('x');
                                    const elementY = element.getAttribute('y');
                                    if (data.attrib.x && data.attrib.y) {{
                                        // Use tolerance-based matching for coordinates
                                        if (Math.abs(parseFloat(elementX) - parseFloat(data.attrib.x)) < 1.0 &&
                                            Math.abs(parseFloat(elementY) - parseFloat(data.attrib.y)) < 1.0) {{
                                            return data;
                                        }}
                                    }}
                                }}
                                // Match by transform attribute for positioned groups
                                else if (element.getAttribute('transform') && data.attrib.transform) {{
                                    if (element.getAttribute('transform') === data.attrib.transform) {{
                                        return data;
                                    }}
                                }}
                                // Multi-attribute matching for unique identification
                                else {{
                                    let matchedAttributes = 0;
                                    let totalChecked = 0;

                                    // Check key identifying attributes
                                    const keyAttributes = ['x', 'y', 'width', 'height', 'id', 'class', 'style', 'transform'];

                                    for (let attr of keyAttributes) {{
                                        const elementAttr = element.getAttribute(attr);
                                        const dataAttr = data.attrib[attr];

                                        if (elementAttr && dataAttr) {{
                                            totalChecked++;
                                            if (elementAttr === dataAttr) {{
                                                matchedAttributes++;
                                            }}
                                        }}
                                    }}

                                    // Only return if we have a strong match (2+ attributes or high match rate)
                                    if (matchedAttributes >= 2 || (totalChecked > 0 && matchedAttributes / totalChecked >= 0.8)) {{
                                        return data;
                                    }}
                                }}
                            }}
                        }}
                    }}

                    return null;
                }}

                function updateTooltipPosition(event) {{
                    const x = event.clientX + 10;
                    const y = event.clientY - 10;

                    tooltip.style.left = x + 'px';
                    tooltip.style.top = y + 'px';
                }}

                function hideTooltip() {{
                    tooltip.style.display = 'none';
                }}

                // Log to parent window if available
                function logToParent(message) {{
                    try {{
                        if (window.pywebview) {{
                            window.pywebview.api.log_message(message);
                        }}
                    }} catch (e) {{
                        console.log(message);
                    }}
                }}

                // Log successful load
                logToParent('SVG Viewer loaded successfully with ' + elementsData.length + ' parsed elements');
            </script>
        </body>
        </html>
        """

        return html_content

    def log_message(self, message):
        """API method for JavaScript to log messages"""
        print(f"SVG Viewer: {message}")
        if self.parent_callback:
            self.parent_callback(f"SVG Viewer: {message}")

    def save_position_with_coords(self, x, y, width, height):
        """API method for JavaScript to save window position with actual coordinates"""
        try:
            import time

            settings = {
                'x': int(x),
                'y': int(y),
                'width': int(width),
                'height': int(height),
                'last_svg_file': self.svg_file_path,
                'manually_saved': True,
                'saved_at': time.time(),
                'note': 'Position saved manually with actual window coordinates'
            }

            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            print(f"✅ Position saved: x={x}, y={y}, w={width}, h={height}")
            if self.parent_callback:
                self.parent_callback(f"📍 Position saved: x={x}, y={y}")

            # Update internal variables for next launch
            self.window_x = int(x)
            self.window_y = int(y)
            self.window_width = int(width)
            self.window_height = int(height)

            return True

        except Exception as e:
            print(f"Error saving position with coords: {e}")
            if self.parent_callback:
                self.parent_callback(f"❌ Error saving position: {e}")
            return False

    def save_current_position(self):
        """Legacy API method - kept for backward compatibility"""
        return self.save_position_with_coords(self.window_x, self.window_y, self.window_width, self.window_height)

    def update_midi_mappings(self, mappings_json):
        """API method to update MIDI mappings without restarting viewer"""
        try:
            import json
            # Update Python-side mappings
            self.midi_mappings = json.loads(mappings_json)

            # Update JavaScript-side mappings via evaluate_js
            if self.window:
                try:
                    js_code = f"window.updateMidiMappings({mappings_json});"
                    self.window.evaluate_js(js_code)
                except Exception as js_error:
                    self.log_message(f"⚠️ JS update failed: {js_error}")

            self.log_message(f"🎹 Updated MIDI mappings: {len(self.midi_mappings)} notes")
            return True
        except Exception as e:
            self.log_message(f"❌ Error updating MIDI mappings: {e}")
            return False

    def copy_to_clipboard(self, text):
        """API method for JavaScript to copy text to system clipboard"""
        try:
            import subprocess
            import platform

            system = platform.system()

            if system == "Darwin":  # macOS
                process = subprocess.run(['pbcopy'], input=text, text=True, check=True)
            elif system == "Windows":
                process = subprocess.run(['clip'], input=text, text=True, check=True)
            elif system == "Linux":
                # Try xclip first, then xsel as fallback
                try:
                    process = subprocess.run(['xclip', '-selection', 'clipboard'], input=text, text=True, check=True)
                except FileNotFoundError:
                    process = subprocess.run(['xsel', '--clipboard', '--input'], input=text, text=True, check=True)
            else:
                print(f"Unsupported system for clipboard: {system}")
                return False

            print(f"✅ Copied to clipboard: {len(text)} characters")
            if self.parent_callback:
                self.parent_callback(f"📋 Element info copied to clipboard ({len(text)} chars)")
            return True

        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            if self.parent_callback:
                self.parent_callback(f"❌ Clipboard error: {e}")
            return False

    def set_svg_file(self, svg_path):
        """Set the SVG file to display"""
        self.svg_file_path = svg_path
        if self.window:
            # Reload with new SVG
            html_content = self.create_html_content(svg_path)
            self.window.load_html(html_content)

    def show(self, svg_path=None, musicxml_path=None, midi_path=None):
        """Show the SVG viewer window with optional MIDI mappings"""
        if svg_path:
            self.svg_file_path = svg_path

        if not self.svg_file_path or not os.path.exists(self.svg_file_path):
            print("No valid SVG file specified")
            return

        # Load MIDI mappings if provided
        if musicxml_path and midi_path:
            self.load_midi_mappings(musicxml_path, midi_path)

        # Create HTML content
        html_content = self.create_html_content(self.svg_file_path)

        # Create webview window with exposed API (no initial positioning to avoid pywebview bugs)
        self.window = webview.create_window(
            f'SVG Viewer - {os.path.basename(self.svg_file_path)}',
            html=html_content,
            width=self.window_width,
            height=self.window_height,
            resizable=True,
            on_top=False,
            js_api=self
        )

        # Start webview
        webview.start(debug=False)

    def show_in_subprocess(self, svg_path=None):
        """Show the SVG viewer in a separate process to avoid main thread issues"""
        import subprocess
        import sys

        if svg_path and os.path.exists(svg_path):
            # Run in separate process to avoid main thread issues
            subprocess.Popen([sys.executable, __file__, svg_path])
        else:
            subprocess.Popen([sys.executable, __file__])

def main():
    """Test the SVG viewer"""
    import sys

    # Check for command line argument
    if len(sys.argv) > 1:
        svg_path = sys.argv[1]
    else:
        svg_path = "PRPs-agentic-eng/Base/SS 9 full.svg"

    if os.path.exists(svg_path):
        viewer = SVGViewerWebView()
        viewer.show(svg_path)
    else:
        print(f"SVG file not found: {svg_path}")

if __name__ == "__main__":
    main()