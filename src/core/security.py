from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt  # Меняем passlib на чистый bcrypt
import jwt
from src.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, совпадает ли введенный пароль с хэшем из базы."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Превращает обычный пароль в защищенный хэш."""
    # Генерируем соль и хэшируем пароль в байтах
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    # Возвращаем хэш как обычную строку для сохранения в БД
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Генерирует JWT-токен для авторизации пользователя."""
    to_encode = data.copy()

    # Устанавливаем время жизни токена
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    # Создаем токен, подписывая его нашим секретным ключом
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
