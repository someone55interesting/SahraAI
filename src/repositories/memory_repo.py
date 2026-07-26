from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.memory import UserMemory
from src.repositories.base import BaseRepository

class MemoryRepository(BaseRepository[UserMemory]):
    def __init__(self):
        super().__init__(UserMemory)

    async def get_user_memories(self, db: AsyncSession, user_id: int):
        """Получает все факты о конкретном пользователе."""
        query = select(self.model).where(self.model.user_id == user_id).order_by(self.model.created_at.asc())
        result = await db.execute(query)
        return result.scalars().all()

memory_repo = MemoryRepository()
