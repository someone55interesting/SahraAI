from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.db.database import get_db
from src.models.user import User
from src.api.deps import get_current_user
from src.schemas.memory import MemoryCreate, MemoryResponse
from src.repositories.memory_repo import memory_repo
from src.core.exceptions import AppError

router = APIRouter(prefix="/memory", tags=["Memory"])

@router.get("/", response_model=List[MemoryResponse])
async def get_memories(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Получить все факты, которые нейросеть знает о тебе."""
    return await memory_repo.get_user_memories(db, current_user.id)

@router.post("/", response_model=MemoryResponse)
async def add_memory(memory_in: MemoryCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Добавить новый факт в память нейросети."""
    return await memory_repo.create(db, {"user_id": current_user.id, "fact": memory_in.fact})


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(memory_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Удалить факт из памяти по его ID."""
    
    # Ищем факт в базе
    memory = await memory_repo.get_by_id(db, memory_id)
    
    # Проверяем, существует ли он и принадлежит ли текущему юзеру
    if not memory or memory.user_id != current_user.id:
        raise AppError("Memory fact not found", status_code=404)
    
    # Удаляем
    await memory_repo.delete(db, memory_id)
    return None
