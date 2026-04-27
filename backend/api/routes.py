from fastapi import APIRouter

from schemas import QueryRequest, QueryResponse
from services.rag_service import rag_service


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/query", response_model=QueryResponse)
async def query(payload: QueryRequest) -> QueryResponse:
    return await rag_service.answer(question=payload.question, top_k=payload.top_k)