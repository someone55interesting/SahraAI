from pydantic import BaseModel
from typing import Optional

class DocumentAskRequest(BaseModel):
    question: str
    filename: Optional[str] = None  # Теперь можно передать конкретный файл или оставить None для поиска по всем

class DocumentAskResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]
