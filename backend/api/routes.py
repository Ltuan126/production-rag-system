from fastapi import APIRouter

from schemas import DocumentListResponse, QueryRequest, QueryResponse
from services.document_service import DocumentService
from services.rag_service import rag_service
from services.indexer import indexer
from fastapi import BackgroundTasks


router = APIRouter()
document_service = DocumentService()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/documents", response_model=DocumentListResponse)
async def documents() -> DocumentListResponse:
    documents = document_service.list_documents()
    return DocumentListResponse(
        documents=[
            {
                "path": document.path,
                "paragraphs": document.paragraphs,
                "characters": document.characters,
            }
            for document in documents
        ],
        total_documents=len(documents),
        total_paragraphs=sum(document.paragraphs for document in documents),
        total_characters=sum(document.characters for document in documents),
    )


@router.post("/ingest")
async def ingest(background_tasks: BackgroundTasks):
    """Trigger rebuilding the local index (runs in background)."""
    # schedule index build in background
    background_tasks.add_task(indexer.build_index)
    return {"status": "scheduled"}


@router.post("/query", response_model=QueryResponse)
async def query(payload: QueryRequest) -> QueryResponse:
    return await rag_service.answer(question=payload.question, top_k=payload.top_k)