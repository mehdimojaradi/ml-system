from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".envs" / ".env.local"

class Settings(BaseSettings):
    ENVIRONMENT: Literal["local", "stage", "prod"] = "local"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = ""
    PROJECT_NAME: str = ""
    PROJECT_DESCRIPTION: str = ""
    SITE_NAME: str = ""


settings = Settings()