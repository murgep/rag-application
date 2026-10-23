
from app.embeddings.embedder import Embedder
from app.retrieval.pg_vector_store import PostgreSQLVectorStore
from app.retrieval.retriever import Retriever
from tests.evaluation_data import EVALUATION_CASES
from tests.test_retrieval_metrics import (
    hit_at_k,
    reciprocal_rank,
    relevance_at_ranks,
)


def main():
    if not EVALUATION_CASES:
        raise ValueError("Evaluation dataset is empty.")

    retriever = Retriever(
        embedder=Embedder(),
        vector_store=PostgreSQLVectorStore(),
    )

    hit_scores = []
    reciprocal_ranks = []

    for case in EVALUATION_CASES:
        results = retriever.retrieve(
            query=case["question"],
            top_k=3,
        )

        retrieved_ids = [
            chunk.chunk_id for chunk, _ in results
        ]

        relevance = relevance_at_ranks(
            retrieved_chunk_ids=retrieved_ids,
            relevant_chunk_ids=case["relevant_chunk_ids"],
        )

        hit = hit_at_k(relevance, 3)
        rr = reciprocal_rank(relevance)

        missing_relevant_ids = [
            chunk_id
            for chunk_id in case["relevant_chunk_ids"]
            if chunk_id not in retrieved_ids
        ]

        # Record every question's scores, regardless of missing chunks.
        hit_scores.append(hit)
        reciprocal_ranks.append(rr)

        print(f"\n{case['id']}: {case['question']}")
        print(f"Retrieved chunks: {retrieved_ids}")
        print(f"Relevance: {relevance}")
        print(f"Hit@3: {hit}")
        print(f"Reciprocal rank: {rr:.3f}")

        if missing_relevant_ids:
            print(
                "Relevant chunks not retrieved in top 3: "
                f"{missing_relevant_ids}"
            )
        else:
            print("All known relevant chunks retrieved in top 3.")

    count = len(EVALUATION_CASES)

    print("\n" + "=" * 60)
    print(f"Questions evaluated: {count}")
    print(f"Hit@3: {sum(hit_scores) / count:.3f}")
    print(f"MRR: {sum(reciprocal_ranks) / count:.3f}")


if __name__ == "__main__":
    main()
