from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".envs" / ".env.local"

class Settings(BaseSettings):
    ENVIRONMENT: Literal["local", "stage", "prod"] = "local" # Default to "local" if not set in the environment variables

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_ignore_empty=True, # Ignore empty environment variables
        extra="ignore", # Ignore extra fields in the .env file that are not defined in the Settings class
    )

    API_V1_STR: str = ""
    PROJECT_NAME: str = ""
    PROJECT_DESCRIPTION: str = ""
    SITE_NAME: str = ""
    DATABASE_URL: str = ""
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True
    MAIL_FROM: str = ""
    MAIL_FROM_NAME: str = ""
    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025
    MAILPIT_UI_PORT: int = 8025
    
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"


settings = Settings()