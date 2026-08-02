from pydantic import BaseModel

class DocumentAskRequest(BaseModel):
    question: str

class DocumentAskResponse(BaseModel):
    question: str
    answer: str
    sources: list[str] # Названия файлов, откуда ИИ взял информацию
