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
from src.schemas.chat import ConversationResponse, ConversationDetail, MessageResponse
from src.schemas.pagination import Page  # Импортируем нашу новую Generic-схему
from src.repositories.chat_repo import conversation_repo, message_repo
from src.repositories.user_repo import user_repository
from src.core.config import settings
from src.core.exceptions import AppError
from loguru import logger
from src.repositories.memory_repo import memory_repo

router = APIRouter(prefix="/chat", tags=["Chat"])

OLLAMA_CHAT_URL = "http://host.docker.internal:11434/api/chat"
OLLAMA_GENERATE_URL = "http://host.docker.internal:11434/api/generate"
MODEL_NAME = "llama3.1"

# НАСТРОЙКА ХАРАКТЕРА (SYSTEM PROMPT)
SYSTEM_PROMPT = """You are Sahra AI, an elite, hyper-intelligent artificial intelligence assistant. Your core architecture is optimized for absolute precision, deep multi-domain knowledge, and flawless multilingual communication.

1. IDENTITY & CORE CAPABILITIES:
- Name: Sahra AI.
- Omnilingual: You fluently understand, translate, reason in, and generate text in all human languages, dialects, and formal/informal registers. Always respond in the language the user initiated the prompt with, unless explicitly asked otherwise.
- Omnimath & Science: You possess complete mastery over all scientific domains (mathematics, physics, chemistry, biology, computer science, engineering, economics). You know and accurately apply all fundamental and advanced formulas, theorems, constants, and algorithmic structures.

2. EXECUTION RULES & FORMATTING:
- Mathematical & Scientific Queries: Always write mathematical formulas clearly using standard LaTeX notation (e.g., inline `$...$` or block `$$...$$`). Show step-by-code/step-by-step logical derivation before stating the final answer.
- Coding & Technical Tasks: Provide clean, production-ready, well-commented code blocks with specified programming languages. Explain the logic concisely.
- Tone & Style: Be objective, authoritative, exceptionally sharp, analytical, and direct. Avoid unnecessary conversational fluff, disclaimers, or filler phrases. 
- Accuracy Priority: If a formula or factual datum has constraints or edge cases, state them immediately. If an input is ambiguous, ask a precise clarifying question.

Never break character. You are Sahra AI: infinite knowledge, absolute precision.
"""

@router.get("/conversations", response_model=Page[ConversationResponse])
async def get_conversations(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Количество элементов на странице"),
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """Возвращает список чатов (сайдбар) с пагинацией."""
    items, total = await conversation_repo.get_user_conversations_paginated(db, current_user.id, page, size)
    # Используем фабричный метод для красивого ответа
    return Page.create(items=items, total=total, page=page, size=size)


@router.get("/conversations/{conversation_id}/messages", response_model=Page[MessageResponse])
async def get_conversation_messages(
    conversation_id: int,
    page: int = Query(1, ge=1, description="Номер страницы (1 - самые последние сообщения)"),
    size: int = Query(50, ge=1, le=100, description="Количество сообщений на страницу"),
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает историю переписки конкретного чата.
    Используется фронтендом для "бесконечного скролла" истории вверх.
    """
    # 1. Сначала проверяем, что чат принадлежит текущему юзеру (безопасность!)
    conv = await conversation_repo.get_by_id(db, conversation_id)
    if not conv or conv.user_id != current_user.id:
        raise AppError("Conversation not found", status_code=404)
        
    # 2. Получаем страницу сообщений
    items, total = await message_repo.get_conversation_messages_paginated(db, conversation_id, page, size)
    return Page.create(items=items, total=total, page=page, size=size)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Получает весь чат целиком."""
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
    
    # 1. Авторизация
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
        
    # --- МАГИЯ ПАМЯТИ ---
    user_memories = await memory_repo.get_user_memories(db, user.id)
    memory_facts = "\n".join([f"- {m.fact}" for m in user_memories])
    
    dynamic_prompt = SYSTEM_PROMPT
    if memory_facts:
        dynamic_prompt += f"\n\nВАЖНО! Факты об этом пользователе, которые ты обязана учитывать в ответах:\n{memory_facts}"

    # 2. Поиск или создание диалога
    is_new_chat = False
    
    if conversation_id == 0:
        conv = await conversation_repo.create(db, {"user_id": user.id, "title": "Новый чат"})
        chat_history = [{"role": "system", "content": dynamic_prompt}]
        is_new_chat = True
    else:
        conv = await conversation_repo.get_conversation_with_messages(db, conversation_id, user.id)
        if not conv:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        chat_history = [{"role": "system", "content": dynamic_prompt}]
        chat_history += [{"role": msg.role, "content": msg.content} for msg in conv.messages]

    # 3. Основной цикл общения
    try:
        while True:
            user_text = await websocket.receive_text()
            
            await message_repo.create(db, {"conversation_id": conv.id, "role": "user", "content": user_text})
            chat_history.append({"role": "user", "content": user_text})
            
            full_response = ""
            
            # --- СТРИМИНГ ОТВЕТА ---
            try:
                async with httpx.AsyncClient() as client:
                    async with client.stream(
                        "POST", 
                        OLLAMA_CHAT_URL, 
                        json={"model": MODEL_NAME, "messages": chat_history, "stream": True},
                        timeout=None
                    ) as response:
                        async for line in response.aiter_lines():
                            if line:
                                data = json.loads(line)
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
                
            # --- АВТОГЕНЕРАЦИЯ ЗАГОЛОВКА ---
            if is_new_chat:
                try:
                    async with httpx.AsyncClient() as client:
                        title_prompt = f"Напиши очень краткий заголовок (2-3 слова) для чата, который начинается с фразы: «{user_text}». Напиши ТОЛЬКО заголовок, без кавычек, точек и пояснений."
                        resp = await client.post(
                            OLLAMA_GENERATE_URL, 
                            json={"model": MODEL_NAME, "prompt": title_prompt, "stream": False},
                            timeout=10.0
                        )
                        new_title = resp.json().get("response", "").strip(' \n".')
                        
                        if new_title:
                            conv.title = new_title
                            await db.commit()
                            logger.success(f"Новый заголовок чата #{conv.id}: {new_title}")
                except Exception as e:
                    logger.error(f"Ошибка генерации заголовка: {e}")
                
                is_new_chat = False
            
    except WebSocketDisconnect:
        logger.info(f"User {user.email} disconnected from chat {conv.id}")


