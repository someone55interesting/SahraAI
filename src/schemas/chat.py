from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class MessageResponse(BaseModel):
    """Схема отдельного сообщения (отправляем клиенту)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime

class ConversationResponse(BaseModel):
    """Схема диалога (для списка диалогов в сайдбаре)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    created_at: datetime

class ConversationDetail(ConversationResponse):
    """Схема диалога вместе со всеми его сообщениями (когда открываем чат)."""
    messages: List[MessageResponse] = []
