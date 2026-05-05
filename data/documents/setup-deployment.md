# Setup & Deployment Guide

## Local Development Setup

### Requirements
- Python 3.11 or higher
- Node.js 18+ with npm
- Git for version control

### Installation Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd production-rag-system
```

2. Create Python virtual environment:
```bash
python -m venv venv
```

3. Activate virtual environment:
- Windows: `venv\Scripts\Activate.ps1`
- Mac/Linux: `source venv/bin/activate`

4. Install backend dependencies:
```bash
pip install -r backend/requirements.txt
```

5. Install frontend dependencies:
```bash
cd frontend/react-app
npm install
cd ../..
```

## Running Locally

### Method 1: Two Terminals (Recommended for Development)

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend/react-app
npm run dev
```

Then open `http://localhost:3000` in your browser.

### Method 2: Docker Compose (Production-like)

Requires Docker and Docker Compose installed.

```bash
# Copy environment template
cp .env.example .env

# Build and start all services
docker-compose up --build

# Services will be available at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - Redis: localhost:6379
# - Chroma: localhost:8001
```

## Document Indexing

### Initial Setup
Sample document is included at `data/documents/sample.md`. It will be indexed automatically when the backend starts.

### Adding New Documents

1. Add files to `data/documents/`:
   - Supported formats: `.md`, `.txt`, `.rst`
   - Example: `data/documents/my-guide.md`

2. Trigger re-indexing via:
   - **UI button**: Click "Re-index documents" in the frontend
   - **API**: `curl -X POST http://localhost:8000/api/ingest`
   - **Direct**: `python -c "from services.indexer import indexer; indexer.build_index()"`

3. Index is stored at `data/index.json` (JSON format)

## Using Ollama for Better Responses

Ollama provides free, local LLM inference.

### Setup Ollama

1. Download from https://ollama.ai
2. Install and launch the application
3. Open terminal and run:
```bash
ollama run llama2
```

First run downloads the model (~4GB). Subsequent runs start faster.

### Supported Models

- **llama2** (default): Balanced performance, 7B parameters
- **mistral**: Faster inference, 7B parameters
- **neural-chat**: Good for conversations, 7B parameters

Once Ollama is running, the backend will automatically detect and use it.
If Ollama is not available, the system falls back to template-based responses.

## Environment Variables

Copy `.env.example` to `.env` for local development:

```bash
# LLM Configuration
OPENAI_API_KEY=  # Optional, leave empty for local mode
OPENAI_MODEL=gpt-4o-mini

# Vector Database
VECTOR_DB_PROVIDER=chroma
CHROMA_HOST=chroma
CHROMA_PORT=8000

# Cache
REDIS_HOST=redis
REDIS_PORT=6379

# App Runtime
BACKEND_PORT=8000
FRONTEND_PORT=3000
VITE_BACKEND_URL=http://localhost:8000
```

## Building for Production

### Backend

```bash
cd backend
pip install -r requirements.txt

# Run with production ASGI server
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Frontend

```bash
cd frontend/react-app

# Build optimized bundle
npm run build

# Preview production build
npm run preview
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend fails to start | Check Python version (3.11+), reinstall requirements |
| Frontend won't load | Clear node_modules, run `npm install` again |
| Port already in use | Change port: `--port 8001` or kill existing process |
| Ollama not connecting | Ensure Ollama is running; backend auto-fallbacks to mock |
| No documents indexed | Add files to `data/documents/`, click re-index button |

