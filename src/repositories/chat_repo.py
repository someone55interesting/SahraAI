from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from src.models.chat import Conversation, Message
from src.repositories.base import BaseRepository

class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self):
        super().__init__(Conversation)

    async def get_user_conversations_paginated(self, db: AsyncSession, user_id: int, page: int, size: int):
        """Получить диалоги пользователя с пагинацией (limit/offset) и общим количеством."""
        offset = (page - 1) * size
        
        # 1. Считаем общее количество записей в базе для этого юзера
        total_query = select(func.count()).select_from(self.model).where(self.model.user_id == user_id)
        total = await db.scalar(total_query)
        
        # 2. Получаем сами записи для текущей страницы
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc()) # Свежие чаты сверху
            .limit(size)
            .offset(offset)
        )
        result = await db.execute(query)
        items = result.scalars().all()
        
        return items, total

    async def get_conversation_with_messages(self, db: AsyncSession, conversation_id: int, user_id: int):
        """Получить диалог и сразу подгрузить все его сообщения (используется для WebSocket)."""
        query = (
            select(self.model)
            .where(self.model.id == conversation_id, self.model.user_id == user_id)
            .options(selectinload(self.model.messages))
        )
        result = await db.execute(query)
        return result.scalars().first()


class MessageRepository(BaseRepository[Message]):
    def __init__(self):
        super().__init__(Message)
        
    async def get_conversation_messages_paginated(self, db: AsyncSession, conversation_id: int, page: int, size: int):
        """Получить сообщения конкретного диалога с пагинацией."""
        offset = (page - 1) * size
        
        # 1. Считаем общее количество сообщений в этом чате
        total_query = select(func.count()).select_from(self.model).where(self.model.conversation_id == conversation_id)
        total = await db.scalar(total_query)
        
        # 2. Берем сообщения по убыванию даты (самые свежие сверху)
        query = (
            select(self.model)
            .where(self.model.conversation_id == conversation_id)
            .order_by(self.model.created_at.desc()) 
            .limit(size)
            .offset(offset)
        )
        result = await db.execute(query)
        items = result.scalars().all()
        
        return items, total

# Экземпляры для работы в сервисах
conversation_repo = ConversationRepository()
message_repo = MessageRepository()


