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


from fastapi import Request
from src.core.exceptions import AppError
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

class RateLimiter:
    """
    Кастомный Rate Limiter.
    Если Redis недоступен, пропускает запрос, чтобы не блокировать работу всего API.
    """
    def __init__(self, times: int, seconds: int):
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request, current_user: User = Depends(get_current_user)):
        redis_client = request.app.state.redis
        key = f"rate_limit:{current_user.id}:{request.url.path}"
        
        try:
            current_requests = await redis_client.incr(key)
            if current_requests == 1:
                await redis_client.expire(key, self.seconds)
                
            if current_requests > self.times:
                logger.warning(f"Юзер {current_user.email} превысил лимит запросов на {request.url.path}")
                raise AppError("Слишком много запросов. Подождите немного.", status_code=429)
                
        except AppError:
            raise  # Если это 429 ошибка, прокидываем её дальше
        except Exception as e:
            # Если упал сам Redis, логируем, но пускаем юзера, чтобы приложение жило
            logger.error(f"Ошибка Rate Limiter (Redis недоступен): {e}")
