# Production RAG System

A small, **evaluated** Retrieval-Augmented Generation (RAG) pipeline: FastAPI
backend, React frontend, lexical retrieval over locally indexed documents, and
response caching. Retrieval configurations were benchmarked against a
hand-labeled question set — switching from paragraph chunks + raw token overlap
to fixed 512-char chunks + BM25 raised **recall@5 from 0.78 to 0.97** and
**MRR@10 from 0.68 to 0.85**, and the response cache cuts p95 latency from
**25ms to 8ms** at an **84.5% hit rate** under a skewed query workload.

It is intentionally lexical: there are no embeddings or vector database in the
retrieval path (see [Design rationale](#design-rationale) and
[Known limitations](#known-limitations)).

## Retrieval evaluation

Ground truth is [eval/questions.json](eval/questions.json): 32 questions over
the 3 corpus documents, each labeled with the source document and a literal
answer span. A retrieved chunk counts as relevant if it comes from the expected
document **and** contains the answer span — span containment (rather than chunk
ids) lets the same labels score different chunking strategies fairly.

Six configs were compared (3 chunkers × 2 scorers), run with
`python eval/run_retrieval_eval.py`; full results in
[data/processed/retrieval_eval.json](data/processed/retrieval_eval.json):

| config | chunks | recall@1 | recall@3 | recall@5 | MRR@10 |
|---|---|---|---|---|---|
| paragraph + overlap *(old default)* | 67 | 0.56 | 0.78 | 0.78 | 0.676 |
| paragraph + BM25 | 67 | 0.66 | 0.78 | 0.84 | 0.732 |
| fixed 256 + overlap | 33 | 0.66 | 0.81 | 0.84 | 0.738 |
| fixed 256 + BM25 | 33 | 0.72 | 0.81 | 0.84 | 0.781 |
| fixed 512 + overlap | 17 | 0.59 | 0.84 | 0.94 | 0.733 |
| **fixed 512 + BM25** *(new default)* | 17 | **0.78** | **0.91** | **0.97** | **0.847** |

Takeaways:

- **BM25 beats raw token-overlap at every chunk size.** Raw overlap counts
  reward chunks that repeat common words ("the", "backend"); BM25's IDF
  weighting and length normalization fix both.
- **Larger chunks help lexical scoring here** — markdown list items become
  tiny, low-signal paragraphs, while 512-char windows keep a question's
  vocabulary and its answer in the same chunk.
- **Caveat:** with 512-char chunks the corpus is only 17 chunks, so top-5
  covers ~30% of it and recall@5 is partly inflated by corpus size. Recall@1
  (0.56 → 0.78) and MRR are the fairer comparisons, and both agree.

The winning config is the production default
([backend/settings.py](backend/settings.py)); the old behavior is reproducible
with `CHUNK_STRATEGY=paragraph SCORING=overlap`.

## Design rationale

**Why lexical retrieval instead of embeddings?** The corpus is three markdown
docs (~17 chunks). At this scale an embedding model + vector DB adds deployment
weight (model download, Chroma service, index sync) without measurable quality
headroom over BM25 — and the eval harness exists precisely so that claim can be
tested rather than assumed. If the corpus grows or the eval shows lexical
recall degrading on paraphrased questions (its known weak spot — see
limitations), swapping the scorer behind `VectorStoreRetriever.search()` is the
intended upgrade path.

**Why fixed-size chunking?** Measured, not assumed: paragraph splitting looked
natural but scored worst, because markdown lists fragment into low-signal
chunks (see table above).

**Why an in-process cache?** Queries are repetitive (the mixed-workload
benchmark shows 84.5% hit rate under Zipf-like traffic) and responses are
deterministic for a given index, so exact-match caching is safe and nearly
free. It is a per-process Python dict, **not Redis** — see limitations.

## Latency & caching

Measured end-to-end through the FastAPI app (`python eval/run_latency_bench.py`,
results in [data/processed/latency_bench.json](data/processed/latency_bench.json)):

| phase | requests | mean | p50 | p95 | cache hit rate |
|---|---|---|---|---|---|
| cold (empty cache) | 32 | 6.8ms | 3.2ms | 25.2ms | 0% |
| warm (repeat queries) | 32 | 3.6ms | 2.7ms | 8.4ms | 100% |
| mixed (Zipf workload, 200 req) | 200 | 3.7ms | 2.3ms | 13.8ms | 84.5% |

**Caveat:** these runs used the template-mock LLM (Ollama not running), so they
measure routing + retrieval + caching, not generation. With a real LLM,
generation dominates (seconds), which makes the cache's value much larger and
these absolute numbers much smaller than real response times. The benchmark
records which LLM mode was active in its output file.

## Known limitations

Observed on the eval set (per-question ranks are in
`data/processed/retrieval_eval.json`), not hypothetical:

- **Vocabulary mismatch breaks lexical retrieval.** "How is the frontend
  *deployed*?" misses the chunk that says "*served* as static build" (q10, the
  one remaining miss at the best config). No amount of BM25 tuning fixes a
  synonym gap; this is the concrete argument for adding an embedding or hybrid
  scorer later.
- **The tokenizer keeps underscores**, so `OPENAI_MODEL` is one token that the
  query "openai model" never matches (q28). Env-var and identifier lookups only
  work quoted verbatim.
- **Version numbers tokenize into noisy digits** — "Python 3.11" becomes
  `3`, `11`, which match unrelated chunks (q14 ranked 4th).
- **Fixed-size chunks can split an answer across a boundary**; the 25% window
  overlap reduces but does not eliminate this.
- **The corpus and eval set are small** (3 documents, 32 questions). Metric
  differences of a few points are within noise; the config ranking was stable
  across chunk sizes, but don't over-read any single cell of the table.
- **Out-of-scope questions fail soft but unhelpfully**: anything with zero
  token overlap returns no sources and a canned "no documents indexed" message
  rather than a calibrated "I don't know".
- **The cache is in-memory per process** — not shared across workers, not
  persistent, no TTL or invalidation on re-index. `docker-compose` starts Redis
  and Chroma containers, but **the application code currently uses neither**;
  they are scaffolding for the intended upgrade path, and honest reading of
  this repo should treat them as unused.
- **Answer generation is template-based unless Ollama is running locally**;
  answer *quality* is unevaluated — the eval covers retrieval only.

## Reproduce the numbers

```bash
pip install -r backend/requirements.txt
python eval/run_retrieval_eval.py    # writes data/processed/retrieval_eval.{json,csv}
python eval/run_latency_bench.py     # writes data/processed/latency_bench.json
```

CI runs the smoke test plus a retrieval-correctness check (a known query must
return its expected source document) on every push — see
[.github/workflows/ci.yml](.github/workflows/ci.yml).

## Local development

Prerequisites: Python 3.11+, Node.js 20+, Docker (only for the production compose).

```powershell
# Backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
cd backend
python -m uvicorn main:app --reload --port 8000

# Frontend (second terminal)
cd frontend/react-app
npm ci
npm run dev
```

Add documents to `data/documents/` (`.md`, `.txt`, `.rst`) and re-index via the
UI button or `curl -X POST http://localhost:8000/api/ingest`. If
[Ollama](https://ollama.ai) is running locally, answers are generated with
`llama2`; otherwise a template fallback is used.

## Production (Docker Compose)

```bash
docker compose -f docker-compose.prod.yml up --build -d
# Frontend: http://localhost:3000   Backend: http://localhost:8000/api/
```

The production frontend is a static Vite build served by Nginx. The compose
file also starts `redis` and `chroma` services, which the current code does not
use (see limitations); remove them or wire them in depending on your target.

## Troubleshooting

- Frontend can't reach the backend in compose: check `VITE_BACKEND_URL` in
  `docker-compose.prod.yml` and `docker compose ps` for service names.
- CI failures: reproduce locally with the same commands as in
  `.github/workflows/ci.yml`.
- Retrieval quality looks off after editing documents: re-run
  `python eval/run_retrieval_eval.py` — the gold spans in
  `eval/questions.json` must still exist verbatim in the corpus, and the
  harness fails loudly if they don't.
