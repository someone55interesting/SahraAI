from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.models.chat import Conversation, Message
from src.repositories.base import BaseRepository

class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self):
        super().__init__(Conversation)

    async def get_user_conversations(self, db: AsyncSession, user_id: int):
        """Получить все диалоги конкретного пользователя (от новых к старым)."""
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_conversation_with_messages(self, db: AsyncSession, conversation_id: int, user_id: int):
        """Получить диалог и сразу подгрузить все его сообщения."""
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

# Экземпляры для работы в сервисах
conversation_repo = ConversationRepository()
message_repo = MessageRepository()
