import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.search import WebSearchRequest, WebSearchResponse
from src.services.search import web_search
from src.api.deps import get_current_user
from src.models.user import User
from src.core.exceptions import AppError
from loguru import logger

router = APIRouter(prefix="/search", tags=["Internet AI"])

OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1"

@router.post("/", response_model=WebSearchResponse)
async def web_search_ai(request: WebSearchRequest, current_user: User = Depends(get_current_user)):
    logger.info(f"Юзер {current_user.email} ищет в интернете: {request.query}")
    
    # 1. Получаем свежие данные из сети
    search_context = await web_search.search(request.query, max_results=4)
    
    # 2. Формируем жесткий промпт (защита от галлюцинаций)
    prompt = (
        "Ты — Sahra AI, умный ассистент. Ответь на вопрос пользователя, используя ТОЛЬКО предоставленную ниже информацию из интернета. "
        "Не придумывай факты. Если в этой информации нет ответа на вопрос, честно скажи: 'Я не нашла ответ в интернете'. "
        "Сформулируй ответ грамотно, структурированно (используй списки и абзацы), на русском языке.\n\n"
        f"Вопрос пользователя: {request.query}\n\n"
        f"Данные из интернета:\n{search_context}"
    )
    
    # 3. Отправляем в Ollama на обработку
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                OLLAMA_GENERATE_URL, 
                json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
                timeout=60.0 
            )
            
            if resp.status_code != 200:
                raise AppError("AI generation failed", status_code=500)
                
            answer = resp.json().get("response", "")
            logger.success("Ответ на основе интернет-данных успешно сгенерирован!")
            
            return WebSearchResponse(
                query=request.query, 
                answer=answer, 
                sources=search_context
            )
            
    except Exception as e:
        logger.error(f"Ошибка при обращении к Ollama: {e}")
        raise AppError("Failed to generate web answer", status_code=500)
