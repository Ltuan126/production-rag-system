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
        self.index_path = self.documents_dir.parent / "index.json"
        self._index = None
        if self.index_path.exists():
            try:
                import json

                self._index = json.loads(self.index_path.read_text(encoding="utf-8"))
            except Exception:
                self._index = None

    def search(self, question: str, top_k: int = 4) -> list[RetrievedChunk]:
        if self._index:
            chunks = [(c["source"], c["content"], c["tokens"]) for c in self._index.get("chunks", [])]
        else:
            chunks = [(s, c, None) for s, c in self._load_chunks()]
        if not chunks:
            return []

        query_tokens = self._tokens(question)
        ranked: list[RetrievedChunk] = []
        for tup in chunks:
            source, content = tup[0], tup[1]
            tokens = tup[2]
            if tokens is None:
                score = self._score(query_tokens, content)
            else:
                # tokens is a dict {token: count}
                overlap = sum(min(query_tokens.get(t, 0), tokens.get(t, 0)) for t in query_tokens.keys())
                score = float(overlap)

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