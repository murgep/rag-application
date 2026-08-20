from app.embeddings.embedder import Embedder
from app.generation.generator import Generator
from app.rag.pipeline import RAGPipeline
from app.retrieval.pg_vector_store import PostgreSQLVectorStore
from app.retrieval.retriever import Retriever


def test_real_rag():

    # 1. Create embedding component
    embedder = Embedder()

    # 2. Create PostgreSQL + pgvector store
    vector_store = PostgreSQLVectorStore()

    # 3. Create retriever
    retriever = Retriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    # 4. Create generator
    generator = Generator()

    # 5. Create complete RAG pipeline
    rag = RAGPipeline(
        retriever=retriever,
        generator=generator,
    )

    # 6. Ask a real question
    question = "How many days of annual leave do employees receive?"

    response = rag.ask(
        question=question,
        top_k=3,
    )

    print("\n" + "=" * 60)
    print("QUESTION")
    print("=" * 60)
    print(question)

    print("\n" + "=" * 60)
    print("RAG ANSWER")
    print("=" * 60)
    print(response.answer)

    print("\n" + "=" * 60)
    print("SOURCES")
    print("=" * 60)

    for source in response.sources:
        print(
            f"Document: {source.document_id}"
        )
        print(
            f"Page: {source.page_number}"
        )
        print(
            f"Similarity: {source.similarity:.4f}"
        )
        print("-" * 60)

    assert response.answer

    assert len(response.sources) > 0