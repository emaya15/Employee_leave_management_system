# app/config.py
# Reads the values from the ".env" file so we never hard-code secrets in code.
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Tell pydantic-settings to load values from the .env file
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
