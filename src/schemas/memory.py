from pydantic import BaseModel
from datetime import datetime

class MemoryCreate(BaseModel):
    fact: str

class MemoryResponse(MemoryCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
