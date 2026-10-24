
import logging
import time

from app.generation.generator import Generator
from app.models.schemas import RAGResponse, RAGSource
from app.retrieval.retriever import Retriever
from app.rag.evidence_verifier import (
    ABSTENTION_ANSWER,
    AlwaysSufficientVerifier,
    EvidenceVerifier,
)

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Orchestrates retrieval and generation."""

    def __init__(
        self,
        retriever: Retriever,
        generator: Generator,
        evidence_verifier: EvidenceVerifier | None = None,
    ):
        self.retriever = retriever
        self.generator = generator
        self.evidence_verifier = (
evidence_verifier or AlwaysSufficientVerifier()
)

    def ask(
        self,
        question: str,
        top_k: int = 3,
        similarity_threshold: float = 0.60,
        department: str | None = None,
        request_id: str | None = None,
        departments: frozenset[str] | set[str] | None = None,
    ) -> RAGResponse:
        if not question.strip():
            raise ValueError("Question cannot be empty.")

        if department is not None and departments is not None:
            raise ValueError(
                "Provide either department or departments, not both."
            )

        retrieval_start = time.perf_counter()

        if departments is not None:
            results = self.retriever.retrieve(
                query=question,
                top_k=top_k,
                departments=departments,
            )
        else:
            results = self.retriever.retrieve(
                query=question,
                top_k=top_k,
                department=department,
            )

        retrieval_duration = time.perf_counter() - retrieval_start

        logger.info(
            "RAG retrieval completed; request_id=%s "
            "duration=%.3f seconds retrieved=%d chunks",
            request_id or "-",
            retrieval_duration,
            len(results),
        )

        filtered_results = [
            (chunk, score)
            for chunk, score in results
            if score >= similarity_threshold
        ]

        if filtered_results and not self.evidence_verifier.is_sufficient(
    question=question,
    chunks=[chunk for chunk, _ in filtered_results],
):
            return RAGResponse(
        answer=ABSTENTION_ANSWER,
        sources=[],
    )

        if not filtered_results:
            return RAGResponse(
        answer=ABSTENTION_ANSWER,
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

        generation_start = time.perf_counter()

        answer = self.generator.generate(
            question=question,
            context=context,
        )

        generation_duration = time.perf_counter() - generation_start

        logger.info(
            "RAG generation completed; request_id=%s "
            "duration=%.3f seconds",
            request_id or "-",
            generation_duration,
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
