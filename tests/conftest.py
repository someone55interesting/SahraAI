import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.main import app
from src.db.database import Base, get_db

# 1. Используем SQLite в оперативной памяти для невероятно быстрых тестов.
# Это гарантирует, что тесты не удалят реальную базу данных.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=sqlalchemy.pool.StaticPool, 
)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine_test, class_=AsyncSession, expire_on_commit=False
)

# 2. Фикстура базы данных: создает таблицы перед каждым тестом и удаляет после
@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
        
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# 3. Фикстура клиента: подменяет зависимость БД на тестовую сессию
@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    # Подмена зависимости
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # ASGITransport нужен для работы с асинхронным FastAPI
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()


