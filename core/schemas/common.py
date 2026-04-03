from pydantic import BaseModel


class CityRead(BaseModel):
    id: int
    name: str
    timezone: str
    is_active: bool

    class Config:
        from_attributes = True


class UserBrief(BaseModel):
    id: int
    full_name: str | None = None
    rating: float
    is_verified: bool
    completed_tasks_count: int

    class Config:
        from_attributes = True
