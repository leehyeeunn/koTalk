from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class WordStamp(BaseModel):
    word: str
    start: float
    end: float

class STTResponse(BaseModel):
    rawText: str
    normText: str
    words: List[WordStamp]
    duration: float
    processing_ms: int
    language: str
    model: str
    version: str

class ErrorBody(BaseModel):
    code: str
    message: str
    hint: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: ErrorBody

class HealthResponse(BaseModel):
    ready: bool
    model: str
    device: str
    version: str
    error: Optional[str] = None
