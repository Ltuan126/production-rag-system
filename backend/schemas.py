from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=10)


class SourceChunk(BaseModel):
    source: str
    content: str
    score: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceChunk]
    top_k: int
    cached: bool = False
    took_ms: int


class DocumentInfo(BaseModel):
    path: str
    paragraphs: int
    characters: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    total_documents: int
    total_paragraphs: int
    total_characters: int