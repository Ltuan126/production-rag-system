from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from settings import settings


@dataclass(frozen=True)
class DocumentInfo:
    path: str
    paragraphs: int
    characters: int


class DocumentService:
    def __init__(self, documents_dir: Path | None = None) -> None:
        self.documents_dir = documents_dir or settings.documents_dir

    def list_documents(self) -> list[DocumentInfo]:
        if not self.documents_dir.exists():
            return []

        documents: list[DocumentInfo] = []
        for path in sorted(self.documents_dir.rglob("*")):
            if path.is_dir() or path.suffix.lower() not in {".md", ".txt", ".rst"}:
                continue

            text = path.read_text(encoding="utf-8", errors="ignore").strip()
            if not text:
                continue

            paragraphs = len([part for part in text.split("\n\n") if part.strip()])
            documents.append(
                DocumentInfo(
                    path=path.relative_to(settings.documents_dir.parent).as_posix(),
                    paragraphs=paragraphs,
                    characters=len(text),
                )
            )

        return documents
