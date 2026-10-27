from unittest.mock import Mock

from app.api.dependencies import get_rag_pipeline
from app.rag.evidence_verifier import PromotionPeriodVerifier


def test_api_pipeline_uses_promotion_period_verifier(monkeypatch):
    monkeypatch.setattr(
        "app.api.dependencies.Embedder",
        Mock(return_value=Mock()),
    )
    monkeypatch.setattr(
        "app.api.dependencies.PostgreSQLVectorStore",
        Mock(return_value=Mock()),
    )
    monkeypatch.setattr(
        "app.api.dependencies.Retriever",
        Mock(return_value=Mock()),
    )
    monkeypatch.setattr(
        "app.api.dependencies.Generator",
        Mock(return_value=Mock()),
    )

    pipeline = get_rag_pipeline()

    assert isinstance(
        pipeline.evidence_verifier,
        PromotionPeriodVerifier,
    )