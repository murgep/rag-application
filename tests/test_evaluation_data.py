from tests.evaluation_data import (
    EVALUATION_CASES,
    UNSUPPORTED_EVALUATION_CASES,
)

def test_evaluation_cases_have_required_fields():
    for case in EVALUATION_CASES:
        assert case["id"]
        assert case["question"]
        assert case["relevant_chunk_ids"]


def test_evaluation_case_ids_are_unique():
    case_ids = [case["id"] for case in EVALUATION_CASES]
    assert len(case_ids) == len(set(case_ids))


def test_relevant_chunk_ids_are_unique_per_case():
    for case in EVALUATION_CASES:
        chunk_ids = case["relevant_chunk_ids"]
        assert len(chunk_ids) == len(set(chunk_ids))

def test_unsupported_evaluation_cases_have_required_fields():
    for case in UNSUPPORTED_EVALUATION_CASES:
        assert case["id"]
        assert case["question"]


def test_unsupported_case_ids_are_unique():
    case_ids = [case["id"] for case in UNSUPPORTED_EVALUATION_CASES]
    assert len(case_ids) == len(set(case_ids))