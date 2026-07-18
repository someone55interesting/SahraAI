from fastapi import FastAPI
from src.api import auth, chat
from src.core.logger import setup_logger
from src.core.exceptions import AppError, app_error_handler

setup_logger()

app = FastAPI(title="Sahra AI API", version="1.0.0")

app.add_exception_handler(AppError, app_error_handler)
app.include_router(auth.router)
app.include_router(chat.router)  # <-- Добавили роутер для чата

@app.get("/health")
async def health_check():
    return {"status": "ok"}
