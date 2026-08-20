from app.models.schemas import DocumentChunk
from app.rag.pipeline import RAGPipeline


class FakeRetriever:
    def retrieve(self, query: str, top_k: int = 3):
        return [
            (
                DocumentChunk(
                    chunk_id="chunk-001",
                    document_id="hr-policy",
                    text="Employees receive 24 days of paid annual leave.",
                    page_number=2,
                    source="hr_policy.pdf",
                    extraction_method="text",
                ),
                0.95,
            )
        ]


class FakeGenerator:
    def generate(self, question: str, context: str):
        assert question == (
            "How many annual leave days do employees receive?"
        )

        assert "24 days of paid annual leave" in context

        return "Employees receive 24 days of paid annual leave."


class LowSimilarityRetriever:
    def retrieve(self, query: str, top_k: int = 3):
        return [
            (
                DocumentChunk(
                    chunk_id="chunk-999",
                    document_id="unrelated-document",
                    text="This document contains unrelated information.",
                    page_number=10,
                    source="unrelated.pdf",
                    extraction_method="text",
                ),
                0.30,
            )
        ]


class FailingGenerator:
    def generate(self, question: str, context: str):
        raise AssertionError(
            "Generator should not be called when "
            "no chunks pass the similarity threshold."
        )


def test_rag_pipeline():

    retriever = FakeRetriever()
    generator = FakeGenerator()

    rag = RAGPipeline(
        retriever=retriever,
        generator=generator,
    )

    response = rag.ask(
        "How many annual leave days do employees receive?"
    )

    print("\nRAG Answer:")
    print(response.answer)

    print("\nSources:")

    for source in response.sources:
        print(
            f"Document ID: {source.document_id}"
        )
        print(
            f"Source: {source.source}"
        )
        print(
            f"Page: {source.page_number}"
        )
        print(
            f"Similarity: {source.similarity}"
        )

    # Verify generated answer
    assert response.answer == (
        "Employees receive 24 days of paid annual leave."
    )

    # Verify source information
    assert len(response.sources) == 1

    assert response.sources[0].document_id == "hr-policy"
    assert response.sources[0].source == "hr_policy.pdf"
    assert response.sources[0].page_number == 2
    assert response.sources[0].similarity == 0.95


def test_rag_pipeline_with_no_relevant_results():

    retriever = LowSimilarityRetriever()
    generator = FailingGenerator()

    rag = RAGPipeline(
        retriever=retriever,
        generator=generator,
    )

    response = rag.ask(
        question="What is the company's Mars policy?",
        similarity_threshold=0.70,
    )

    print("\nFallback Answer:")
    print(response.answer)

    print("\nSources:")
    print(response.sources)

    # Verify safe fallback
    assert response.answer == (
        "I don't have enough information in the provided "
        "documents to answer this question."
    )

    # No sources should be returned
    assert response.sources == []