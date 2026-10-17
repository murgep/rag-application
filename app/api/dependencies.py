from app.embeddings.embedder import Embedder
from app.generation.generator import Generator
from app.rag.pipeline import RAGPipeline
from app.retrieval.pg_vector_store import PostgreSQLVectorStore
from app.retrieval.retriever import Retriever


def get_rag_pipeline() -> RAGPipeline:
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