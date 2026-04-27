from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re

from settings import settings


@dataclass(frozen=True)
class RetrievedChunk:
    source: str
    content: str
    score: float


class VectorStoreRetriever:
    def __init__(self, documents_dir: Path | None = None) -> None:
        self.documents_dir = documents_dir or settings.documents_dir

    def search(self, question: str, top_k: int = 4) -> list[RetrievedChunk]:
        chunks = self._load_chunks()
        if not chunks:
            return []

        query_tokens = self._tokens(question)
        ranked: list[RetrievedChunk] = []
        for source, content in chunks:
            score = self._score(query_tokens, content)
            if score <= 0:
                continue
            ranked.append(RetrievedChunk(source=source, content=content, score=score))

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]

    def _load_chunks(self) -> list[tuple[str, str]]:
        if not self.documents_dir.exists():
            return []

        chunks: list[tuple[str, str]] = []
        for path in sorted(self.documents_dir.rglob("*")):
            if path.is_dir() or path.suffix.lower() not in {".md", ".txt", ".rst"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
            if not text:
                continue
            for paragraph in self._split_paragraphs(text):
                chunks.append((path.name, paragraph))
        return chunks

    @staticmethod
    def _split_paragraphs(text: str) -> list[str]:
        parts = [part.strip() for part in re.split(r"\n\s*\n", text)]
        return [part for part in parts if part]

    @staticmethod
    def _tokens(text: str) -> Counter[str]:
        tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        return Counter(tokens)

    def _score(self, query_tokens: Counter[str], content: str) -> float:
        content_tokens = self._tokens(content)
        overlap = sum(min(count, content_tokens[token]) for token, count in query_tokens.items())
        return float(overlap)