from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict

from retriever.vector_store import VectorStoreRetriever
from settings import settings


@dataclass
class ChunkRecord:
    id: str
    source: str
    content: str
    tokens: Dict[str, int]


class Indexer:
    def __init__(self, documents_dir: Path | None = None) -> None:
        self.documents_dir = documents_dir or settings.documents_dir
        self.index_path = self.documents_dir.parent / "index.json"

    def build_index(self) -> dict:
        retriever = VectorStoreRetriever(self.documents_dir)

        chunks = []
        for path in sorted(self.documents_dir.rglob("*")):
            if path.is_dir() or path.suffix.lower() not in {".md", ".txt", ".rst"}:
                continue

            text = path.read_text(encoding="utf-8", errors="ignore").strip()
            if not text:
                continue

            for i, paragraph in enumerate(retriever._split_paragraphs(text)):
                token_counts = retriever._tokens(paragraph)
                chunks.append(
                    ChunkRecord(
                        id=f"{path.name}::{i}",
                        source=path.name,
                        content=paragraph,
                        tokens=dict(token_counts),
                    )
                )

        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "chunks": [asdict(c) for c in chunks],
            "stats": {"documents": len({c.source for c in chunks}), "chunks": len(chunks)},
        }

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload


indexer = Indexer()
