from pydantic import BaseModel
from typing import Optional, Dict, Any

class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int
    path: Optional[str] = None
    timestamp: Optional[str] = None
    request_id: Optional[str] = None

class ValidationErrorDetail(BaseModel):
    loc: list
    msg: str
    type: str

class ValidationErrorResponse(BaseModel):
    error: str = "Validation Error"
    detail: str
    status_code: int = 422
    errors: list[ValidationErrorDetail]
