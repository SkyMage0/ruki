from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BidCreate(BaseModel):
    task_id: int
    message: Optional[str] = None
    proposed_amount: Optional[int] = None


class BidRead(BaseModel):
    id: int
    task_id: int
    worker_id: int
    message: Optional[str] = None
    proposed_amount: Optional[int] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
