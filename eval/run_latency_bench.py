"""Latency and cache benchmark.

Drives the FastAPI app in-process via TestClient and measures end-to-end
/api/query latency in three phases:

1. cold  — every question from eval/questions.json once, empty cache (all misses)
2. warm  — the same questions again (all cache hits)
3. mixed — 200 requests sampled with a Zipf-like skew over the question set,
           starting from an empty cache, to estimate a realistic hit rate

Numbers include FastAPI routing + retrieval + answer generation. If Ollama is
not running the LLM falls back to the template mock, which makes generation
nearly free — the run records which mode was active so results are not
misread. Run with Ollama up to measure real generation latency.

Usage (from repo root):
    python eval/run_latency_bench.py

Writes data/processed/latency_bench.json.
"""
from __future__ import annotations

import json
import random
import statistics
import sys
from pathlib import Path
from time import perf_counter

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from services.rag_service import rag_service  # noqa: E402
from settings import settings  # noqa: E402

QUESTIONS_PATH = REPO_ROOT / "eval" / "questions.json"
OUT_PATH = REPO_ROOT / "data" / "processed" / "latency_bench.json"
MIXED_REQUESTS = 200
TOP_K = 4


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    idx = (len(ordered) - 1) * p
    lo, hi = int(idx), min(int(idx) + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (idx - lo)


def summarize(latencies_ms: list[float]) -> dict:
    return {
        "requests": len(latencies_ms),
        "mean_ms": round(statistics.mean(latencies_ms), 2),
        "p50_ms": round(percentile(latencies_ms, 0.50), 2),
        "p95_ms": round(percentile(latencies_ms, 0.95), 2),
        "max_ms": round(max(latencies_ms), 2),
    }


def clear_cache() -> None:
    rag_service.cache._store.clear()


def run_phase(client: TestClient, questions: list[str]) -> tuple[list[float], int]:
    latencies, hits = [], 0
    for q in questions:
        started = perf_counter()
        r = client.post("/api/query", json={"question": q, "top_k": TOP_K})
        latencies.append((perf_counter() - started) * 1000)
        r.raise_for_status()
        hits += 1 if r.json()["cached"] else 0
    return latencies, hits


def main() -> None:
    questions = [q["question"] for q in json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))["questions"]]
    client = TestClient(app)
    client.get("/")  # warm up the app itself (imports, first-request overhead)

    clear_cache()
    cold, cold_hits = run_phase(client, questions)
    warm, warm_hits = run_phase(client, questions)

    # Mixed workload: Zipf-like skew so a few questions dominate, as in real traffic.
    rng = random.Random(42)
    weights = [1 / (rank + 1) for rank in range(len(questions))]
    mixed_questions = rng.choices(questions, weights=weights, k=MIXED_REQUESTS)
    clear_cache()
    mixed, mixed_hits = run_phase(client, mixed_questions)

    results = {
        "llm_mode": "ollama" if rag_service.llm_client._ollama_available else "template_mock",
        "retrieval_config": f"{settings.chunk_strategy}+{settings.scoring}",
        "cache": "in-memory (per-process dict)",
        "phases": {
            "cold": {**summarize(cold), "cache_hit_rate": round(cold_hits / len(cold), 3)},
            "warm": {**summarize(warm), "cache_hit_rate": round(warm_hits / len(warm), 3)},
            "mixed_zipf": {**summarize(mixed), "cache_hit_rate": round(mixed_hits / len(mixed), 3)},
        },
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"llm_mode: {results['llm_mode']}  retrieval: {results['retrieval_config']}")
    print(f"{'phase':<12} {'n':>4} {'mean':>8} {'p50':>8} {'p95':>8} {'hit rate':>9}")
    for name, ph in results["phases"].items():
        print(f"{name:<12} {ph['requests']:>4} {ph['mean_ms']:>7.1f}ms {ph['p50_ms']:>7.1f}ms {ph['p95_ms']:>7.1f}ms {ph['cache_hit_rate']:>9.1%}")
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
