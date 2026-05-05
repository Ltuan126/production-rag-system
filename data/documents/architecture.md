# Project Architecture

The Production RAG System is built with a modular architecture that separates concerns:

## Backend Architecture

### API Layer
The FastAPI backend exposes RESTful endpoints:
- `GET /` - Health check
- `GET /api/health` - API status
- `GET /api/documents` - List loaded documents with stats
- `POST /api/query` - Submit query and get answer with sources
- `POST /api/ingest` - Trigger document re-indexing

### Retriever Module
The retriever uses token-based search to find relevant documents:
1. Loads all documents from `data/documents/`
2. Splits into paragraphs (separated by blank lines)
3. Tokenizes both query and documents
4. Ranks by token overlap using Counter
5. Returns top-k results with relevance scores

### LLM Module
The LLM client has two modes:
- **Production mode**: Attempts to connect to local Ollama at localhost:11434
- **Fallback mode**: Uses template-based responses when LLM unavailable
- Automatically detects question type (how/why/architecture) to select template

### Cache Layer
In-memory response cache stores recent query results to reduce re-processing.

## Frontend Architecture

### React Components
Single-page application built with React + Vite:
- **Hero section**: Title and document statistics
- **Query panel**: Text input form for questions
- **Answer panel**: Displays LLM response and retrieved source cards

### Data Flow
1. User types question and clicks "Run retrieval"
2. Frontend sends POST to `/api/query` with question + top_k
3. Backend retrieves relevant documents and generates answer
4. Frontend receives QueryResponse (question, answer, sources array)
5. Displays answer text and source cards with relevance scores

### Styling
Built with CSS Grid and Flexbox for responsive layout.
Includes dark mode consideration with CSS variables.

## Deployment Considerations

### Local Development
- Backend: FastAPI with uvicorn reload
- Frontend: Vite dev server with HMR
- LLM: Optional local Ollama or mock responses

### Production Deployment
- Docker containers for reproducibility
- Backend API behind reverse proxy
- Frontend served as static build
- Persistent storage for indexed documents
