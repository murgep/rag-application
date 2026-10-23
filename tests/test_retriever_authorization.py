from app.retrieval.retriever import Retriever


class FakeEmbedder:
    def embed_text(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class TrackingVectorStore:
    def __init__(self):
        self.received_department = None
        self.received_departments = None

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        department: str | None = None,
        departments: frozenset[str] | set[str] | None = None,
    ):
        self.received_department = department
        self.received_departments = departments
        return []


def test_retriever_forwards_authorized_departments():
    vector_store = TrackingVectorStore()
    retriever = Retriever(
        embedder=FakeEmbedder(),
        vector_store=vector_store,
    )

    allowed_departments = frozenset({"HR", "Finance"})

    results = retriever.retrieve(
        query="What is the company policy?",
        departments=allowed_departments,
    )

    assert results == []
    assert vector_store.received_departments == allowed_departments
    assert vector_store.received_department is None
