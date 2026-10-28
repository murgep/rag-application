
from app.embeddings.embedder import Embedder
from app.retrieval.pg_vector_store import PostgreSQLVectorStore
from app.retrieval.retriever import Retriever
from tests.evaluation_data import UNSUPPORTED_EVALUATION_CASES


SIMILARITY_THRESHOLD = 0.70


def main():
    retriever = Retriever(
        embedder=Embedder(),
        vector_store=PostgreSQLVectorStore(),
    )

    for case in UNSUPPORTED_EVALUATION_CASES:
        results = retriever.retrieve(
            query=case["question"],
            top_k=3,
        )

        print(f"\n{case['id']}: {case['question']}")

        if not results:
            print("Retrieved chunks: none")
            print("Decision at threshold: ABSTAIN")
            continue

        for rank, (chunk, score) in enumerate(results, start=1):
            print(
                f"Rank {rank} | similarity={score:.4f} "
                f"| chunk_id={chunk.chunk_id}"
            )

        highest_score = results[0][1]
        decision = (
            "WOULD ANSWER"
            if highest_score >= SIMILARITY_THRESHOLD
            else "WOULD ABSTAIN"
        )

        print(f"Highest similarity: {highest_score:.4f}")
        print(f"Decision at threshold {SIMILARITY_THRESHOLD}: {decision}")


if __name__ == "__main__":
    main()
