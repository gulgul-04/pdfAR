from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Base Components
class Coordinates(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float

class AnnotationMetadata(BaseModel):
    author: str = "Unknown"
    creation_date: str = ""
    modification_date: str = ""

# Pipeline State Models
class ExtractedAnnotation(BaseModel):
    id: str
    parent_id: Optional[str] = None
    type: str
    page: int
    strategy: str
    coordinates: Coordinates
    metadata: AnnotationMetadata
    anchor_text: str
    comment_text: str
    context_window: str

class MatchedAnnotation(BaseModel):
    original_id: str
    parent_id: Optional[str] = None
    type: str
    confidence_score: float = Field(..., ge=0.0, le=100.0)
    match_reason: str
    anchor_text: str
    context_window: str

    new_page: Optional[int] = None
    new_coordinates: Optional[Coordinates] = None

    metadata: AnnotationMetadata
    comment_text: str

# API Request / Response Models (FastAPI Boundaries)
class ProcessPDFResponse(BaseModel):
    # Final JSON payload sent back to the React UI
    status: str
    message: str
    total_annotations_found: int
    successful_matches: int
    needs_review: int 

    auto_injected: List[MatchedAnnotation]
    review_queue: List[MatchedAnnotation]

    download_token: Optional[str] = None 

class ManualInjectionRequest(BaseModel):
    job_id: str
    page_number: int
    rect: Dict[str, float]  
    comment_text: str
    author: Optional[str] = "Manual Reviewer"
    annot_type: Optional[str] = "Highlight"