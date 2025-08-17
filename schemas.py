# schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Job status Enum
class StatusEnum(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    SCRAPING = "SCRAPING"
    SYNTHESIZING = "SYNTHESIZING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"

class ErrorType(str, Enum):
    VALIDATION_ERROR = "ValidationError"
    NOT_FOUND = "NotFound"
    INTERNAL_ERROR = "InternalError"

# --- Error Schema ---
# A standardized structure for returning errors to the client.
class ErrorResponse(BaseModel):
    error: ErrorType
    details: Optional[Dict[str, Any]] = None

# --- Request/Response Schemas for Endpoints ---

# The single input model for our main endpoint.
class AnalysisRequest(BaseModel):
    # Field is used to add extra validation, like length constraints.
    research_question: str = Field(..., min_length=10, max_length=500)
    # The '...' indicates that this field is absolutely required.

# The immediate response after a job is accepted (202 Accepted).
class AnalysisResponse(BaseModel):
    analysis_id: str
    status: StatusEnum

# The model for the status polling endpoint.
class StatusResponse(BaseModel):
    status: StatusEnum
    progress: int
    current_step: Optional[str] = None
    error_message: Optional[str] = None

# --- Schemas for the Final Result Payload ---
# Schemas defining the structure of the final analysis report.

class WebAnalysis(BaseModel):
    source: str
    content: str
    timestamp: datetime
    confidence_score: float

class ChatGPTResponse(BaseModel):
    simulated_response: str
    identified_brands: List[str]

class VisualizationData(BaseModel):
    chart_type: str
    data: Dict[str, Any]

# The main model for the final result. This is what will be stored in the
# database's JSON field and returned by the final results endpoint.
class FullAnalysisResult(BaseModel):
    analysis_id: str
    research_question: str
    status: StatusEnum = StatusEnum.COMPLETE
    completed_at: datetime
    web_results: WebAnalysis
    chatgpt_simulation: ChatGPTResponse
    visualization: VisualizationData
