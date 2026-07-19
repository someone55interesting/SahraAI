import asyncio
import jwt
import json
import httpx
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

# ИСПОЛЬЗУЕМ ЭНДПОИНТ ЧАТА, ЧТОБЫ ПЕРЕДАВАТЬ ИСТОРИЮ
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.1"

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await conversation_repo.get_user_conversations(db, current_user.id)

@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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
    await websocket.accept()
    
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
        
    if conversation_id == 0:
        conv = await conversation_repo.create(db, {"user_id": user.id, "title": "Новый чат"})
        chat_history = []
    else:
        conv = await conversation_repo.get_conversation_with_messages(db, conversation_id, user.id)
        if not conv:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        # Загружаем старые сообщения из базы в память Ollama
        chat_history = [{"role": msg.role, "content": msg.content} for msg in conv.messages]
            
    try:
        while True:
            user_text = await websocket.receive_text()
            
            await message_repo.create(db, {"conversation_id": conv.id, "role": "user", "content": user_text})
            chat_history.append({"role": "user", "content": user_text})
            
            full_response = ""
            
            try:
                async with httpx.AsyncClient() as client:
                    async with client.stream(
                        "POST", 
                        OLLAMA_URL, 
                        json={"model": MODEL_NAME, "messages": chat_history, "stream": True},
                        timeout=None
                    ) as response:
                        async for line in response.aiter_lines():
                            if line:
                                data = json.loads(line)
                                # Для /api/chat ответ лежит в message -> content
                                chunk = data.get("message", {}).get("content", "")
                                full_response += chunk
                                await websocket.send_text(chunk)
                                
            except Exception as e:
                logger.error(f"Ollama connection error: {e}")
                await websocket.send_text("\n[Ошибка подключения к ИИ]")
                
            await websocket.send_text("[DONE]")
            
            if full_response:
                await message_repo.create(db, {"conversation_id": conv.id, "role": "assistant", "content": full_response})
                chat_history.append({"role": "assistant", "content": full_response})
            
    except WebSocketDisconnect:
        logger.info(f"User {user.email} disconnected from chat {conv.id}")