"""Retrieval evaluation harness.

Compares chunking strategies (paragraph vs fixed-size windows) and scoring
functions (raw token overlap vs BM25) against a hand-labeled question set
(eval/questions.json). A retrieved chunk counts as relevant if it comes from
the expected source document AND contains the gold answer span
(case-insensitive, whitespace-normalized). Span containment is used instead of
chunk ids so the same ground truth works across chunking configurations.

Metrics: recall@1/3/5 (fraction of questions with a relevant chunk in top-k)
and MRR@10.

Usage (from repo root):
    python eval/run_retrieval_eval.py

Writes data/processed/retrieval_eval.json and retrieval_eval.csv.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from retriever.chunking import split_fixed, split_paragraphs  # noqa: E402
from retriever.vector_store import VectorStoreRetriever  # noqa: E402

DOCUMENTS_DIR = REPO_ROOT / "data" / "documents"
QUESTIONS_PATH = REPO_ROOT / "eval" / "questions.json"
OUT_DIR = REPO_ROOT / "data" / "processed"

TOP_K = 10
RECALL_KS = (1, 3, 5)

tokenize = VectorStoreRetriever._tokens


@dataclass(frozen=True)
class Chunk:
    source: str
    content: str


# ---------------------------------------------------------------- chunking


def load_documents() -> list[tuple[str, str]]:
    docs = []
    for path in sorted(DOCUMENTS_DIR.rglob("*")):
        if path.is_dir() or path.suffix.lower() not in {".md", ".txt", ".rst"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if text:
            docs.append((path.name, text))
    return docs


def chunk_paragraph(docs: list[tuple[str, str]]) -> list[Chunk]:
    """Production chunking: split on blank lines."""
    return [Chunk(name, p) for name, text in docs for p in split_paragraphs(text)]


def chunk_fixed(docs: list[tuple[str, str]], size: int, overlap: int) -> list[Chunk]:
    """Fixed-size character windows with overlap, snapped to word boundaries."""
    return [Chunk(name, c) for name, text in docs for c in split_fixed(text, size, overlap)]


# ---------------------------------------------------------------- scoring


def rank_overlap(query: str, chunks: list[Chunk], top_k: int) -> list[Chunk]:
    """Production scoring: raw token-overlap count (sum of min counts)."""
    q = tokenize(query)
    scored = []
    for chunk in chunks:
        c = tokenize(chunk.content)
        score = sum(min(count, c[tok]) for tok, count in q.items())
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [c for _, c in scored[:top_k]]


def rank_bm25(query: str, chunks: list[Chunk], top_k: int, k1: float = 1.5, b: float = 0.75) -> list[Chunk]:
    """Okapi BM25 over the same tokenizer."""
    chunk_tokens = [tokenize(c.content) for c in chunks]
    n = len(chunks)
    avgdl = sum(sum(t.values()) for t in chunk_tokens) / max(n, 1)
    df: Counter[str] = Counter()
    for t in chunk_tokens:
        df.update(t.keys())

    q = tokenize(query)
    scored = []
    for chunk, tokens in zip(chunks, chunk_tokens):
        dl = sum(tokens.values())
        score = 0.0
        for tok in q:
            tf = tokens.get(tok, 0)
            if tf == 0:
                continue
            idf = math.log(1 + (n - df[tok] + 0.5) / (df[tok] + 0.5))
            score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / max(avgdl, 1e-9)))
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [c for _, c in scored[:top_k]]


# ---------------------------------------------------------------- evaluation


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def is_relevant(chunk: Chunk, expected_source: str, answer_span: str) -> bool:
    return chunk.source == expected_source and normalize(answer_span) in normalize(chunk.content)


def validate_gold_spans(docs: list[tuple[str, str]], questions: list[dict]) -> None:
    by_name = {name: normalize(text) for name, text in docs}
    for item in questions:
        doc = by_name.get(item["expected_source"])
        assert doc is not None, f"{item['id']}: unknown source {item['expected_source']}"
        assert normalize(item["answer_span"]) in doc, (
            f"{item['id']}: answer span not found in {item['expected_source']}: {item['answer_span']!r}"
        )


def evaluate(config_name: str, chunks: list[Chunk], ranker, questions: list[dict]) -> dict:
    per_question = []
    for item in questions:
        results = ranker(item["question"], chunks, TOP_K)
        rank = next(
            (i + 1 for i, c in enumerate(results) if is_relevant(c, item["expected_source"], item["answer_span"])),
            None,
        )
        per_question.append({"id": item["id"], "rank": rank})

    n = len(per_question)
    metrics = {f"recall@{k}": sum(1 for r in per_question if r["rank"] and r["rank"] <= k) / n for k in RECALL_KS}
    metrics["mrr@10"] = sum(1 / r["rank"] for r in per_question if r["rank"]) / n
    return {
        "config": config_name,
        "num_chunks": len(chunks),
        "metrics": {k: round(v, 4) for k, v in metrics.items()},
        "per_question": per_question,
    }


def main() -> None:
    docs = load_documents()
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))["questions"]
    validate_gold_spans(docs, questions)

    chunkings = {
        "paragraph": chunk_paragraph(docs),
        "fixed256": chunk_fixed(docs, size=256, overlap=64),
        "fixed512": chunk_fixed(docs, size=512, overlap=128),
    }
    scorers = {"overlap": rank_overlap, "bm25": rank_bm25}

    results = [
        evaluate(f"{chunk_name}+{scorer_name}", chunks, ranker, questions)
        for chunk_name, chunks in chunkings.items()
        for scorer_name, ranker in scorers.items()
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "question_set": str(QUESTIONS_PATH.relative_to(REPO_ROOT)),
        "num_questions": len(questions),
        "top_k_retrieved": TOP_K,
        "baseline_config": "paragraph+overlap",
        "results": results,
    }
    (OUT_DIR / "retrieval_eval.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with (OUT_DIR / "retrieval_eval.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["config", "num_chunks", "recall@1", "recall@3", "recall@5", "mrr@10"])
        for r in results:
            m = r["metrics"]
            writer.writerow([r["config"], r["num_chunks"], m["recall@1"], m["recall@3"], m["recall@5"], m["mrr@10"]])

    print(f"{'config':<20} {'chunks':>6} {'r@1':>6} {'r@3':>6} {'r@5':>6} {'mrr@10':>7}")
    for r in results:
        m = r["metrics"]
        print(
            f"{r['config']:<20} {r['num_chunks']:>6} {m['recall@1']:>6.2f} {m['recall@3']:>6.2f} "
            f"{m['recall@5']:>6.2f} {m['mrr@10']:>7.3f}"
        )
    print(f"\nWrote {OUT_DIR / 'retrieval_eval.json'} and .csv")


if __name__ == "__main__":
    main()
