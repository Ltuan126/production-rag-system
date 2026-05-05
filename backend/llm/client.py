from __future__ import annotations

from collections.abc import Sequence
import requests

from retriever.vector_store import RetrievedChunk


class LLMClient:
    OLLAMA_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama2"
    USE_OLLAMA = True

    FALLBACK_PROMPTS = {
        "default": "Based on the provided context, here's what I found relevant to your question: {context}",
        "architecture": "The system architecture described in the documents shows: {context}",
        "how": "The process works as follows: {context}",
        "why": "The reason for this is: {context}",
    }

    def __init__(self):
        self._ollama_available = self._check_ollama()

    def _check_ollama(self) -> bool:
        """Check if Ollama is running and accessible."""
        if not self.USE_OLLAMA:
            return False
        try:
            r = requests.get(f"{self.OLLAMA_URL}/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def generate_answer(self, question: str, sources: Sequence[RetrievedChunk]) -> str:
        if not sources:
            return (
                "Chưa có tài liệu nào được lập chỉ mục cho câu hỏi này. "
                "Hãy thêm tài liệu vào data/documents để retriever có ngữ cảnh."
            )

        # Try Ollama first, fallback to mock if unavailable
        if self._ollama_available:
            try:
                return self._generate_with_ollama(question, sources)
            except Exception:
                pass

        # Fallback to mock response
        return self._generate_mock_answer(question, sources)

    def _generate_with_ollama(self, question: str, sources: Sequence[RetrievedChunk]) -> str:
        """Generate answer using local Ollama model."""
        # Build context from sources
        context_parts = []
        for source in sources[:3]:
            text = source.content.strip().replace("\n", " ")
            text = " ".join(text.split())
            context_parts.append(text[:120])
        context = " ".join(context_parts)

        # Create prompt for Ollama
        prompt = f"""Based on the following context, answer the question concisely in 1-2 sentences.

Context: {context}

Question: {question}

Answer:"""

        # Call Ollama API
        response = requests.post(
            f"{self.OLLAMA_URL}/api/generate",
            json={
                "model": self.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
            },
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()

    def _generate_mock_answer(self, question: str, sources: Sequence[RetrievedChunk]) -> str:
        """Generate mock answer when Ollama is unavailable."""
        context_parts = []
        for source in sources[:3]:
            text = source.content.strip().replace("\n", " ")
            text = " ".join(text.split())
            context_parts.append(text[:150])

        combined_context = " ".join(context_parts)
        template = self._select_template(question)
        return template.format(context=combined_context)

    def _select_template(self, question: str) -> str:
        q_lower = question.lower()
        if any(w in q_lower for w in ["how", "work", "process", "step"]):
            return self.FALLBACK_PROMPTS["how"]
        if any(w in q_lower for w in ["why", "reason", "because"]):
            return self.FALLBACK_PROMPTS["why"]
        if any(w in q_lower for w in ["architecture", "structure", "design"]):
            return self.FALLBACK_PROMPTS["architecture"]
        return self.FALLBACK_PROMPTS["default"]