from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from retriever.chunking import split_chunks
from settings import settings


@dataclass(frozen=True)
class RetrievedChunk:
    source: str
    content: str
    score: float


class VectorStoreRetriever:
    """Lexical retriever over locally indexed document chunks.

    Despite the module name there is no embedding store here: chunks are
    ranked with BM25 (default) or raw token-overlap counts, controlled by
    settings.scoring. Both scorers share the same tokenizer. Configs were
    compared on eval/questions.json; see data/processed/retrieval_eval.json.
    """

    def __init__(self, documents_dir: Path | None = None) -> None:
        self.documents_dir = documents_dir or settings.documents_dir
        self.index_path = self.documents_dir.parent / "index.json"
        self._index = None
        if self.index_path.exists():
            try:
                self._index = json.loads(self.index_path.read_text(encoding="utf-8"))
            except Exception:
                self._index = None

    def search(self, question: str, top_k: int = 4) -> list[RetrievedChunk]:
        if self._index:
            chunks = [
                (c["source"], c["content"], Counter(c["tokens"]))
                for c in self._index.get("chunks", [])
            ]
        else:
            chunks = [(s, c, self._tokens(c)) for s, c in self._load_chunks()]
        if not chunks:
            return []

        query_tokens = self._tokens(question)
        if settings.scoring == "bm25":
            scored = self._score_bm25(query_tokens, chunks)
        else:
            scored = self._score_overlap(query_tokens, chunks)

        ranked = [
            RetrievedChunk(source=source, content=content, score=round(score, 4))
            for (source, content, _), score in zip(chunks, scored)
            if score > 0
        ]
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]

    @staticmethod
    def _score_overlap(
        query_tokens: Counter[str], chunks: list[tuple[str, str, Counter[str]]]
    ) -> list[float]:
        return [
            float(sum(min(count, tokens[tok]) for tok, count in query_tokens.items()))
            for _, _, tokens in chunks
        ]

    @staticmethod
    def _score_bm25(
        query_tokens: Counter[str],
        chunks: list[tuple[str, str, Counter[str]]],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> list[float]:
        n = len(chunks)
        lengths = [sum(tokens.values()) for _, _, tokens in chunks]
        avgdl = sum(lengths) / max(n, 1)
        df: Counter[str] = Counter()
        for _, _, tokens in chunks:
            df.update(tokens.keys())

        scores = []
        for (_, _, tokens), dl in zip(chunks, lengths):
            score = 0.0
            for tok in query_tokens:
                tf = tokens.get(tok, 0)
                if tf == 0:
                    continue
                idf = math.log(1 + (n - df[tok] + 0.5) / (df[tok] + 0.5))
                score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / max(avgdl, 1e-9)))
            scores.append(score)
        return scores

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
            for chunk in split_chunks(text, settings.chunk_strategy):
                chunks.append((path.name, chunk))
        return chunks

    @staticmethod
    def _split_paragraphs(text: str) -> list[str]:
        parts = [part.strip() for part in re.split(r"\n\s*\n", text)]
        return [part for part in parts if part]

    @staticmethod
    def _tokens(text: str) -> Counter[str]:
        tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        return Counter(tokens)
