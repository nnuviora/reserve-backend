from typing import Optional

from pydantic import (
    Field,
    field_validator,
    model_validator,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from dotenv import load_dotenv
import os

# абсолютний шлях до .env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=env_path)

class ConfigSettings(BaseSettings):
    PROJECT_NAME: str

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str

    DB_URI: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def generate_db_uri(self):
        if not self.DB_URI:
            self.DB_URI = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    SENDER: str
    CHARSET: str
    CONFIGURATION_SET: str
    AWS_REGION: str
    AWS_BUCKET_NAME: str
    ACCESS_KEY: str
    SECRET_ACCESS_KEY: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    GOOGLE_AUTH_URL: str
    GOOGLE_TOKEN_URL: str
    GOOGLE_USERINFO_URL: str

    # model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8")


config_setting = ConfigSettings()
