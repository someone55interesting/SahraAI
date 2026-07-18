from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Инициализируем приложение с правильным названием и версией
app = FastAPI(
    title="Sahra AI API",
    description="Backend for Sahra AI Project",
    version="1.0.0"
)

# Создаем базовый роут для проверки работоспособности сервера (Health Check)
@app.get("/health", tags=["System"])
async def health_check():
    """
    Эндпоинт для проверки статуса сервера.
    Если сервер работает, он вернет статус "ok".
    """
    return JSONResponse(
        content={
            "status": "ok",
            "message": "Sahra AI backend is running optimally."
        },
        status_code=200
    )
