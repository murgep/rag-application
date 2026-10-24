import logging
from app.models.schemas import DocumentChunk
from app.rag.pipeline import RAGPipeline

class FakeRetriever:
    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        department: str | None = None,
        departments: frozenset[str] | set[str] | None = None,
    ):
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
class DepartmentTrackingRetriever:
    def __init__(self):
        self.received_department = None

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        department: str | None = None,
        departments: frozenset[str] | set[str] | None = None,
    ):
        self.received_department = department
        return []
class DepartmentsTrackingRetriever:
    def __init__(self):
        self.received_departments = None

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        department: str | None = None,
        departments: frozenset[str] | set[str] | None = None,
    ):
        self.received_departments = departments
        return []
class FakeGenerator:
    def generate(self, question: str, context: str):
        assert question == (
            "How many annual leave days do employees receive?"
        )
        assert "24 days of paid annual leave" in context

        return "Employees receive 24 days of paid annual leave."


class LowSimilarityRetriever:
    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        department: str | None = None,
        departments: frozenset[str] | set[str] | None = None,
    ):
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
class MultipleLowSimilarityRetriever:
    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        department: str | None = None,
        departments: frozenset[str] | set[str] | None = None,
    ):
        return [
            (
                DocumentChunk(
                    chunk_id="chunk-low-001",
                    document_id="unrelated-document-1",
                    text="Company principles and general information.",
                    page_number=1,
                    source="unrelated_1.pdf",
                    extraction_method="text",
                ),
                0.6712,
            ),
            (
                DocumentChunk(
                    chunk_id="chunk-low-002",
                    document_id="unrelated-document-2",
                    text="General document control information.",
                    page_number=1,
                    source="unrelated_2.pdf",
                    extraction_method="text",
                ),
                0.6508,
            ),
        ]
class FailingGenerator:
    def generate(self, question: str, context: str):
        raise AssertionError(
            "Generator should not be called when "
            "no chunks pass the similarity threshold."
        )


def test_rag_pipeline_forwards_department():
    retriever = DepartmentTrackingRetriever()
    generator = FailingGenerator()

    rag = RAGPipeline(
        retriever=retriever,
        generator=generator,
    )

    rag.ask(
        question="What is the leave policy?",
        department="HR",
    )

    assert retriever.received_department == "HR"
def test_rag_pipeline_forwards_authorized_departments():
    retriever = DepartmentsTrackingRetriever()
    generator = FailingGenerator()

    rag = RAGPipeline(
        retriever=retriever,
        generator=generator,
    )

    allowed_departments = frozenset({"HR", "Finance"})

    rag.ask(
        question="What is the company policy?",
        departments=allowed_departments,
    )

    assert retriever.received_departments == allowed_departments
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

    assert response.answer == (
        "Employees receive 24 days of paid annual leave."
    )

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

    assert response.answer == (
        "I don't have enough information in the provided "
        "documents to answer this question."
    )

    assert response.sources == []


def test_rag_pipeline_with_empty_retrieval_results():
    retriever = DepartmentTrackingRetriever()
    generator = FailingGenerator()

    rag = RAGPipeline(
        retriever=retriever,
        generator=generator,
    )

    response = rag.ask(
        question="What is the leave policy?",
    )

    assert response.answer == (
        "I don't have enough information in the provided "
        "documents to answer this question."
    )
    assert response.sources == []
def test_rag_pipeline_logs_request_id(caplog):
    retriever = FakeRetriever()
    generator = FakeGenerator()

    rag = RAGPipeline(
        retriever=retriever,
        generator=generator,
    )

    request_id = "test-request-123"

    with caplog.at_level(logging.INFO, logger="app.rag.pipeline"):
        rag.ask(
            question="How many annual leave days do employees receive?",
            request_id=request_id,
        )

    assert any(
        "RAG retrieval completed" in record.message
        and request_id in record.message
        for record in caplog.records
    )

    assert any(
        "RAG generation completed" in record.message
        and request_id in record.message
        for record in caplog.records
    )



def test_rag_pipeline_abstains_when_all_results_are_below_threshold():
    retriever = MultipleLowSimilarityRetriever()
    generator = FailingGenerator()

    rag = RAGPipeline(
        retriever=retriever,
        generator=generator,
    )

    response = rag.ask(
        question="What is the company's policy for working on Mars?",
        top_k=3,
        similarity_threshold=0.70,
    )

    assert response.answer == (
        "I don't have enough information in the provided "
        "documents to answer this question."
    )
    assert response.sources == []
