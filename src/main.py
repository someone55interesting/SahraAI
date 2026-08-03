from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as redis

from src.core.exceptions import AppError, app_error_handler
from src.core.config import settings
from src.api import auth, chat, memory, youtube, search, documents, tasks
from loguru import logger
from arq import create_pool
from arq.connections import RedisSettings

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Подключение к Redis и ARQ...")
    app.state.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    
    # Пул соединений для отправки задач в очередь
    app.state.arq_pool = await create_pool(RedisSettings(host="localhost", port=6379))
    logger.success("Redis и ARQ успешно подключены!")
    
    yield
    
    logger.info("Отключение от Redis и ARQ...")
    await app.state.redis.close()
    await app.state.arq_pool.close()

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
app.include_router(tasks.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
