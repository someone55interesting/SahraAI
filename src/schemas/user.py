from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Схема для регистрации нового пользователя."""
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserResponse(BaseModel):
    """Схема для отправки данных пользователя обратно клиенту (без пароля)."""
    # Новая конфигурация Pydantic v2 для работы с моделями SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    """Схема для выдачи токена при входе."""
    access_token: str
    token_type: str
