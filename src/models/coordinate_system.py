from pydantic import BaseModel

class CoordinateSystem(BaseModel):
    viewbox_x: float
    viewbox_y: float
    viewbox_width: float
    viewbox_height: float
    document_width: float
    document_height: float
    dpi: float = 300.0

class ProcessingResult(BaseModel):
    success: bool
    elements_processed: int
    noteheads_found: int
    instruments_identified: int
    output_files_created: int
    processing_time_seconds: float
    coordinate_accuracy: float = 0.0