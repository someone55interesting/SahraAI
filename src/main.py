from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as redis

from src.core.exceptions import AppError, app_error_handler
from src.core.config import settings
from src.api import auth, chat, memory, youtube, search, documents
from loguru import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Подключение к Redis...")
    # Сохраняем подключение глобально в app.state
    app.state.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    logger.success("Redis успешно подключен!")
    
    yield
    
    logger.info("Отключение от Redis...")
    await app.state.redis.close()

app = FastAPI(
    title="Sahra AI API",
    lifespan=lifespan
)


# Подключаем глобальные обработчики исключений и роутеры
app.add_exception_handler(AppError, app_error_handler)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(memory.router)
app.include_router(youtube.router)
app.include_router(search.router)
app.include_router(documents.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
