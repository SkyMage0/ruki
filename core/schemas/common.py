from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CityRead(BaseModel):
    id: int
    name: str
    timezone: str
    is_active: bool

    class Config:
        from_attributes = True


class UserBrief(BaseModel):
    id: int
    full_name: Optional[str] = None
    rating: float
    is_verified: bool
    completed_tasks_count: int

    class Config:
        from_attributes = True
