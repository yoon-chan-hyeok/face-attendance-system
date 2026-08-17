from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class AttendanceResponse(BaseModel):
    success: bool
    message: str
    action_type: Literal["IN", "OUT"]
    employee_id: str
    employee_name: str
    action_at: datetime
    
    class Config:
        from_attributes = True

class AttendanceHistoryResponse(BaseModel):
    id: int
    employee_id: str
    employee_name: str
    action_type: Literal["IN", "OUT"]
    action_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

