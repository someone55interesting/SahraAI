import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Проверка успешной регистрации пользователя."""
    response = await client.post(
        "/auth/register",
        json={
            "email": "sahra@example.com",
            "password": "supersecretpassword",
            "first_name": "Sahra",
            "last_name": "AI"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "sahra@example.com"
    assert "id" in data
    # Убеждаемся, что хэш пароля случайно не утек в ответ API
    assert "hashed_password" not in data

@pytest.mark.asyncio
async def test_register_duplicate_user(client: AsyncClient):
    """Проверка защиты от регистрации дублирующегося email."""
    user_data = {
        "email": "duplicate@example.com",
        "password": "password123"
    }
    
    # Первая регистрация (должна быть успешной)
    await client.post("/auth/register", json=user_data)
    
    # Вторая попытка с тем же email (должна вернуть ошибку 400)
    response = await client.post("/auth/register", json=user_data)
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Проверка успешной выдачи JWT токена при логине."""
    user_data = {
        "email": "login@example.com",
        "password": "password123"
    }
    
    # Регистрируем юзера
    await client.post("/auth/register", json=user_data)
    
    # Пробуем войти. OAuth2PasswordRequestForm требует отправлять данные как form-data (username/password)
    response = await client.post(
        "/auth/login", 
        data={"username": "login@example.com", "password": "password123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Проверка успешной регистрации пользователя."""
    response = await client.post(
        "/auth/register",
        json={
            "email": "sahra@example.com",
            "password": "supersecretpassword",
            "first_name": "Sahra",
            "last_name": "AI"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "sahra@example.com"
    assert "id" in data
    # Убеждаемся, что хэш пароля случайно не утек в ответ API
    assert "hashed_password" not in data

@pytest.mark.asyncio
async def test_register_duplicate_user(client: AsyncClient):
    """Проверка защиты от регистрации дублирующегося email."""
    user_data = {
        "email": "duplicate@example.com",
        "password": "password123"
    }
    
    # Первая регистрация (должна быть успешной)
    await client.post("/auth/register", json=user_data)
    
    # Вторая попытка с тем же email (должна вернуть ошибку 400)
    response = await client.post("/auth/register", json=user_data)
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Проверка успешной выдачи JWT токена при логине."""
    user_data = {
        "email": "login@example.com",
        "password": "password123"
    }
    
    # Регистрируем юзера
    await client.post("/auth/register", json=user_data)
    
    # Пробуем войти. OAuth2PasswordRequestForm требует отправлять данные как form-data (username/password)
    response = await client.post(
        "/auth/login", 
        data={"username": "login@example.com", "password": "password123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


