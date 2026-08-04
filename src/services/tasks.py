import asyncio
from arq.connections import RedisSettings
from src.core.config import settings
from loguru import logger

async def process_heavy_ai_task(ctx, task_name: str, user_id: int):
    """
    Пример фоновой задачи (например, транскрибация длинного видео или парсинг 500 страниц PDF).
    """
    logger.info(f"[Worker] Начинаем фоновую задачу '{task_name}' для юзера {user_id}...")
    
    # Имитация тяжелой работы на 10 секунд (в реальности тут работа с YouTube/Ollama)
    await asyncio.sleep(10)
    
    logger.success(f"[Worker] Задача '{task_name}' для юзера {user_id} успешно завершена!")
    return f"Результат для задачи '{task_name}' успешно сгенерирован!"


# Класс конфигурации для запуска воркера ARQ
class WorkerSettings:
    functions = [process_heavy_ai_task]
    # Используем наш хост и порт из конфигов
    redis_settings = RedisSettings(host="redis", port=6379)
