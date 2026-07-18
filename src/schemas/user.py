from pydantic import BaseModel, EmailStr
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
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        # Позволяет Pydantic читать данные напрямую из моделей SQLAlchemy
        from_attributes = True

class Token(BaseModel):
    """Схема для выдачи токена при входе."""
    access_token: str
    token_type: str
