#!/usr/bin/env python3

import click
import time
import os
import sys
from pathlib import Path
from typing import List, Dict

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from svg_parser.core_parser import SVGParser
from svg_parser.element_classifier import MusicalElementClassifier
from svg_parser.coordinate_extractor import CoordinateExtractor
from svg_parser.svg_generator import SVGGenerator
from utils.file_organizer import FileOrganizer
from models.coordinate_system import ProcessingResult
from models.musical_elements import MusicalElement

@click.command()
@click.option('--input', '-i', 'input_file', required=True, 
              help='Path to Sibelius SVG file to process')
@click.option('--output', '-o', 'output_dir', required=True,
              help='Output directory for generated PNG files')
@click.option('--dpi', default=300, help='DPI for PNG output (default: 300)')
@click.option('--instruments', help='Comma-separated list of expected instruments')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def process_sibelius_svg(input_file: str, output_dir: str, dpi: int, 
                        instruments: str, verbose: bool):
    """Process Sibelius SVG file and generate organized PNG assets for After Effects."""
    
    start_time = time.time()
    
    if verbose:
        click.echo(f"Starting SVG processing: {input_file}")
        click.echo(f"Output directory: {output_dir}")
        click.echo(f"DPI: {dpi}")
    
    try:
        # Validate input file
        if not os.path.exists(input_file):
            raise click.ClickException(f"Input file not found: {input_file}")
        
        # STEP 1: Parse SVG and extract all elements
        if verbose:
            click.echo("Step 1: Parsing SVG file...")
        
        parser = SVGParser()
        svg_data = parser.parse_svg(input_file)
        all_svg_elements = parser.extract_elements(svg_data)
        
        if verbose:
            click.echo(f"Found {len(all_svg_elements)} SVG elements")
        
        # STEP 2: Auto-detect instruments and classify musical elements
        if verbose:
            click.echo("Step 2: Auto-detecting instruments and classifying elements...")
        
        classifier = MusicalElementClassifier()
        
        # Auto-detect instruments from staff lines
        classifier.detect_instruments_from_elements(all_svg_elements)
        
        classified_elements = []
        for svg_element in all_svg_elements:
            # Extract basic properties
            bbox = parser.extract_bounding_box(svg_element)
            transform = parser.extract_transform_matrix(svg_element)
            
            # Classify the element
            musical_element = classifier.classify_element(svg_element, bbox, transform)
            classified_elements.append(musical_element)
        
        if verbose:
            element_counts = {}
            for elem in classified_elements:
                element_counts[elem.element_type] = element_counts.get(elem.element_type, 0) + 1
            click.echo(f"Element classification: {element_counts}")
        
        # STEP 3: Extract and preserve coordinates
        if verbose:
            click.echo("Step 3: Extracting coordinates...")
        
        coord_extractor = CoordinateExtractor()
        for i, (element, svg_element) in enumerate(zip(classified_elements, all_svg_elements)):
            element.transformed_bbox = coord_extractor.extract_coordinates(element, svg_element)
        
        # STEP 3.5: Filter noteheads based on position patterns
        if verbose:
            click.echo("Step 3.5: Filtering noteheads by position patterns...")
        
        classified_elements = classifier.filter_noteheads_by_position(classified_elements)
        
        # STEP 4: Group by instruments  
        if verbose:
            click.echo("Step 4: Grouping by instruments...")
        
        instrument_groups = classifier.group_by_instrument(classified_elements)
        detected_instruments = classifier.instruments_detected
        
        if verbose:
            for instrument, elements in instrument_groups.items():
                click.echo(f"  {instrument}: {len(elements)} elements")
        
        # STEP 5: Setup file organization
        if verbose:
            click.echo("Step 5: Setting up output structure...")
        
        organizer = FileOrganizer(output_dir)
        folders = organizer.create_folder_structure(detected_instruments)
        output_paths = organizer.get_output_paths(detected_instruments)
        
        # STEP 6: Generate SVG outputs
        if verbose:
            click.echo("Step 6: Generating SVG files...")
        
        svg_generator = SVGGenerator()
        files_created = 0
        
        # Generate master files
        noteheads = [e for e in classified_elements if e.element_type == "notehead"]
        others = [e for e in classified_elements if e.element_type != "notehead"]
        
        if verbose:
            click.echo(f"  Generating master files ({len(noteheads)} noteheads, {len(others)} other elements)...")
        
        if svg_generator.generate_filtered_svg(noteheads, output_paths["all_noteheads"], input_file):
            files_created += 1
        
        if svg_generator.generate_filtered_svg(others, output_paths["all_except_noteheads"], input_file):
            files_created += 1
        
        # Generate individual notehead files
        if verbose:
            click.echo(f"  Generating {len(noteheads)} individual notehead files...")
        
        for i, notehead in enumerate(noteheads):
            individual_path = organizer.generate_individual_notehead_path("all", i)
            if svg_generator.generate_individual_element_svg(notehead, individual_path, input_file):
                files_created += 1
        
        # Generate per-instrument files
        for instrument_name, instrument_elements in instrument_groups.items():
            if verbose:
                click.echo(f"  Generating files for {instrument_name}...")
            
            # Complete instrument
            if svg_generator.generate_filtered_svg(
                instrument_elements, output_paths[f"{instrument_name}_complete"], input_file):
                files_created += 1
            
            # Instrument noteheads only
            instrument_noteheads = [e for e in instrument_elements if e.element_type == "notehead"]
            if svg_generator.generate_filtered_svg(
                instrument_noteheads, output_paths[f"{instrument_name}_noteheads"], input_file):
                files_created += 1
            
            # Instrument without noteheads
            instrument_others = [e for e in instrument_elements if e.element_type != "notehead"]
            if svg_generator.generate_filtered_svg(
                instrument_others, output_paths[f"{instrument_name}_except_noteheads"], input_file):
                files_created += 1
            
            # Individual noteheads per instrument
            for i, notehead in enumerate(instrument_noteheads):
                individual_path = organizer.generate_individual_notehead_path(instrument_name, i)
                if svg_generator.generate_individual_element_svg(notehead, individual_path, input_file):
                    files_created += 1
        
        # STEP 7: Generate metadata
        if verbose:
            click.echo("Step 7: Generating metadata...")
        
        coordinate_map_path = str(organizer.output_base_dir / "metadata" / "coordinate_map.json")
        organizer.generate_metadata_json(classified_elements, coordinate_map_path)
        
        # Calculate processing results
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Validate coordinate accuracy
        coordinate_accuracy = coord_extractor.validate_coordinate_precision(classified_elements)
        max_deviation = max([coord_extractor.calculate_coordinate_accuracy(e.original_bbox, e.transformed_bbox) 
                            for e in classified_elements]) if classified_elements else 0.0
        
        result = ProcessingResult(
            success=True,
            elements_processed=len(classified_elements),
            noteheads_found=len(noteheads),
            instruments_identified=len(detected_instruments),
            output_files_created=files_created,
            processing_time_seconds=processing_time,
            coordinate_accuracy=max_deviation
        )
        
        # Generate processing report
        processing_report_path = str(organizer.output_base_dir / "metadata" / "processing_report.json")
        organizer.generate_processing_report(result.dict(), processing_report_path)
        
        # Display results
        click.echo("\n" + "="*50)
        click.echo("PROCESSING COMPLETE")
        click.echo("="*50)
        click.echo(f"✓ Elements processed: {result.elements_processed}")
        click.echo(f"✓ Noteheads found: {result.noteheads_found}")
        click.echo(f"✓ Instruments identified: {result.instruments_identified} ({', '.join(detected_instruments)})")
        click.echo(f"✓ SVG files created: {result.output_files_created}")
        click.echo(f"✓ Processing time: {result.processing_time_seconds:.2f} seconds")
        click.echo(f"✓ Coordinate accuracy: ±{result.coordinate_accuracy:.2f} pixels")
        
        # Check validation criteria
        if result.processing_time_seconds > 60:
            click.echo(f"⚠ Warning: Processing time exceeded 60 seconds")
        if result.coordinate_accuracy > 1.0:
            click.echo(f"⚠ Warning: Coordinate accuracy exceeds ±1 pixel tolerance")
        
        click.echo("✓ SVG generation and coordinate detection complete")
        
        click.echo(f"\nOutput available in: {output_dir}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.ClickException(f"Processing failed: {e}")

if __name__ == '__main__':
    process_sibelius_svg()