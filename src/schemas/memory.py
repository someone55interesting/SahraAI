from pydantic import BaseModel, ConfigDict
from datetime import datetime

class MemoryCreate(BaseModel):
    fact: str

class MemoryResponse(MemoryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
