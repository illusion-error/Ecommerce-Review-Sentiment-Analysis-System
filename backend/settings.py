"""Runtime settings for the FastAPI backend.

The backend can run immediately with SQLite for local development and tests.
When MySQL/Redis are available, set the environment variables in `.env` and
switch `DATABASE_BACKEND=mysql`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    app_name: str = "E-commerce Review Sentiment Analysis API"
    app_version: str = "0.1.0"
    database_backend: str = os.getenv("DATABASE_BACKEND", "sqlite").lower()
    sqlite_db_path: Path = Path(
        os.getenv("SQLITE_DB_PATH", str(PROJECT_ROOT / "backend" / "backend_data" / "sentiment.db"))
    )
    mysql_host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_database: str = os.getenv("MYSQL_DATABASE", "sentiment_analysis")
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    redis_host: str = os.getenv("REDIS_HOST", "127.0.0.1")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "86400"))
    max_upload_rows: int = int(os.getenv("MAX_UPLOAD_ROWS", "5000"))


settings = Settings()

