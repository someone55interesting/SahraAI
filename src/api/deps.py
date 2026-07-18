from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from loguru import logger

from src.core.config import settings
from src.core.exceptions import AppError
from src.db.database import get_db
from src.models.user import User
from src.repositories.user_repo import user_repository

# Говорим FastAPI, где находится эндпоинт для логина
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """
    Проверяет JWT-токен и возвращает текущего пользователя.
    Если токен невалиден или юзера нет — бросает 401 ошибку.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise AppError("Invalid token payload", status_code=status.HTTP_401_UNAUTHORIZED)
            
    except jwt.PyJWTError as e:
        logger.warning(f"Token validation error: {str(e)}")
        raise AppError("Could not validate credentials", status_code=status.HTTP_401_UNAUTHORIZED)
    
    user = await user_repository.get_by_email(db, email=email)
    if user is None:
        raise AppError("User not found", status_code=status.HTTP_404_NOT_FOUND)
        
    return user
