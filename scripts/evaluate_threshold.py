
from app.embeddings.embedder import Embedder
from app.retrieval.pg_vector_store import PostgreSQLVectorStore
from app.retrieval.retriever import Retriever
from tests.evaluation_data import (
    EVALUATION_CASES,
    UNSUPPORTED_EVALUATION_CASES,
)


SIMILARITY_THRESHOLD = 0.70
TOP_K = 3


def evaluate_cases(retriever, cases, expected_answerable):
    outcomes = {
        "correct_answerable": 0,
        "false_abstention": 0,
        "correct_abstention": 0,
        "false_accept": 0,
    }

    for case in cases:
        results = retriever.retrieve(
            query=case["question"],
            top_k=TOP_K,
        )

        highest_score = results[0][1] if results else None
        would_answer = (
            highest_score is not None
            and highest_score >= SIMILARITY_THRESHOLD
        )

        if expected_answerable:
            outcome = (
                "correct_answerable"
                if would_answer
                else "false_abstention"
            )
        else:
            outcome = (
                "false_accept"
                if would_answer
                else "correct_abstention"
            )

        outcomes[outcome] += 1

        print(f"\nCase: {case['id']}")
        print(f"Question: {case['question']}")
        print(
            f"Highest similarity: "
            f"{highest_score:.4f}"
            if highest_score is not None
            else "Highest similarity: no results"
        )
        print(
            f"Threshold decision: "
            f"{'WOULD ANSWER' if would_answer else 'WOULD ABSTAIN'}"
        )
        print(f"Evaluation outcome: {outcome}")

    return outcomes


def main():
    retriever = Retriever(
        embedder=Embedder(),
        vector_store=PostgreSQLVectorStore(),
    )

    print(f"Similarity threshold: {SIMILARITY_THRESHOLD}")
    print(f"Top K: {TOP_K}")

    answerable_outcomes = evaluate_cases(
        retriever,
        EVALUATION_CASES,
        expected_answerable=True,
    )

    unsupported_outcomes = evaluate_cases(
        retriever,
        UNSUPPORTED_EVALUATION_CASES,
        expected_answerable=False,
    )

    print("\n" + "=" * 60)
    print("ANSWERABLE CASES")
    print(f"Correctly passed threshold: {answerable_outcomes['correct_answerable']}")
    print(f"False abstentions: {answerable_outcomes['false_abstention']}")

    print("\nUNSUPPORTED CASES")
    print(f"Correctly abstained: {unsupported_outcomes['correct_abstention']}")
    print(f"False accepts: {unsupported_outcomes['false_accept']}")


if __name__ == "__main__":
    main()
