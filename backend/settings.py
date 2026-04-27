from dataclasses import dataclass
from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _split_csv(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if not value:
        return default
    items = [item.strip() for item in value.split(",")]
    return tuple(item for item in items if item)


@dataclass(frozen=True)
class Settings:
    app_name: str = "Production RAG System"
    app_version: str = "0.1.0"
    documents_dir: Path = PROJECT_ROOT / "data" / "documents"
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    cors_origins: tuple[str, ...] = _split_csv(
        os.getenv("CORS_ORIGINS"),
        ("http://localhost:3000", "http://127.0.0.1:3000"),
    )


settings = Settings()