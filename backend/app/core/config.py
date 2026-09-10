import os
from typing import Any, List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict



BACKEND_DIR: Path = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_DIR / ".env"), str(BACKEND_DIR.parent / ".env"), ".env"),
        case_sensitive=True, 
        extra="ignore"
    )

    PROJECT_NAME: str = "SmartExcel PTPN AI Modeling System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Base directories
    BASE_DIR: Path = BACKEND_DIR
    STORAGE_DIR: Path = BACKEND_DIR.parent / "storage"
    UPLOAD_DIR: Path = BACKEND_DIR.parent / "storage" / "uploads"
    EXPORT_DIR: Path = BACKEND_DIR.parent / "storage" / "exports"
    SAMPLE_DIR: Path = BACKEND_DIR.parent / "storage" / "samples"
    
    # Database Configuration
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_DATABASE: str = "smart_excel"
    DB_USERNAME: str = "smartAdmin"
    DB_PASSWORD: str = ""
    DATABASE_URL: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.DATABASE_URL:
            if self.DB_PASSWORD:
                self.DATABASE_URL = f"postgresql+psycopg2://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
            else:
                self.DATABASE_URL = f"postgresql+psycopg2://{self.DB_USERNAME}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
    
    # AI / LLM Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
settings.SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
