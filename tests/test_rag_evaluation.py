from app.embeddings.embedder import Embedder
from app.generation.generator import Generator
from app.rag.pipeline import RAGPipeline
from app.retrieval.pg_vector_store import PostgreSQLVectorStore
from app.retrieval.retriever import Retriever


def create_rag_pipeline():

    embedder = Embedder()

    vector_store = PostgreSQLVectorStore()

    retriever = Retriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    generator = Generator()

    return RAGPipeline(
        retriever=retriever,
        generator=generator,
    )


def test_known_question():

    rag = create_rag_pipeline()

    question = (
        "How many days of annual leave do employees receive?"
    )

    response = rag.ask(
        question=question,
        top_k=3,
        similarity_threshold=0.70,
    )

    print("\nKnown Question")
    print("----------------")
    print(f"Question: {question}")
    print(f"Answer: {response.answer}")
    print(f"Sources: {len(response.sources)}")

    assert response.answer
    assert len(response.sources) > 0


def test_paraphrased_question():

    rag = create_rag_pipeline()

    question = (
        "How much annual leave is an employee entitled "
        "to each year?"
    )

    response = rag.ask(
        question=question,
        top_k=3,
        similarity_threshold=0.70,
    )

    print("\nParaphrased Question")
    print("----------------------")
    print(f"Question: {question}")
    print(f"Answer: {response.answer}")
    print(f"Sources: {len(response.sources)}")

    assert response.answer
    assert len(response.sources) > 0


def test_unrelated_question():

    rag = create_rag_pipeline()

    question = (
        "What is the company's policy for working on Mars?"
    )

    response = rag.ask(
        question=question,
        top_k=3,
        similarity_threshold=0.70,
    )

    print("\nUnrelated Question")
    print("-------------------")
    print(f"Question: {question}")
    print(f"Answer: {response.answer}")
    print(f"Sources: {response.sources}")

    assert response.answer == (
        "I don't have enough information in the provided "
        "documents to answer this question."
    )

    assert response.sources == []