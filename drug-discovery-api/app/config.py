from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    db_path: str = "db/drug_discovery.duckdb"
    # ORD / retrosynthesis dataset (read-only, separate from the app DB)
    ord_db_path: str = "db/retrosynthesis.duckdb"
    app_name: str = "Drug Discovery API"
    app_version: str = "0.1.0"
    debug: bool = False
    ai_model: str = "local-mock"
    ai_max_tokens: int = 8192

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
