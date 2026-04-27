# Production RAG System

This sample document describes the initial architecture of the project.

The backend is a FastAPI service that exposes query and health endpoints. The retriever scans local documents in `data/documents`, ranks chunks by token overlap, and returns the best matches for the question.

The frontend is a React application that submits questions to the backend and renders the generated answer together with source snippets.