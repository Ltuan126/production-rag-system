from __future__ import annotations

from collections.abc import Sequence

from retriever.vector_store import RetrievedChunk


class LLMClient:
    def generate_answer(self, question: str, sources: Sequence[RetrievedChunk]) -> str:
        if not sources:
            return (
                "Chưa có tài liệu nào được lập chỉ mục cho câu hỏi này. "
                "Hãy thêm tài liệu vào data/documents để retriever có ngữ cảnh."
            )

        lead = sources[0]
        summary = lead.content.strip().replace("\n", " ")
        return (
            f"Dựa trên các tài liệu đã nạp, câu trả lời cho '{question}' hiện được ước lượng từ ngữ cảnh gần nhất. "
            f"Điểm khởi đầu tốt nhất là nguồn {lead.source}: {summary[:280]}"
        )