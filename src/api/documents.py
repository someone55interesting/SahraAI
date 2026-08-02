from fastapi import APIRouter, UploadFile, File, Depends
from src.services.document_parser import document_parser
from src.api.deps import get_current_user
from src.models.user import User
from loguru import logger

router = APIRouter(prefix="/documents", tags=["Documents AI"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Юзер {current_user.email} загружает документ {file.filename}")
    
    # Парсим текст через наш сервис
    text = await document_parser.parse(file)
    text_length = len(text)
    
    logger.success(f"Документ {file.filename} успешно распарсен. Длина: {text_length} символов.")
    
    return {
        "filename": file.filename,
        "content_length": text_length,
        # Отдаем первые 500 символов, чтобы ты в Swagger мог убедиться, что текст читается корректно
        "preview": text[:500] + ("..." if text_length > 500 else "")
    }
