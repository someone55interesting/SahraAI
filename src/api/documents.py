import httpx
from fastapi import APIRouter, UploadFile, File, Depends
from src.services.document_parser import document_parser
from src.services.vector_db import vector_db
from src.api.deps import get_current_user
from src.models.user import User
from src.core.exceptions import AppError
from src.schemas.documents import DocumentAskRequest, DocumentAskResponse
from loguru import logger
from src.api.deps import RateLimiter
from src.core.config import settings

router = APIRouter(prefix="/documents", tags=["Documents AI"])

# Добавил .rstrip('/') чтобы избежать ошибки с двойным слэшем
OLLAMA_GENERATE_URL = f"{settings.OLLAMA_URL.rstrip('/')}/api/generate"

@router.post("/upload", dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Юзер {current_user.email} загружает документ {file.filename}")
    
    # 1. Извлекаем текст
    text = await document_parser.parse(file)
    text_length = len(text)
    
    # 2. Сохраняем в векторную базу
    vector_db.add_document(
        user_id=current_user.id, 
        filename=file.filename, 
        text=text
    )
    
    return {
        "message": "Документ успешно загружен и обработан нейросетью.",
        "filename": file.filename,
        "content_length": text_length
    }

@router.post("/ask", response_model=DocumentAskResponse, dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def ask_document(
    request: DocumentAskRequest,
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Юзер {current_user.email} задал вопрос по документам: '{request.question}'")
    
    # 1. Ищем релевантные куски в ChromaDB (ЗДЕСЬ ДОБАВЛЕН ФИЛЬТР ПО ФАЙЛУ!)
    search_results = vector_db.search(
        user_id=current_user.id, 
        query=request.question,
        filename=request.filename,  # <--- Теперь база ищет СТРОГО в нужном файле
        n_results=4
    )
    
    if not search_results:
        return DocumentAskResponse(
            question=request.question,
            answer="Я не нашла ответ на этот вопрос в указанном документе.",
            sources=[]
        )

    # 2. Формируем контекст для нейросети
    context_text = "\n\n---\n\n".join([f"Файл: {res['filename']}\nТекст: {res['text']}" for res in search_results])
    
    # Вытаскиваем уникальные названия файлов-источников
    unique_sources = list(set([res['filename'] for res in search_results]))
    
    # 3. Жесткий промпт: запрещаем ИИ придумывать факты
    prompt = (
        "Ты — Sahra AI, умный ассистент. Ответь на вопрос пользователя, опираясь ТОЛЬКО на предоставленные ниже фрагменты из его личных документов.\n"
        "Если в фрагментах нет ответа, прямо скажи об этом. Не придумывай информацию от себя. Отвечай структурированно и на русском языке.\n\n"
        f"Вопрос пользователя: {request.question}\n\n"
        f"Фрагменты документов:\n{context_text}"
    )
    
    # 4. Отправляем в Ollama
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                OLLAMA_GENERATE_URL, 
                json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=60.0
            )
            
            if resp.status_code != 200:
                raise AppError("AI generation failed", status_code=500)
                
            answer = resp.json().get("response", "")
            logger.success("Ответ по документам успешно сгенерирован!")
            
            return DocumentAskResponse(
                question=request.question, 
                answer=answer, 
                sources=unique_sources
            )
            
    except Exception as e:
        logger.error(f"Ошибка генерации ответа: {e}")
        raise AppError("Failed to generate answer from documents", status_code=500)
