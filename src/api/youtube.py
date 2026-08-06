import httpx
import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.youtube import YouTubeSummaryRequest, YouTubeSummaryResponse
from src.services.youtube import youtube_service
from src.api.deps import get_current_user
from src.models.user import User
from src.core.exceptions import AppError
from loguru import logger

from src.core.config import settings

router = APIRouter(prefix="/youtube", tags=["YouTube AI"])

OLLAMA_GENERATE_URL = f"{settings.OLLAMA_URL}/api/generate"
CHUNK_SIZE = 12000 # Безопасный размер для контекстного окна Llama 3.1 8B

async def ask_ollama(prompt: str, timeout: float = 120.0) -> str:
    """Вспомогательная функция для запросов к локальной нейросети"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                OLLAMA_GENERATE_URL, 
                json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=timeout
            )
            
            if resp.status_code != 200:
                raise AppError(f"AI generation failed: {resp.text}", status_code=500)
                
            return resp.json().get("response", "")
            
    except httpx.ReadTimeout:
        logger.error("Ollama думала слишком долго (таймаут)")
        raise AppError("Timeout: AI took too long to generate", status_code=504)
    except Exception as e:
        logger.error(f"Ошибка при обращении к Ollama: {e}")
        raise AppError("Failed to communicate with AI", status_code=500)


@router.post("/summary", response_model=YouTubeSummaryResponse)
async def summarize_video(request: YouTubeSummaryRequest, current_user: User = Depends(get_current_user)):
    logger.info(f"Юзер {current_user.email} запросил конспект для: {request.url}")
    
    # 1. Извлекаем ID и текст из видео
    video_id = youtube_service.extract_video_id(request.url)
    transcript = youtube_service.get_transcript(video_id)
    
    text_length = len(transcript)
    logger.info(f"Длина текста: {text_length} символов")
    
    # 2. Логика Map-Reduce (Чанкинг)
    if text_length <= CHUNK_SIZE:
        # Если текст короткий — обрабатываем за один проход
        logger.info("Текст короткий, обрабатываем целиком...")
        prompt = (
            "Сделай подробный, структурированный и понятный конспект следующего текста из видео. "
            "Выдели главные мысли, добавь маркированные списки и ключевые инсайты. "
            "Отвечай строго на русском языке, без лишних вступлений.\n\n"
            f"Текст: {transcript}"
        )
        final_summary = await ask_ollama(prompt)
        
    else:
        # Текст длинный — разбиваем на куски
        chunks = [transcript[i:i + CHUNK_SIZE] for i in range(0, text_length, CHUNK_SIZE)]
        logger.info(f"Текст слишком длинный. Разбиваем на {len(chunks)} частей (Map-Reduce)...")
        
        chunk_summaries = []
        
        # ВАЖНО: Обрабатываем куски строго последовательно
        for i, chunk in enumerate(chunks):
            logger.info(f"Обработка части {i + 1} из {len(chunks)}...")
            chunk_prompt = (
                "Сделай краткую выжимку главных мыслей из этой части текста видео. "
                "Пиши только факты и суть, на русском языке.\n\n"
                f"Текст: {chunk}"
            )
            # Даем модели больше времени на каждый кусок
            chunk_summary = await ask_ollama(chunk_prompt, timeout=180.0)
            chunk_summaries.append(f"--- Часть {i+1} ---\n{chunk_summary}")
            
        # Склеиваем промежуточные результаты
        combined_summaries = "\n\n".join(chunk_summaries)
        logger.info("Все части обработаны. Генерируем финальный конспект (Reduce)...")
        
        # Финальная сборка
        final_prompt = (
            "Ниже представлены краткие выжимки из разных частей одного длинного видео. "
            "Твоя задача — объединить их в один цельный, подробный, красивый и структурированный конспект. "
            "Используй заголовки, маркированные списки и выдели ключевые инсайты всего видео. "
            "Отвечай строго на русском языке.\n\n"
            f"Выжимки:\n{combined_summaries}"
        )
        # На финальную сборку даем 4 минуты таймаута
        final_summary = await ask_ollama(final_prompt, timeout=240.0)
        
    logger.success(f"Конспект для {video_id} успешно сгенерирован!")
    
    return YouTubeSummaryResponse(video_id=video_id, summary=final_summary)