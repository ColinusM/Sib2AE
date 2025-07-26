import pytest
import os
from pathlib import Path

from src.svg_parser.core_parser import SVGParser
from src.svg_parser.element_classifier import MusicalElementClassifier
from src.svg_parser.coordinate_extractor import CoordinateExtractor
from src.models.musical_elements import BoundingBox, TransformMatrix

# Test data paths
TEST_SVG_PATH = "Base/Saint-Saens Trio No 2_0001.svg"

class TestSVGParser:
    
    def setup_method(self):
        """Setup test environment"""
        self.parser = SVGParser()
        
    def test_svg_parsing_basic(self):
        """Test basic SVG file parsing"""
        if not os.path.exists(TEST_SVG_PATH):
            pytest.skip(f"Test SVG file not found: {TEST_SVG_PATH}")
        
        result = self.parser.parse_svg(TEST_SVG_PATH)
        assert result is not None
        
        elements = self.parser.extract_elements(result)
        assert len(elements) > 0
        print(f"Found {len(elements)} elements in SVG")
    
    def test_svg_parsing_file_not_found(self):
        """Test SVG parsing with non-existent file"""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_svg("nonexistent_file.svg")
    
    def test_coordinate_system_extraction(self):
        """Test coordinate system information extraction"""
        if not os.path.exists(TEST_SVG_PATH):
            pytest.skip(f"Test SVG file not found: {TEST_SVG_PATH}")
        
        svg_data = self.parser.parse_svg(TEST_SVG_PATH)
        coord_system = self.parser.coordinate_system
        
        assert coord_system is not None
        assert coord_system.viewbox_width > 0
        assert coord_system.viewbox_height > 0
        print(f"ViewBox: {coord_system.viewbox_width} x {coord_system.viewbox_height}")

class TestMusicalElementClassifier:
    
    def setup_method(self):
        """Setup test environment"""
        self.classifier = MusicalElementClassifier()
        self.parser = SVGParser()
    
    def test_element_classification_basic(self):
        """Test basic element classification"""
        if not os.path.exists(TEST_SVG_PATH):
            pytest.skip(f"Test SVG file not found: {TEST_SVG_PATH}")
        
        svg_data = self.parser.parse_svg(TEST_SVG_PATH)
        elements = self.parser.extract_elements(svg_data)
        
        classified_elements = []
        for svg_element in elements[:10]:  # Test first 10 elements
            bbox = self.parser.extract_bounding_box(svg_element)
            transform = self.parser.extract_transform_matrix(svg_element)
            musical_element = self.classifier.classify_element(svg_element, bbox, transform)
            classified_elements.append(musical_element)
        
        assert len(classified_elements) > 0
        
        # Check that elements have been classified
        element_types = [e.element_type for e in classified_elements]
        assert len(set(element_types)) > 0  # At least one type
        print(f"Element types found: {set(element_types)}")
    
    def test_notehead_identification(self):
        """Test notehead identification accuracy"""
        if not os.path.exists(TEST_SVG_PATH):
            pytest.skip(f"Test SVG file not found: {TEST_SVG_PATH}")
        
        svg_data = self.parser.parse_svg(TEST_SVG_PATH)
        elements = self.parser.extract_elements(svg_data)
        
        noteheads = []
        for svg_element in elements:
            bbox = self.parser.extract_bounding_box(svg_element)
            transform = self.parser.extract_transform_matrix(svg_element)
            musical_element = self.classifier.classify_element(svg_element, bbox, transform)
            
            if musical_element.element_type == "notehead":
                noteheads.append(musical_element)
        
        # Should find some noteheads in a musical score
        assert len(noteheads) >= 5, f"Expected at least 5 noteheads, found {len(noteheads)}"
        print(f"Found {len(noteheads)} noteheads")
    
    def test_instrument_assignment(self):
        """Test instrument assignment based on Y-coordinates"""
        # Test with known coordinates from the SVG analysis
        flute_bbox = BoundingBox(x=100, y=1000, width=20, height=15)  # Flute range
        violin_bbox = BoundingBox(x=100, y=1300, width=20, height=15)  # Violin range
        
        flute_instrument = self.classifier._assign_instrument(flute_bbox)
        violin_instrument = self.classifier._assign_instrument(violin_bbox)
        
        assert flute_instrument == "flute"
        assert violin_instrument == "violin"

