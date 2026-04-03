from datetime import datetime

from pydantic import BaseModel


class BidCreate(BaseModel):
    task_id: int
    message: str | None = None
    proposed_amount: int | None = None


class BidRead(BaseModel):
    id: int
    task_id: int
    worker_id: int
    message: str | None = None
    proposed_amount: int | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
