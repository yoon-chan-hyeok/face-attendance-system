# app/core/config.py
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 1. Original values to read from .env (Optional so no error if missing)
    APP_ENV: str = "dev"
    DATABASE_URL_DEV: Optional[str] = None
    DATABASE_URL_PROD: Optional[str] = None
    LIVENESS_ADMIN_PASSWORD: Optional[str] = None  # Liveness admin password
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    

    # 2. Final variable to use in code
    DATABASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",  # Now only looking at one file!
        env_file_encoding="utf-8",
        extra="ignore"    # Ignore undefined variables
    )

    # 3. Logic: Auto-set DATABASE_URL based on APP_ENV
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v, info):
        # If value already exists (set via env var), use it
        if v:
            return v
        
        # Check currently loaded values
        env_values = info.data
        app_env = env_values.get("APP_ENV", "dev")
        
        if app_env == "prod":
            url = env_values.get("DATABASE_URL_PROD")
            print("Connecting to PROD DB.")
        else:
            url = env_values.get("DATABASE_URL_DEV")
            print("Connecting to DEV DB.")
            
        if not url:
            raise ValueError(f"No DB URL found in .env for {app_env} environment.")
            
        return url

settings = Settings()
