from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sahra AI"
    VERSION: str = "1.0.0"
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    TAVILY_API_KEY: str
    REDIS_URL: str = "redis://localhost:6379/0"
    OLLAMA_URL: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "llama3.1"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()