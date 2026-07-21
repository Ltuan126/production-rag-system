"""Document chunking strategies shared by the indexer, retriever, and eval harness.

Two strategies are supported:

- "paragraph": split on blank lines. Original behavior; chunks follow author
  structure but markdown list items and short lines become tiny, low-signal
  chunks.
- "fixed512" / "fixed256": fixed-size character windows snapped to word
  boundaries, with 25% overlap. Evaluated best on eval/questions.json
  (see data/processed/retrieval_eval.json); larger windows keep related
  sentences together, which helps lexical scoring.
"""
from __future__ import annotations

import re

FIXED_SIZES = {"fixed256": (256, 64), "fixed512": (512, 128)}


def split_paragraphs(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"\n\s*\n", text)]
    return [part for part in parts if part]


def split_fixed(text: str, size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    words = text.split()
    current: list[str] = []
    length = 0
    i = 0
    while i < len(words):
        current.append(words[i])
        length += len(words[i]) + 1
        i += 1
        if length >= size:
            chunks.append(" ".join(current))
            # back up to create overlap
            back = 0
            j = len(current)
            while j > 0 and back < overlap:
                j -= 1
                back += len(current[j]) + 1
            current = current[j:] if j < len(current) else []
            length = sum(len(w) + 1 for w in current)
    if current and length > overlap:  # avoid emitting a pure-overlap tail
        chunks.append(" ".join(current))
    return chunks


def split_chunks(text: str, strategy: str) -> list[str]:
    if strategy == "paragraph":
        return split_paragraphs(text)
    if strategy in FIXED_SIZES:
        size, overlap = FIXED_SIZES[strategy]
        return split_fixed(text, size, overlap)
    raise ValueError(f"Unknown chunk strategy: {strategy!r}")
