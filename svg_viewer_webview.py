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
                Hover over elements for details
            </div>

            <div class="svg-container">
                {svg_content}
            </div>

            <div class="tooltip" id="tooltip"></div>

            <script>
                const elementsData = {json.dumps(elements_data, indent=2)};
                const tooltip = document.getElementById('tooltip');

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
                    }}

                    tooltip.innerHTML = content;
                    tooltip.style.display = 'block';
                    updateTooltipPosition(event);
                }}

                function findMatchingElementData(element) {{
                    const tagName = element.tagName.toLowerCase();

                    // Try to match by tag and attributes
                    for (let data of elementsData) {{
                        if (data.tag === tagName) {{
                            // For text elements, match by content and position
                            if (tagName === 'text' && element.textContent) {{
                                if (data.text === element.textContent.trim()) {{
                                    return data;
                                }}
                            }}
                            // For other elements, basic tag matching
                            else if (tagName !== 'text') {{
                                return data;
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

    def set_svg_file(self, svg_path):
        """Set the SVG file to display"""
        self.svg_file_path = svg_path
        if self.window:
            # Reload with new SVG
            html_content = self.create_html_content(svg_path)
            self.window.load_html(html_content)

    def show(self, svg_path=None):
        """Show the SVG viewer window"""
        if svg_path:
            self.svg_file_path = svg_path

        if not self.svg_file_path or not os.path.exists(self.svg_file_path):
            print("No valid SVG file specified")
            return

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