class TestCoordinateExtractor:
    
    def setup_method(self):
        """Setup test environment"""
        self.extractor = CoordinateExtractor()
    
    def test_transform_matrix_application(self):
        """Test transformation matrix application"""
        # Identity transform should not change coordinates
        bbox = BoundingBox(x=10, y=20, width=30, height=40)
        identity_transform = TransformMatrix(a=1, b=0, c=0, d=1, e=0, f=0)
        
        result = self.extractor._apply_transform_to_bbox(bbox, identity_transform)
        
        assert abs(result.x - bbox.x) < 0.01
        assert abs(result.y - bbox.y) < 0.01
        assert abs(result.width - bbox.width) < 0.01
        assert abs(result.height - bbox.height) < 0.01
    
    def test_coordinate_translation(self):
        """Test coordinate translation transformation"""
        bbox = BoundingBox(x=0, y=0, width=10, height=10)
        translate_transform = TransformMatrix(a=1, b=0, c=0, d=1, e=50, f=30)  # Translate by (50, 30)
        
        result = self.extractor._apply_transform_to_bbox(bbox, translate_transform)
        
        assert abs(result.x - 50) < 0.01
        assert abs(result.y - 30) < 0.01
        assert abs(result.width - 10) < 0.01
        assert abs(result.height - 10) < 0.01
    
    def test_coordinate_scaling(self):
        """Test coordinate scaling transformation"""
        bbox = BoundingBox(x=10, y=20, width=30, height=40)
        scale_transform = TransformMatrix(a=2, b=0, c=0, d=0.5, e=0, f=0)  # Scale x by 2, y by 0.5
        
        result = self.extractor._apply_transform_to_bbox(bbox, scale_transform)
        
        # Check that scaling is applied correctly
        assert abs(result.width - 60) < 0.01  # 30 * 2
        assert abs(result.height - 20) < 0.01  # 40 * 0.5
    
    def test_coordinate_precision(self):
        """Test coordinate precision and quantization"""
        bbox = BoundingBox(x=10.123456, y=20.987654, width=30.555555, height=40.444444)
        identity_transform = TransformMatrix(a=1, b=0, c=0, d=1, e=0, f=0)
        
        result = self.extractor._apply_transform_to_bbox(bbox, identity_transform)
        quantized = self.extractor._quantize_bbox(result)
        
        # Should be rounded to 2 decimal places
        assert quantized.x == 10.12
        assert quantized.y == 20.99
        assert quantized.width == 30.56
        assert quantized.height == 40.44

class TestIntegration:
    
    def test_full_processing_pipeline(self):
        """Test the complete processing pipeline with a small subset"""
        if not os.path.exists(TEST_SVG_PATH):
            pytest.skip(f"Test SVG file not found: {TEST_SVG_PATH}")
        
        # Parse SVG
        parser = SVGParser()
        svg_data = parser.parse_svg(TEST_SVG_PATH)
        elements = parser.extract_elements(svg_data)
        
        # Classify elements (test first 20 for speed)
        classifier = MusicalElementClassifier()
        classified_elements = []
        
        for svg_element in elements[:20]:
            bbox = parser.extract_bounding_box(svg_element)
            transform = parser.extract_transform_matrix(svg_element)
            musical_element = classifier.classify_element(svg_element, bbox, transform)
            classified_elements.append(musical_element)
        
        # Extract coordinates
        coord_extractor = CoordinateExtractor()
        for i, (element, svg_element) in enumerate(zip(classified_elements, elements[:20])):
            element.transformed_bbox = coord_extractor.extract_coordinates(element, svg_element)
        
        # Validate results
        assert len(classified_elements) == 20
        
        # Check that coordinate extraction worked
        for element in classified_elements:
            assert element.transformed_bbox.width >= 0
            assert element.transformed_bbox.height >= 0
        
        print(f"Successfully processed {len(classified_elements)} elements")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])