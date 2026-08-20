from app.generation.generator import Generator
from app.models.schemas import RAGResponse, RAGSource
from app.retrieval.retriever import Retriever


class RAGPipeline:
    """
    Orchestrates retrieval and generation.
    """

    def __init__(
        self,
        retriever: Retriever,
        generator: Generator,
    ):
        self.retriever = retriever
        self.generator = generator

    def ask(
            self,
            question: str,
            top_k: int = 3,
            similarity_threshold: float = 0.60,
    ) -> RAGResponse:

        if not question.strip():
            raise ValueError(
                "Question cannot be empty."
            )

        results = self.retriever.retrieve(
            query=question,
            top_k=top_k,
        )

        filtered_results = [
            (chunk, score)
            for chunk, score in results
            if score >= similarity_threshold
        ]

        if not filtered_results:
            return RAGResponse(
                answer=(
                    "I don't have enough information in the provided "
                    "documents to answer this question."
                ),
                sources=[],
            )

        context_parts = []

        for chunk, score in filtered_results:
            context_parts.append(
                f"""
    Document: {chunk.document_id}
    Page: {chunk.page_number}

    {chunk.text}
    """
            )

        context = "\n".join(context_parts)

        answer = self.generator.generate(
            question=question,
            context=context,
        )

        sources = [
            RAGSource(
                document_id=chunk.document_id,
                source=chunk.source,
                page_number=chunk.page_number,
                similarity=score,
            )
            for chunk, score in filtered_results
        ]

        return RAGResponse(
            answer=answer,
            sources=sources,
        )