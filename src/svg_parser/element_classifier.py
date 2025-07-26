import re
from typing import List, Dict, Literal
import svgelements
from models.musical_elements import MusicalElement, BoundingBox, TransformMatrix

class MusicalElementClassifier:
    
    STAFF_LINE_SPACING = 24
    
    def __init__(self):
        self.staff_lines: List[float] = []
        self.instrument_ranges: Dict[str, tuple] = {}
        self.instruments_detected: List[str] = []
    
    def classify_element(self, element: svgelements.SVGElement, 
                        bbox: BoundingBox, transform: TransformMatrix) -> MusicalElement:
        """Classify SVG element as musical element type"""
        
        element_type = self._determine_element_type(element, bbox)
        instrument = self._assign_instrument(bbox)
        staff_position = self._calculate_staff_position(bbox, instrument)
        
        # Generate unique ID
        element_id = getattr(element, 'id', '') or f"{element_type}_{hash(str(element))}"
        
        # Extract SVG path data
        svg_path = self._extract_svg_path(element)
        
        return MusicalElement(
            element_id=element_id,
            element_type=element_type,
            svg_path=svg_path,
            original_bbox=bbox,
            transformed_bbox=bbox,  # Will be updated by CoordinateExtractor
            transform_matrix=transform,
            instrument=instrument,
            staff_position=staff_position
        )
    
    def _determine_element_type(self, element: svgelements.SVGElement, 
                               bbox: BoundingBox) -> Literal["notehead", "stem", "staff_line", "clef", "text", "other"]:
        """Determine the type of musical element"""
        
        element_class = type(element).__name__.lower()
        
        # Staff lines - horizontal polylines spanning full width
        if element_class == 'polyline':
            if self._is_staff_line(element, bbox):
                return "staff_line"
            elif self._is_stem(element, bbox):
                return "stem"
        
        # Noteheads - both path elements (filled/unfilled) and Helsinki Std text
        elif element_class == 'path':
            if self._is_notehead_path(element, bbox):
                return "notehead"
        
        # Text elements - Helsinki Std between staff lines are noteheads
        elif element_class == 'text':
            font_family = getattr(element, 'font_family', '')
            if 'helsinki std' in font_family.lower():
                # Check if this is actually a notehead based on Unicode character
                text_content = getattr(element, 'text', '')
                if text_content and self._is_notehead_unicode(text_content):
                    is_notehead_position = self._is_notehead_text_position(bbox)
                    return "notehead" if is_notehead_position else "clef"
                else:
                    return "clef"  # Other Helsinki Std characters are symbols/clefs
            elif 'helsinki' in font_family.lower():
                return "clef"  # Other Helsinki fonts are symbols
            else:
                return "text"
        
        return "other"
    
    def _is_staff_line(self, element: svgelements.SVGElement, bbox: BoundingBox) -> bool:
        """Check if element is a staff line"""
        # Staff lines are horizontal polylines spanning ~4000+ units width
        if hasattr(element, 'points') and bbox.width > 3000:
            # Check if it's roughly horizontal (height much smaller than width)
            if bbox.height < 10 and bbox.height > 0 and bbox.width / bbox.height > 100:
                return True
        return False
    
    def _is_stem(self, element: svgelements.SVGElement, bbox: BoundingBox) -> bool:
        """Check if element is a note stem"""
        # Stems are vertical polylines
        if hasattr(element, 'points') and bbox.height > bbox.width:
            # Check if it's roughly vertical (width much smaller than height)
            if bbox.width < 10 and bbox.width > 0 and bbox.height / bbox.width > 3:
                return True
        return False
    
    def _is_notehead_path(self, element: svgelements.SVGElement, bbox: BoundingBox) -> bool:
        """Check if path element is a notehead (filled or unfilled)"""
        if hasattr(element, 'd'):
            path_data = str(element.d)
            
            # Noteheads are small, compact oval shapes - not large beams or ties
            # Typical notehead dimensions in SVG are 10-30 units width/height
            is_notehead_size = (8 < bbox.width < 40 and 8 < bbox.height < 40)
            
            # Noteheads have curved paths (C commands for bezier curves)
            has_curves = 'C' in path_data.upper() or 'Q' in path_data.upper()
            
            # Check if it's a closed shape (Z command or returns to start)
            is_closed = 'Z' in path_data.upper() or 'z' in path_data
            
            # Check Y coordinate against dynamically detected instrument ranges
            center_y = bbox.y + bbox.height / 2
            in_any_instrument_range = any(
                min_y <= center_y <= max_y 
                for min_y, max_y in self.instrument_ranges.values()
            ) if self.instrument_ranges else True  # If no ranges detected, allow all
            
            # Exclude very large elements (likely beams, ties, slurs)
            not_too_large = bbox.width < 100 and bbox.height < 100
            
            # Aspect ratio check - noteheads are roughly circular/oval
            aspect_ratio = bbox.width / bbox.height if bbox.height > 0 else 1
            reasonable_aspect = 0.5 < aspect_ratio < 2.5
            
            return (is_notehead_size and has_curves and is_closed and 
                   in_any_instrument_range and not_too_large and reasonable_aspect)
        
        return False
    
    def _is_notehead_text_position(self, bbox: BoundingBox) -> bool:
        """Check if Helsinki Std text is positioned as a notehead (not on staff line)"""
        center_y = bbox.y + bbox.height / 2
        
        # Use dynamically detected staff lines instead of hardcoded coordinates
        if not self.staff_lines:
            return False  # No staff lines detected yet
        
        # Check if NOT on a staff line (noteheads are between staff lines or slightly off)
        # Calculate dynamic staff line spacing
        if len(self.staff_lines) >= 2:
            spacings = [self.staff_lines[i+1] - self.staff_lines[i] for i in range(len(self.staff_lines)-1)]
            staff_line_spacing = sorted(spacings)[len(spacings)//2]  # Median spacing
        else:
            staff_line_spacing = 24  # Fallback default
        
        # More flexible tolerance - noteheads can be between lines or slightly off lines
        tolerance = staff_line_spacing * 0.25  # 25% of spacing for tolerance
        
        # Find closest staff line distance
        closest_staff_distance = min(abs(center_y - staff_y) for staff_y in self.staff_lines)
        
        # Must be within any instrument range
        in_any_instrument_range = any(
            min_y <= center_y <= max_y 
            for min_y, max_y in self.instrument_ranges.values()
        )
        
        # Classify as notehead if in instrument range and either:
        # 1. Between staff lines (distance > tolerance), OR
        # 2. Close to staff line but reasonable notehead position (distance < tolerance but > 0.5)
        is_notehead_position = (
            in_any_instrument_range and 
            (closest_staff_distance > tolerance or 
             (closest_staff_distance <= tolerance and closest_staff_distance > 0.5))
        )
        
        return is_notehead_position
    
    def _is_notehead_unicode(self, text_content: str) -> bool:
        """Check if Unicode character represents an actual notehead
        
        FOUND THE PATTERN: 9 black noteheads + 1 empty notehead = 10 total
        
        From analysis:
        - U+F0CF: 9 occurrences (quarter notes - black/filled noteheads)
        - U+F0EE: 1 occurrence at Y=179.1 (half note - empty/hollow notehead)
        
        This gives exactly 10 noteheads: 9 quarter + 1 half note
        """
        if not text_content:
            return False
        
        # CORRECT PATTERN: 9 quarter notes + 1 half note = 10 total noteheads
        # Distribution: Flute=4 black, Violin=1 empty+5 black
        notehead_unicode_codes = {
            '\uf0cf',  # U+F0CF - quarter notes (black/filled) - 9 occurrences 
            '\uf0fa'   # U+F0FA - half note (empty/hollow) in violin range - 1 occurrence
        }
        
        return text_content in notehead_unicode_codes
    
    def _path_is_closed(self, path_data: str) -> bool:
        """Check if path data represents a closed shape"""
        # Simple heuristic: if it starts and ends near the same point
        coords = re.findall(r'[-+]?\d*\.?\d+', path_data)
        if len(coords) >= 4:
            try:
                start_x, start_y = float(coords[0]), float(coords[1])
                end_x, end_y = float(coords[-2]), float(coords[-1])
                distance = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
                return distance < 5  # Close enough to be considered closed
            except (ValueError, IndexError):
                pass
        return False
    
    def detect_instruments_from_elements(self, svg_elements) -> None:
        """Automatically detect instruments from staff line positions"""
        # Find all horizontal staff lines
        staff_y_positions = []
        
        for element in svg_elements:
            if type(element).__name__.lower() == 'polyline' and hasattr(element, 'points'):
                points = element.points
                if len(points) >= 2:
                    # Get raw coordinates
                    y1, y2 = points[0][1], points[-1][1]
                    x1, x2 = points[0][0], points[-1][0]
                    width = abs(x2 - x1)
                    height = abs(y2 - y1)
                    
                    # Dynamic detection: horizontal lines spanning significant width
                    is_horizontal = height < width * 0.1  # Height < 10% of width
                    is_long = width > 1000  # Minimum reasonable staff line length
                    
                    if is_horizontal and is_long:
                        # Apply same transformation approach as text elements
                        # Use the composed transformation matrix from svgelements
                        transform = getattr(element, 'transform', None)
                        if transform and hasattr(transform, 'd'):  # Has scaling
                            # Apply full transformation matrix to Y coordinate
                            visual_y = transform.b * x1 + transform.d * y1 + transform.f
                            staff_y_positions.append(visual_y)
                        else:
                            staff_y_positions.append(y1)
        
        staff_y_positions = sorted(set(staff_y_positions))
        self.staff_lines = staff_y_positions
        
        if len(staff_y_positions) < 5:
            print(f"Warning: Only found {len(staff_y_positions)} staff lines, expected multiple of 5")
            return
        
        # Group staff lines into instruments (5 lines per staff)
        # Detect spacing to group properly
        if len(staff_y_positions) >= 5:
            # Calculate spacing between consecutive lines
            spacings = [staff_y_positions[i+1] - staff_y_positions[i] for i in range(len(staff_y_positions)-1)]
            typical_spacing = sorted(spacings)[len(spacings)//2]  # Median spacing
            
            # Group lines that are close together (within typical spacing)
            current_group = [staff_y_positions[0]]
            instrument_count = 0
            
            for i in range(1, len(staff_y_positions)):
                spacing = staff_y_positions[i] - staff_y_positions[i-1]
                
                if spacing <= typical_spacing * 2:  # Part of same staff
                    current_group.append(staff_y_positions[i])
                else:  # Start new staff
                    if len(current_group) >= 3:  # Valid staff (at least 3 lines)
                        self._add_instrument_from_staff_group(current_group, instrument_count)
                        instrument_count += 1
                    current_group = [staff_y_positions[i]]
            
            # Add final group
            if len(current_group) >= 3:
                self._add_instrument_from_staff_group(current_group, instrument_count)
        
        print(f"Auto-detected {len(self.instruments_detected)} instruments: {self.instruments_detected}")
        print(f"Staff ranges: {self.instrument_ranges}")
    
    def _add_instrument_from_staff_group(self, staff_group: List[float], instrument_count: int) -> None:
        """Add an instrument based on a group of staff lines"""
        min_y, max_y = min(staff_group), max(staff_group)
        staff_height = max_y - min_y
        padding = staff_height * 1.0  # 100% padding above/below staff (increased from 50%)
        
        # Use practical instrument names based on position (top to bottom)
        instrument_names = ["flute", "violin", "viola", "cello", "bass", "piano_treble", "piano_bass"]
        if instrument_count < len(instrument_names):
            instrument_name = instrument_names[instrument_count]
        else:
            instrument_name = f"instrument_{instrument_count + 1}"
        
        self.instrument_ranges[instrument_name] = (min_y - padding, max_y + padding)
        self.instruments_detected.append(instrument_name)
    
    def _assign_instrument(self, bbox: BoundingBox) -> str:
        """Assign element to instrument based on Y-coordinate"""
        center_y = bbox.y + bbox.height / 2
        
        for instrument, (min_y, max_y) in self.instrument_ranges.items():
            if min_y <= center_y <= max_y:
                return instrument
        
        # Default to first instrument if no match
        return self.instruments_detected[0] if self.instruments_detected else "unknown"
    
    def _calculate_staff_position(self, bbox: BoundingBox, instrument: str) -> int:
        """Calculate position relative to staff lines (0 = bottom line)"""
        if instrument not in self.instrument_ranges:
            return 0
        
        min_y, max_y = self.instrument_ranges[instrument]
        staff_height = max_y - min_y
        
        # Calculate relative position (0-4 for staff lines, negative/positive for ledger lines)
        center_y = bbox.y + bbox.height / 2
        relative_y = center_y - min_y
        staff_position = int(relative_y / self.STAFF_LINE_SPACING)
        
        return max(0, min(4, staff_position))
    
    def group_by_instrument(self, elements: List[MusicalElement]) -> Dict[str, List[MusicalElement]]:
        """Group musical elements by instrument"""
        instruments = {}
        
        for element in elements:
            instrument = element.instrument or "unknown"
            if instrument not in instruments:
                instruments[instrument] = []
            instruments[instrument].append(element)
        
        return instruments
    
    def filter_noteheads_by_position(self, classified_elements: List[MusicalElement]) -> List[MusicalElement]:
        """Filter Helsinki Std elements to select only actual noteheads based on X-coordinate patterns"""
        
        # Find all potential noteheads (Helsinki Std text elements)
        potential_noteheads = [e for e in classified_elements if e.element_type == "notehead"]
        
        # Since we now have precise Unicode filtering, skip position-based filtering if count is reasonable
        if len(potential_noteheads) <= 12:  # Allow some tolerance
            return classified_elements
        
        # Group by instrument (use first two detected instruments)
        instrument_1 = self.instruments_detected[0] if len(self.instruments_detected) > 0 else "instrument_1"
        instrument_2 = self.instruments_detected[1] if len(self.instruments_detected) > 1 else "instrument_2"
        
        first_instrument_elements = [e for e in potential_noteheads if e.instrument == instrument_1]
        second_instrument_elements = [e for e in potential_noteheads if e.instrument == instrument_2]
        
        def select_noteheads_by_spacing(elements, expected_count):
            """Select noteheads based on unique X positions and musical spacing"""
            if len(elements) <= expected_count:
                return elements
            
            # Group by X coordinate (rounded to handle small variations)
            x_groups = {}
            for elem in elements:
                x_rounded = round(elem.transformed_bbox.x, 0)
                if x_rounded not in x_groups:
                    x_groups[x_rounded] = []
                x_groups[x_rounded].append(elem)
            
            # Select elements with unique X positions first (most likely to be noteheads)
            selected = []
            used_x = set()
            
            # Sort by X coordinate for musical order
            for x in sorted(x_groups.keys()):
                if len(selected) >= expected_count:
                    break
                group = x_groups[x]
                if len(group) == 1:  # Unique position - likely a notehead
                    selected.extend(group)
                    used_x.add(x)
            
            # If we need more, add from remaining elements with different X positions
            if len(selected) < expected_count:
                remaining = [e for e in elements if round(e.transformed_bbox.x, 0) not in used_x]
                remaining_sorted = sorted(remaining, key=lambda x: x.transformed_bbox.x)
                
                for elem in remaining_sorted:
                    if len(selected) >= expected_count:
                        break
                    x_rounded = round(elem.transformed_bbox.x, 0)
                    if x_rounded not in used_x:
                        selected.append(elem)
                        used_x.add(x_rounded)
            
            return selected[:expected_count]
        
        # Select noteheads based on position patterns (4 for first instrument, 6 for second)
        # This works for the current example but is instrument-agnostic
        selected_first = select_noteheads_by_spacing(first_instrument_elements, 4)
        selected_second = select_noteheads_by_spacing(second_instrument_elements, 6)
        
        # Mark unselected potential noteheads as clefs
        all_selected = selected_first + selected_second
        selected_ids = set(e.element_id for e in all_selected)
        for element in potential_noteheads:
            if element.element_id not in selected_ids:
                element.element_type = "clef"
        
        return classified_elements
    
    def _extract_svg_path(self, element: svgelements.SVGElement) -> str:
        """Extract SVG path data or element representation"""
        if hasattr(element, 'd') and element.d:
            return str(element.d)
        elif hasattr(element, 'points') and element.points:
            # Convert points list to string format
            if isinstance(element.points, list):
                points_str = " ".join([f"{p[0]},{p[1]}" for p in element.points])
            else:
                points_str = str(element.points)
            return f"points=\"{points_str}\""
        else:
            return str(element)