from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MessageResponse(BaseModel):
    """Схема отдельного сообщения (отправляем клиенту)."""
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    """Схема диалога (для списка диалогов в сайдбаре)."""
    id: int
    title: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationDetail(ConversationResponse):
    """Схема диалога вместе со всеми его сообщениями (когда открываем чат)."""
    messages: List[MessageResponse] = []
