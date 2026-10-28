import logging
from app.models.schemas import DocumentChunk
from app.rag.pipeline import RAGPipeline
from app.rag.evidence_verifier import PromotionPeriodVerifier

class FakeRetriever:
    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        department: str | None = None,
        departments: frozenset[str] | set[str] | None = None,
        request_id: str | None = None,
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

class MultiChunkFakeRetriever:
    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        department: str | None = None,
        departments: frozenset[str] | set[str] | None = None,
        request_id: str | None = None,
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
            ),
            (
                DocumentChunk(
                    chunk_id="chunk-002",
                    document_id="hr-policy",
                    text="Annual leave requests should be submitted in advance.",
                    page_number=3,
                    source="hr_policy.pdf",
                    extraction_method="text",
                ),
                0.88,
            ),
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
        request_id: str | None = None,
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
        request_id: str | None = None,
    ):
        self.received_departments = departments
        return []
class FakeGenerator:
    def generate(
        self,
        question: str,
        context: str,
        request_id: str | None = None,
    ):
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
        request_id: str | None = None,
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
        request_id: str | None = None,
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

class PromotionRelatedRetriever:
    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        department: str | None = None,
        departments: frozenset[str] | set[str] | None = None,
        request_id: str | None = None,
    ):
        return [
            (
                DocumentChunk(
                    chunk_id="promotion-chunk-001",
                    document_id="employee-handbook",
                    text=(
                        "Promotion decisions consider demonstrated "
                        "capability at the next level, sustained "
                        "performance, role availability, and approval "
                        "from the department head. Time in role alone "
                        "does not guarantee promotion."
                    ),
                    page_number=4,
                    source="employee_handbook.pdf",
                    extraction_method="text",
                ),
                0.7408,
            )
        ]


class FailingGenerator:
    def generate(
        self,
        question: str,
        context: str,
        request_id: str | None = None,
    ):
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
def test_rag_pipeline_does_not_invent_promotion_eligibility_period():
    retriever = PromotionRelatedRetriever()
    generator = FailingGenerator()

    rag = RAGPipeline(
        retriever=retriever,
        generator=generator,
        evidence_verifier=PromotionPeriodVerifier(),
    )

    response = rag.ask(
        question=(
            "What minimum number of months must an employee "
            "work before becoming eligible for promotion?"
        ),
        top_k=3,
        similarity_threshold=0.70,
    )

    assert response.answer == (
        "I don't have enough information in the provided "
        "documents to answer this question."
    )
    assert response.sources == []


def test_rag_pipeline_returns_sources_for_each_retrieved_chunk():
    rag = RAGPipeline(
        retriever=MultiChunkFakeRetriever(),
        generator=FakeGenerator(),
    )

    response = rag.ask(
        question="How many annual leave days do employees receive?",
        top_k=3,
        similarity_threshold=0.70,
    )

    assert len(response.sources) == 2

    assert response.sources[0].document_id == "hr-policy"
    assert response.sources[0].source == "hr_policy.pdf"
    assert response.sources[0].page_number == 2
    assert response.sources[0].similarity == 0.95

    assert response.sources[1].document_id == "hr-policy"
    assert response.sources[1].source == "hr_policy.pdf"
    assert response.sources[1].page_number == 3
    assert response.sources[1].similarity == 0.88
