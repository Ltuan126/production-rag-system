# Production RAG System

Lightweight Retrieval-Augmented Generation (RAG) starter: a minimal full-stack app
for ingesting documents, building a local index, retrieving relevant chunks, and
generating answers.

Prerequisites
-------------
- Docker & Docker Compose (for production compose)
- Node.js 20+ and npm (for frontend dev)
- Python 3.11+ (for backend dev)

Local development (fast)
------------------------
1. Create & activate a Python virtualenv

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

2. Install backend dependencies

```powershell
pip install -r backend/requirements.txt
```

3. Install frontend dependencies

```powershell
cd frontend/react-app
npm ci
cd ../..
```

4. Run backend + frontend in two terminals

```powershell
# Terminal 1
cd backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2
cd frontend/react-app
npm run dev
```

Production (Docker Compose)
--------------------------
This repository includes `docker-compose.prod.yml` which builds the backend image
and serves the frontend `dist` via Nginx (`Dockerfile.prod` + `nginx.conf`).

To run the production compose locally:

```bash
docker compose -f docker-compose.prod.yml up --build -d

# Frontend: http://localhost:3000
# Backend: http://localhost:8000/api/
```

Notes
-----
- The production frontend is a static build served by Nginx; the dev Dockerfile
	used previously ran the Vite dev server and is not production-ready.
- `docker-compose.prod.yml` includes `redis` and `chroma` services used by the
	retriever; you can remove or replace them depending on your target infra.

CI (GitHub Actions)
--------------------
We added a minimal CI workflow at `.github/workflows/ci.yml` that runs on pushes
and PRs to `main`. It performs:

- Backend: install `backend/requirements.txt` and run `backend/ci_smoke.py`.
- Frontend: `npm ci` and `npm run build` in `frontend/react-app`.

This CI is designed for learning/testing only (no secrets). For real deploys
you'll add registry credentials and deployment steps.

Troubleshooting
---------------
- If the frontend can't reach the backend in Docker Compose, check `VITE_BACKEND_URL`
	in `docker-compose.prod.yml` or use `docker compose ps` to confirm service names.
- If tests fail in CI, reproduce locally by running the same commands listed in
	`.github/workflows/ci.yml`.

If you want, I can push the branch and open a PR, or add a deploy step to push
images to Docker Hub / ACR (you'll need to provide registry credentials).

