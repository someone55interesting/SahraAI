from fastapi import FastAPI
from src.api import auth # Импортируем наш новый роутер

app = FastAPI(title="Sahra AI API", version="1.0.0")

# Подключаем роуты
app.include_router(auth.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
