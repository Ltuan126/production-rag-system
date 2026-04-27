from cache.response_cache import ResponseCache
from llm.client import LLMClient
from retriever.vector_store import VectorStoreRetriever
from schemas import QueryResponse, SourceChunk


class RagService:
    def __init__(self) -> None:
        self.retriever = VectorStoreRetriever()
        self.llm_client = LLMClient()
        self.cache = ResponseCache()

    async def answer(self, question: str, top_k: int) -> QueryResponse:
        cache_key = f"query:{top_k}:{question.strip().lower()}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        retrieved = self.retriever.search(question=question, top_k=top_k)
        answer_text = self.llm_client.generate_answer(question=question, sources=retrieved)
        response = QueryResponse(
            question=question,
            answer=answer_text,
            sources=[
                SourceChunk(source=item.source, content=item.content, score=item.score)
                for item in retrieved
            ],
        )
        await self.cache.set(cache_key, response)
        return response


rag_service = RagService()