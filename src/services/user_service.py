from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.user import User, Profile
from src.schemas.user import UserCreate
from src.core.security import get_password_hash

async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Создает пользователя и его пустой профиль в базе."""
    hashed_pw = get_password_hash(user_data.password)
    
    # Создаем объект пользователя
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Создаем профиль для этого пользователя
    new_profile = Profile(
        user_id=new_user.id,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    
    db.add(new_profile)
    await db.commit()
    
    return new_user

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Ищет пользователя по email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()
