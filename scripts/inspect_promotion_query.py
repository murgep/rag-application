
from app.embeddings.embedder import Embedder
from app.retrieval.pg_vector_store import PostgreSQLVectorStore
from app.retrieval.retriever import Retriever


def main():
    retriever = Retriever(
        embedder=Embedder(),
        vector_store=PostgreSQLVectorStore(),
    )

    query = (
        "What minimum number of months must an employee work "
        "before becoming eligible for promotion?"
    )

    results = retriever.retrieve(query=query, top_k=3)

    for rank, (chunk, score) in enumerate(results, start=1):
        print(f"\nRank: {rank}")
        print(f"Similarity: {score:.4f}")
        print(f"Chunk ID: {chunk.chunk_id}")
        print(f"Source: {chunk.source}")
        print(f"Page: {chunk.page_number}")
        print(f"Text: {chunk.text}")


if __name__ == "__main__":
    main()
