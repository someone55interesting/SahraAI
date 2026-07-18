from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User, Profile
from src.schemas.user import UserCreate
from src.core.security import get_password_hash
from src.repositories.user_repo import user_repository
from src.core.exceptions import AppError
from loguru import logger

async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    logger.info(f"Попытка регистрации: {user_data.email}")
    
    # Проверяем пользователя через репозиторий
    existing_user = await user_repository.get_by_email(db, user_data.email)
    if existing_user:
        logger.warning(f"Ошибка регистрации: Email {user_data.email} уже занят")
        raise AppError("Email already registered", status_code=400)
    
    hashed_pw = get_password_hash(user_data.password)
    user_dict = {"email": user_data.email, "hashed_password": hashed_pw}
    
    # Создаем пользователя через репозиторий
    new_user = await user_repository.create(db, user_dict)
    
    # Создаем профиль
    new_profile = Profile(
        user_id=new_user.id,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    db.add(new_profile)
    await db.commit()
    
    logger.success(f"Пользователь успешно создан: {new_user.email}")
    return new_user

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await user_repository.get_by_email(db, email)
