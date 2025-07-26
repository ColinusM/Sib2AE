from pydantic import BaseModel
from typing import List, Optional, Literal

class Coordinate(BaseModel):
    x: float
    y: float

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class TransformMatrix(BaseModel):
    a: float  # x-scale
    b: float  # y-skew
    c: float  # x-skew
    d: float  # y-scale
    e: float  # x-translate
    f: float  # y-translate

class MusicalElement(BaseModel):
    element_id: str
    element_type: Literal["notehead", "stem", "staff_line", "clef", "text", "other"]
    svg_path: str
    original_bbox: BoundingBox
    transformed_bbox: BoundingBox
    transform_matrix: TransformMatrix
    instrument: Optional[str] = None
    staff_position: Optional[int] = None

class InstrumentGroup(BaseModel):
    name: str
    elements: List[MusicalElement]
    staff_lines: List[MusicalElement]
    noteheads: List[MusicalElement]