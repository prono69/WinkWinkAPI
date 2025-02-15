from pydantic import BaseModel
from typing import Dict, Any, Optional

# Constants
CREATOR = "EyePatch"
API_VERSION = "1.3.5"

# ----- Pydantic Models -----
class SuccessResponse(BaseModel):
    creator: str = CREATOR
    status: str = "success"
    api_version: str = API_VERSION
    data: Dict[str, Any]

class ErrorResponse(BaseModel):
    status: str = "error"
    creator: str = CREATOR
    api_version: str = API_VERSION
    error_code: int
    message: str

class ItemPayload(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tags: list[str] = []
