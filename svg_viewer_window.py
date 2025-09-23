#!/usr/bin/env python3
"""
SVG Viewer Window - Interactive SVG inspector with hover details

Provides a separate, draggable window that displays SVG files with real-time
element inspection. Shows detailed information about SVG elements when hovering
with the mouse, designed specifically for debugging music notation SVGs.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET
import re
import json
from pathlib import Path

class SVGViewerWindow:
    def __init__(self, parent=None, svg_file=None):
        self.parent = parent
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title("SVG Inspector")

        # Settings file for window preferences
        self.project_root = Path(__file__).parent
        self.settings_file = self.project_root / "svg_viewer_settings.json"

        # Load saved window settings
        self.load_window_settings()

        # Bind window close event to save settings
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # SVG data storage
        self.svg_tree = None
        self.svg_elements = []
        self.current_file = svg_file

        # Canvas and interaction state
        self.canvas = None
        self.hover_tooltip = None
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0

        self.setup_ui()

        # Load SVG if provided
        if svg_file and Path(svg_file).exists():
            self.load_svg_file(svg_file)

    def setup_ui(self):
        """Setup the SVG viewer interface"""
        # Top toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill='x', padx=5, pady=2)

        # File controls
        ttk.Button(toolbar, text="📁 Open SVG", command=self.browse_svg_file).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🔍 Zoom In", command=lambda: self.zoom(1.2)).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🔍 Zoom Out", command=lambda: self.zoom(0.8)).pack(side='left', padx=2)
        ttk.Button(toolbar, text="↺ Reset", command=self.reset_view).pack(side='left', padx=2)

        # Remember position button
        ttk.Button(toolbar, text="📍 Remember", command=self.save_current_position).pack(side='left', padx=2)

        # File info label
        self.file_label = ttk.Label(toolbar, text="No SVG loaded", foreground="gray")
        self.file_label.pack(side='right', padx=5)

        # Main content area with scrollable canvas
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=5, pady=2)

        # Canvas with scrollbars
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill='both', expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg='white', cursor='crosshair')

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient='horizontal', command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack scrollbars and canvas
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        self.canvas.pack(side='left', fill='both', expand=True)

        # Bind mouse events
        self.canvas.bind('<Motion>', self.on_mouse_move)
        self.canvas.bind('<Leave>', self.hide_tooltip)
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)  # Windows/Linux
        self.canvas.bind('<Button-4>', self.on_mousewheel)    # Linux
        self.canvas.bind('<Button-5>', self.on_mousewheel)    # Linux

        # Tooltip window
        self.tooltip_window = None

        # Bottom status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief='sunken', anchor='w')
        self.status_bar.pack(fill='x', padx=5, pady=2)

    def browse_svg_file(self):
        """Browse and load an SVG file"""
        filetypes = [
            ("SVG files", "*.svg"),
            ("All files", "*.*")
        ]

        initial_dir = str(Path.cwd() / "PRPs-agentic-eng" / "Base")
        if not Path(initial_dir).exists():
            initial_dir = str(Path.cwd())

        filename = filedialog.askopenfilename(
            title="Select SVG File",
            filetypes=filetypes,
            initialdir=initial_dir
        )

        if filename:
            self.load_svg_file(filename)

    def load_svg_file(self, file_path):
        """Load and parse an SVG file"""
        try:
            self.current_file = file_path

            # Parse SVG
            self.svg_tree = ET.parse(file_path)

            # Extract SVG dimensions and viewBox
            root = self.svg_tree.getroot()

            # Get SVG dimensions
            width = self.parse_dimension(root.get('width', '800'))
            height = self.parse_dimension(root.get('height', '600'))

            # Parse viewBox if available
            viewbox = root.get('viewBox')
            if viewbox:
                vb_parts = viewbox.split()
                if len(vb_parts) == 4:
                    vb_x, vb_y, vb_width, vb_height = map(float, vb_parts)
                    width = vb_width
                    height = vb_height

            # Clear canvas and reset view
            self.canvas.delete('all')
            self.reset_view()

            # Set canvas size
            self.canvas.configure(scrollregion=(0, 0, width, height))

            # Extract all SVG elements for hover detection
            self.extract_svg_elements()

            # Render basic SVG preview with saved zoom
            self.render_svg_preview()

            # Update UI
            filename = Path(file_path).name
            self.file_label.config(text=filename, foreground="black")
            self.status_bar.config(text=f"Loaded: {filename} ({len(self.svg_elements)} elements)")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load SVG file:\n{str(e)}")
            self.status_bar.config(text="Error loading SVG")

    def parse_dimension(self, dim_str):
        """Parse SVG dimension string (handles px, mm, etc.)"""
        if not dim_str:
            return 100

        # Extract numeric value (remove units)
        match = re.match(r'([0-9.]+)', str(dim_str))
        if match:
            return float(match.group(1))
        return 100

    def extract_svg_elements(self):
        """Extract all SVG elements with their properties for hover detection"""
        self.svg_elements = []

        if not self.svg_tree:
            return

        def extract_recursive(element, parent_transform=None):
            """Recursively extract elements and their computed properties"""

            # Calculate cumulative transform
            transform = parent_transform or {'scale': 1.0, 'tx': 0, 'ty': 0}

            # Parse transform attribute if present
            if 'transform' in element.attrib:
                transform = self.parse_transform(element.get('transform'), transform)

            # Extract element data
            elem_data = {
                'tag': element.tag.split('}')[-1] if '}' in element.tag else element.tag,
                'attrib': dict(element.attrib),
                'text': element.text.strip() if element.text else None,
                'transform': transform,
                'bbox': self.calculate_bbox(element, transform),
                'element': element
            }

            # Add music notation specific data
            if elem_data['tag'] == 'text':
                elem_data['music_type'] = self.classify_music_text(elem_data)
            elif elem_data['tag'] == 'polyline':
                elem_data['music_type'] = self.classify_polyline(elem_data)

            self.svg_elements.append(elem_data)

            # Process children
            for child in element:
                extract_recursive(child, transform)

        # Start extraction from root
        root = self.svg_tree.getroot()
        for child in root:
            extract_recursive(child)

    def parse_transform(self, transform_str, parent_transform):
        """Parse SVG transform attribute"""
        # Simple matrix transform parser
        # For full implementation, would need more sophisticated parsing

        transform = dict(parent_transform)

        if 'matrix(' in transform_str:
            # Extract matrix values: matrix(a,b,c,d,e,f)
            match = re.search(r'matrix\(([^)]+)\)', transform_str)
            if match:
                values = [float(x.strip()) for x in match.group(1).split(',')]
                if len(values) >= 6:
                    # Apply matrix transform (simplified)
                    transform['scale'] *= values[0]  # a (scale x)
                    transform['tx'] += values[4]     # e (translate x)
                    transform['ty'] += values[5]     # f (translate y)

        return transform

    def calculate_bbox(self, element, transform):
        """Calculate bounding box for an element"""
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag

        scale = transform.get('scale', 1.0)
        tx = transform.get('tx', 0)
        ty = transform.get('ty', 0)

        if tag == 'text':
            x = float(element.get('x', 0)) * scale + tx
            y = float(element.get('y', 0)) * scale + ty
            # Estimate text dimensions
            font_size = float(element.get('font-size', 12))
            text_len = len(element.text or '') * font_size * 0.6
            return {'x': x, 'y': y - font_size, 'width': text_len, 'height': font_size}

        elif tag == 'polyline':
            points_str = element.get('points', '')
            if points_str:
                coords = [float(x) for x in points_str.replace(',', ' ').split()]
                if len(coords) >= 4:
                    xs = [coords[i] * scale + tx for i in range(0, len(coords), 2)]
                    ys = [coords[i] * scale + ty for i in range(1, len(coords), 2)]
                    return {
                        'x': min(xs), 'y': min(ys),
                        'width': max(xs) - min(xs),
                        'height': max(ys) - min(ys)
                    }

        # Default small bbox
        return {'x': 0, 'y': 0, 'width': 10, 'height': 10}

    def classify_music_text(self, elem_data):
        """Classify text elements as music notation types"""
        font_family = elem_data['attrib'].get('font-family', '')
        text = elem_data.get('text', '')

        if 'Helsinki' in font_family:
            return f"Note symbol: '{text}'"
        elif 'Opus' in font_family:
            return f"Music symbol: '{text}'"
        elif text in ['Flûte', 'Violon', 'Piano']:
            return f"Instrument name: '{text}'"
        elif text in ['p', 'f', 'mp', 'mf']:
            return f"Dynamic: '{text}'"
        else:
            return f"Text: '{text}'"

    def classify_polyline(self, elem_data):
        """Classify polyline elements as music notation types"""
        stroke_width = elem_data['attrib'].get('stroke-width', '1')

        if stroke_width == '2.25':
            return "Staff line"
        elif stroke_width in ['5', '16']:
            return "Barline"
        else:
            return f"Line (width: {stroke_width})"

    def render_svg_preview(self):
        """Render a basic preview of the SVG on canvas"""
        # Simple rendering for basic shapes
        for elem_data in self.svg_elements:
            self.render_element_preview(elem_data)

    def render_element_preview(self, elem_data):
        """Render a single element preview"""
        if elem_data['tag'] == 'polyline':
            self.render_polyline_preview(elem_data)
        elif elem_data['tag'] == 'text':
            self.render_text_preview(elem_data)

    def render_polyline_preview(self, elem_data):
        """Render polyline preview"""
        points_str = elem_data['attrib'].get('points', '')
        if not points_str:
            return

        coords = [float(x) for x in points_str.replace(',', ' ').split()]
        if len(coords) < 4:
            return

        # Apply transform
        transform = elem_data['transform']
        scale = transform.get('scale', 1.0)
        tx = transform.get('tx', 0)
        ty = transform.get('ty', 0)

        # Convert to canvas coordinates
        canvas_coords = []
        for i in range(0, len(coords), 2):
            x = coords[i] * scale + tx
            y = coords[i + 1] * scale + ty
            canvas_coords.extend([x * self.scale_factor + self.offset_x,
                                y * self.scale_factor + self.offset_y])

        # Get line properties
        stroke_width = float(elem_data['attrib'].get('stroke-width', 1))
        color = elem_data['attrib'].get('stroke', 'black')

        # Draw line
        if len(canvas_coords) >= 4:
            self.canvas.create_line(canvas_coords,
                                  width=stroke_width * self.scale_factor,
                                  fill=color,
                                  tags='svg_element')

    def render_text_preview(self, elem_data):
        """Render text preview"""
        x = float(elem_data['attrib'].get('x', 0))
        y = float(elem_data['attrib'].get('y', 0))

        # Apply transform
        transform = elem_data['transform']
        scale = transform.get('scale', 1.0)
        tx = transform.get('tx', 0)
        ty = transform.get('ty', 0)

        canvas_x = (x * scale + tx) * self.scale_factor + self.offset_x
        canvas_y = (y * scale + ty) * self.scale_factor + self.offset_y

        text = elem_data.get('text', '')
        font_size = int(float(elem_data['attrib'].get('font-size', 12)) * self.scale_factor)

        if text and font_size > 2:
            self.canvas.create_text(canvas_x, canvas_y,
                                  text=text,
                                  font=('Arial', max(8, font_size)),
                                  anchor='nw',
                                  tags='svg_element')

    def on_mouse_move(self, event):
        """Handle mouse movement for hover detection"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Convert to SVG coordinates
        svg_x = (canvas_x - self.offset_x) / self.scale_factor
        svg_y = (canvas_y - self.offset_y) / self.scale_factor

        # Find element under cursor
        hovered_element = self.find_element_at_position(svg_x, svg_y)

        if hovered_element:
            self.show_tooltip(event.x_root, event.y_root, hovered_element)
            self.status_bar.config(text=f"Hover: {hovered_element['tag']} at ({svg_x:.1f}, {svg_y:.1f})")
        else:
            self.hide_tooltip()
            self.status_bar.config(text=f"Position: ({svg_x:.1f}, {svg_y:.1f})")

    def find_element_at_position(self, x, y):
        """Find SVG element at given position"""
        for elem_data in reversed(self.svg_elements):  # Check top elements first
            bbox = elem_data['bbox']
            if (bbox['x'] <= x <= bbox['x'] + bbox['width'] and
                bbox['y'] <= y <= bbox['y'] + bbox['height']):
                return elem_data
        return None

    def show_tooltip(self, x, y, elem_data):
        """Show tooltip with element details"""
        self.hide_tooltip()  # Hide existing tooltip

        self.tooltip_window = tk.Toplevel(self.root)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x + 10}+{y + 10}")

        # Create tooltip content
        tooltip_text = self.format_element_details(elem_data)

        label = tk.Label(self.tooltip_window,
                        text=tooltip_text,
                        background='lightyellow',
                        relief='solid',
                        borderwidth=1,
                        font=('Consolas', 9),
                        justify='left')
        label.pack()

    def format_element_details(self, elem_data):
        """Format element details for tooltip"""
        lines = []

        # Element type and music classification
        lines.append(f"Tag: {elem_data['tag']}")
        if 'music_type' in elem_data:
            lines.append(f"Type: {elem_data['music_type']}")

        # Position and size
        bbox = elem_data['bbox']
        lines.append(f"Position: ({bbox['x']:.1f}, {bbox['y']:.1f})")
        lines.append(f"Size: {bbox['width']:.1f} × {bbox['height']:.1f}")

        # Key attributes
        attrib = elem_data['attrib']
        important_attrs = ['font-family', 'font-size', 'stroke-width', 'fill', 'stroke']

        for attr in important_attrs:
            if attr in attrib:
                value = attrib[attr]
                if len(value) > 30:
                    value = value[:27] + "..."
                lines.append(f"{attr}: {value}")

        # Text content
        if elem_data.get('text'):
            text = elem_data['text']
            if len(text) > 20:
                text = text[:17] + "..."
            lines.append(f"Text: '{text}'")

        return '\n'.join(lines)

    def hide_tooltip(self, event=None):
        """Hide tooltip window"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def on_click(self, event):
        """Handle canvas clicks"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        svg_x = (canvas_x - self.offset_x) / self.scale_factor
        svg_y = (canvas_y - self.offset_y) / self.scale_factor

        clicked_element = self.find_element_at_position(svg_x, svg_y)

        if clicked_element:
            self.show_element_details(clicked_element)

    def show_element_details(self, elem_data):
        """Show detailed element information in a dialog"""
        details = []
        details.append(f"Element: {elem_data['tag']}")

        if 'music_type' in elem_data:
            details.append(f"Music Type: {elem_data['music_type']}")

        details.append("\nAttributes:")
        for key, value in elem_data['attrib'].items():
            details.append(f"  {key}: {value}")

        if elem_data.get('text'):
            details.append(f"\nText Content: '{elem_data['text']}'")

        bbox = elem_data['bbox']
        details.append(f"\nBounding Box:")
        details.append(f"  Position: ({bbox['x']:.2f}, {bbox['y']:.2f})")
        details.append(f"  Size: {bbox['width']:.2f} × {bbox['height']:.2f}")

        messagebox.showinfo("Element Details", '\n'.join(details))

    def zoom(self, factor):
        """Zoom the view"""
        self.scale_factor *= factor
        self.redraw()

    def reset_view(self):
        """Reset view to default"""
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.redraw()

    def redraw(self):
        """Redraw the SVG with current view settings"""
        self.canvas.delete('svg_element')
        self.render_svg_preview()

    def on_mousewheel(self, event):
        """Handle mouse wheel for zooming"""
        if event.delta > 0 or event.num == 4:
            self.zoom(1.1)
        else:
            self.zoom(0.9)

    def load_window_settings(self):
        """Load window settings from file or use defaults"""
        default_settings = {
            "geometry": "800x600+300+150",
            "zoom": 1.0
        }

        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)

                # Apply saved geometry
                geometry = settings.get("geometry", default_settings["geometry"])
                self.root.geometry(geometry)

                # Apply saved zoom (will be used after SVG loads)
                self.scale_factor = settings.get("zoom", default_settings["zoom"])

                print(f"✅ SVG Viewer: Loaded settings {geometry}, zoom: {self.scale_factor}")
            else:
                # Use defaults for first run
                self.root.geometry(default_settings["geometry"])
                print(f"📋 SVG Viewer: Using default settings {default_settings['geometry']}")

        except Exception as e:
            # Fall back to defaults if error
            self.root.geometry(default_settings["geometry"])
            print(f"⚠️ SVG Viewer: Error loading settings, using defaults: {e}")

    def save_current_position(self):
        """Save current window position and zoom as new defaults"""
        try:
            current_geometry = self.root.geometry()

            settings = {
                "geometry": current_geometry,
                "zoom": self.scale_factor
            }

            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            # Update status bar
            self.status_bar.config(text=f"💾 Position saved: {current_geometry}, zoom: {self.scale_factor:.2f}")

            messagebox.showinfo(
                "Position Saved",
                f"Current window position and zoom saved!\n\n"
                f"Position: {current_geometry}\n"
                f"Zoom: {self.scale_factor:.2f}x\n\n"
                f"This will be used when the SVG viewer opens next time."
            )

        except Exception as e:
            error_msg = f"Error saving position: {e}"
            self.status_bar.config(text=f"❌ {error_msg}")
            messagebox.showerror("Save Error", error_msg)

    def save_settings_on_close(self):
        """Automatically save settings when window is closed"""
        try:
            current_geometry = self.root.geometry()

            settings = {
                "geometry": current_geometry,
                "zoom": self.scale_factor
            }

            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            print(f"💾 SVG Viewer: Auto-saved settings on close: {current_geometry}, zoom: {self.scale_factor}")

        except Exception as e:
            print(f"⚠️ SVG Viewer: Error auto-saving settings: {e}")

    def on_closing(self):
        """Handle window close event"""
        # Auto-save current position when closing
        self.save_settings_on_close()

        # Hide tooltip if open
        self.hide_tooltip()

        # Close the window
        self.root.destroy()

def main():
    """Standalone SVG viewer for testing"""
    app = SVGViewerWindow()
    app.root.mainloop()

if __name__ == "__main__":
    main()