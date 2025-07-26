import json
import os
from pathlib import Path
from typing import List, Dict, Any
from models.musical_elements import MusicalElement

class FileOrganizer:
    
    def __init__(self, output_base_dir: str):
        self.output_base_dir = Path(output_base_dir)
        self.ensure_base_directory()
    
    def ensure_base_directory(self):
        """Create base output directory, removing any existing content"""
        if self.output_base_dir.exists():
            import shutil
            shutil.rmtree(self.output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
    
    def create_folder_structure(self, instruments: List[str]) -> Dict[str, str]:
        """Create complete folder structure for all output files"""
        
        folders = {}
        
        # Create main organized output structure
        folders["master_files"] = self._create_dir("master_files")
        folders["individual_noteheads"] = self._create_dir("master_files/individual_noteheads")
        folders["instruments"] = self._create_dir("instruments")
        folders["metadata"] = self._create_dir("metadata")
        
        # Per-instrument directories  
        for instrument in instruments:
            instrument_dir = self._create_dir(f"instruments/{instrument}")
            folders[f"instrument_{instrument}"] = instrument_dir
            folders[f"instrument_{instrument}_individual"] = self._create_dir(f"instruments/{instrument}/individual_noteheads")
        
        return folders
    
    def _create_dir(self, relative_path: str) -> str:
        """Create directory and return full path"""
        full_path = self.output_base_dir / relative_path
        full_path.mkdir(parents=True, exist_ok=True)
        return str(full_path)
    
    def get_output_paths(self, instruments: List[str]) -> Dict[str, str]:
        """Generate all output file paths for SVG files"""
        
        paths = {}
        
        # Master SVG files in organized structure
        paths["all_noteheads"] = str(self.output_base_dir / "master_files" / "all_noteheads.svg")
        paths["all_except_noteheads"] = str(self.output_base_dir / "master_files" / "all_except_noteheads.svg")
        
        # Individual noteheads directory
        paths["individual_noteheads_dir"] = str(self.output_base_dir / "master_files" / "individual_noteheads")
        
        # Per-instrument SVG files
        for instrument in instruments:
            instrument_dir = self.output_base_dir / "instruments" / instrument
            paths[f"{instrument}_complete"] = str(instrument_dir / f"{instrument}_complete.svg")
            paths[f"{instrument}_noteheads"] = str(instrument_dir / f"{instrument}_noteheads.svg")
            paths[f"{instrument}_except_noteheads"] = str(instrument_dir / f"{instrument}_except_noteheads.svg")
            paths[f"{instrument}_individual_dir"] = str(instrument_dir / "individual_noteheads")
        
        # Metadata
        paths["coordinate_map"] = str(self.output_base_dir / "metadata" / "coordinate_map.json")
        paths["processing_report"] = str(self.output_base_dir / "metadata" / "processing_report.json")
        
        return paths
    
    def generate_individual_notehead_path(self, instrument: str, notehead_index: int) -> str:
        """Generate path for individual notehead SVG"""
        if instrument == "all":
            dir_path = self.output_base_dir / "master_files" / "individual_noteheads"
        else:
            dir_path = self.output_base_dir / "instruments" / instrument / "individual_noteheads"
        
        return str(dir_path / f"notehead_{notehead_index:03d}.svg")
    
    def generate_metadata_json(self, elements: List[MusicalElement], output_path: str) -> bool:
        """Generate JSON metadata with coordinate mapping"""
        try:
            metadata = {
                "total_elements": len(elements),
                "processing_info": {
                    "coordinate_system": "absolute",
                    "dpi": 300,
                    "precision": 2
                },
                "elements": []
            }
            
            for element in elements:
                element_data = {
                    "id": element.element_id,
                    "type": element.element_type,
                    "instrument": element.instrument,
                    "coordinates": {
                        "x": round(element.transformed_bbox.x, 2),
                        "y": round(element.transformed_bbox.y, 2),
                        "width": round(element.transformed_bbox.width, 2),
                        "height": round(element.transformed_bbox.height, 2)
                    },
                    "center_point": {
                        "x": round(element.transformed_bbox.x + element.transformed_bbox.width / 2, 2),
                        "y": round(element.transformed_bbox.y + element.transformed_bbox.height / 2, 2)
                    },
                    "staff_position": element.staff_position,
                    "transform_matrix": {
                        "a": element.transform_matrix.a,
                        "b": element.transform_matrix.b,
                        "c": element.transform_matrix.c,
                        "d": element.transform_matrix.d,
                        "e": element.transform_matrix.e,
                        "f": element.transform_matrix.f
                    }
                }
                metadata["elements"].append(element_data)
            
            # Group statistics
            metadata["statistics"] = self._generate_statistics(elements)
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error generating metadata JSON: {e}")
            return False
    
    def _generate_statistics(self, elements: List[MusicalElement]) -> Dict[str, Any]:
        """Generate processing statistics"""
        
        stats = {
            "element_counts": {},
            "instrument_counts": {},
            "coordinate_ranges": {
                "x_min": float('inf'), "x_max": float('-inf'),
                "y_min": float('inf'), "y_max": float('-inf')
            }
        }
        
        # Count elements by type
        for element in elements:
            element_type = element.element_type
            instrument = element.instrument or "unknown"
            
            stats["element_counts"][element_type] = stats["element_counts"].get(element_type, 0) + 1
            stats["instrument_counts"][instrument] = stats["instrument_counts"].get(instrument, 0) + 1
            
            # Track coordinate ranges
            bbox = element.transformed_bbox
            stats["coordinate_ranges"]["x_min"] = min(stats["coordinate_ranges"]["x_min"], bbox.x)
            stats["coordinate_ranges"]["x_max"] = max(stats["coordinate_ranges"]["x_max"], bbox.x + bbox.width)
            stats["coordinate_ranges"]["y_min"] = min(stats["coordinate_ranges"]["y_min"], bbox.y)
            stats["coordinate_ranges"]["y_max"] = max(stats["coordinate_ranges"]["y_max"], bbox.y + bbox.height)
        
        return stats
    
    def generate_processing_report(self, result_data: Dict[str, Any], output_path: str) -> bool:
        """Generate comprehensive processing report"""
        try:
            report = {
                "processing_summary": result_data,
                "timestamp": self._get_timestamp(),
                "file_structure": self._document_file_structure(),
                "validation_results": {
                    "coordinate_accuracy": result_data.get("coordinate_accuracy", 0.0),
                    "files_created": result_data.get("output_files_created", 0),
                    "processing_time": result_data.get("processing_time_seconds", 0.0)
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error generating processing report: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for reporting"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _document_file_structure(self) -> Dict[str, List[str]]:
        """Document the created file structure"""
        structure = {}
        
        for root, dirs, files in os.walk(self.output_base_dir):
            relative_root = os.path.relpath(root, self.output_base_dir)
            if relative_root == ".":
                relative_root = "root"
            
            structure[relative_root] = {
                "directories": dirs,
                "files": files
            }
        
        return structure
    
    def validate_output_structure(self, expected_instruments: List[str]) -> Dict[str, bool]:
        """Validate that all expected output files were created"""
        
        validation = {
            "all_noteheads_png": os.path.exists(self.output_base_dir / "master_files" / "all_noteheads.png"),
            "all_except_noteheads_png": os.path.exists(self.output_base_dir / "master_files" / "all_except_noteheads.png"),
            "individual_noteheads_dir": os.path.exists(self.output_base_dir / "master_files" / "individual_noteheads"),
            "metadata_dir": os.path.exists(self.output_base_dir / "metadata"),
            "coordinate_map_json": os.path.exists(self.output_base_dir / "metadata" / "coordinate_map.json")
        }
        
        # Validate per-instrument structure
        for instrument in expected_instruments:
            instrument_dir = self.output_base_dir / "instruments" / instrument
            validation[f"{instrument}_complete_png"] = os.path.exists(instrument_dir / f"{instrument}_complete.png")
            validation[f"{instrument}_noteheads_png"] = os.path.exists(instrument_dir / f"{instrument}_noteheads.png")
            validation[f"{instrument}_except_noteheads_png"] = os.path.exists(instrument_dir / f"{instrument}_except_noteheads.png")
            validation[f"{instrument}_individual_dir"] = os.path.exists(instrument_dir / "individual_noteheads")
        
        return validation
    
    def cleanup_incomplete_files(self):
        """Remove any incomplete or empty output files"""
        for root, dirs, files in os.walk(self.output_base_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if os.path.getsize(file_path) == 0:
                        os.remove(file_path)
                        print(f"Removed empty file: {file_path}")
                except OSError:
                    pass