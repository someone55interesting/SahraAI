from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

async def app_error_handler(request: Request, exc: AppError):
    logger.error(f"Error {exc.status_code}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )
