import asyncio
import jwt
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.db.database import get_db
from src.models.user import User
from src.api.deps import get_current_user
from src.schemas.chat import ConversationResponse, ConversationDetail
from src.repositories.chat_repo import conversation_repo, message_repo
from src.repositories.user_repo import user_repository
from src.core.config import settings
from src.core.exceptions import AppError
from loguru import logger

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Получить список всех диалогов пользователя."""
    return await conversation_repo.get_user_conversations(db, current_user.id)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Получить историю конкретного диалога."""
    conv = await conversation_repo.get_conversation_with_messages(db, conversation_id, current_user.id)
    if not conv:
        raise AppError("Conversation not found", status_code=404)
    return conv


@router.websocket("/ws/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket, 
    conversation_id: int, 
    token: str = Query(...), 
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket эндпоинт для чата с AI.
    Если conversation_id = 0, создается новый диалог.
    """
    await websocket.accept()
    
    # 1. Авторизация (в WebSocket токены передаются через URL)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user = await user_repository.get_by_email(db, payload.get("sub"))
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    # 2. Поиск или создание диалога
    if conversation_id == 0:
        conv = await conversation_repo.create(db, {"user_id": user.id, "title": "Новый чат"})
    else:
        conv = await conversation_repo.get_conversation_with_messages(db, conversation_id, user.id)
        if not conv:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
    # 3. Основной цикл общения
    try:
        while True:
            # Ждем сообщение от пользователя
            user_text = await websocket.receive_text()
            
            # Сохраняем в БД
            await message_repo.create(db, {
                "conversation_id": conv.id,
                "role": "user",
                "content": user_text
            })
            
            # TODO: На ЭТАПЕ 4 здесь будет вызов реальной модели AI.
            # Пока делаем заглушку, которая имитирует "раздумья" и стриминг текста.
            mock_ai_response = f"Привет! Я Sahra AI. Я получила твое сообщение: «{user_text}». Скоро ко мне подключат настоящий мозг!"
            
            # Стримим ответ по одной букве (имитация генерации)
            for char in mock_ai_response:
                await websocket.send_text(char)
                await asyncio.sleep(0.02) # Небольшая задержка
                
            # Отправляем специальный сигнал, что генерация завершена
            await websocket.send_text("[DONE]")
            
            # Сохраняем ответ ИИ в базу
            await message_repo.create(db, {
                "conversation_id": conv.id,
                "role": "assistant",
                "content": mock_ai_response
            })
            
    except WebSocketDisconnect:
        logger.info(f"User {user.email} disconnected from chat {conv.id}")
