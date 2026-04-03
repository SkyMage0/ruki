from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaskCreate(BaseModel):
    title: str
    description: str
    category: str
    city_id: int
    address_text: str
    payment_type: str
    payment_amount: int


class TaskRead(BaseModel):
    id: int
    customer_id: int
    title: str
    description: str
    category: str
    city_id: int
    address_text: str
    payment_type: str
    payment_amount: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskList(BaseModel):
    id: int
    title: str
    category: str
    payment_type: str
    payment_amount: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
