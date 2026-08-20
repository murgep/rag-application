from app.embeddings.embedder import Embedder
from app.ingestion.chunker import chunk_document
from app.ingestion.parser import parse_document
from app.retrieval.retriever import Retriever
from app.retrieval.vector_store import VectorStore


# --------------------------------------------------
# 1. Parse document
# --------------------------------------------------
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]

file_path = (
    PROJECT_ROOT
    / "data"
    / "sample"
    / "rag_test_mixed_pdf.pdf"
)

document = parse_document(file_path)


# --------------------------------------------------
# 2. Create chunks
# --------------------------------------------------

chunks = chunk_document(
    document,
    chunk_size=50,
    overlap=10,
)

print(f"Created {len(chunks)} chunks.")


# --------------------------------------------------
# 3. Generate embeddings
# --------------------------------------------------

embedder = Embedder()

chunk_texts = [
    chunk.text
    for chunk in chunks
]

embeddings = embedder.embed_texts(
    chunk_texts
)

print(
    f"Generated {len(embeddings)} embeddings."
)

print(
    f"Embedding dimensions: "
    f"{len(embeddings[0])}"
)


# --------------------------------------------------
# 4. Create vector store
# --------------------------------------------------

vector_store = VectorStore()

vector_store.add(
    chunks,
    embeddings,
)


# --------------------------------------------------
# 5. Create Retriever
# --------------------------------------------------

retriever = Retriever(
    embedder=embedder,
    vector_store=vector_store,
)


# --------------------------------------------------
# 6. Query
# --------------------------------------------------

query = (
    "How many annual leave days "
    "does an employee get?"
)


# --------------------------------------------------
# 7. Retrieve
# --------------------------------------------------

results = retriever.retrieve(
    query=query,
    top_k=3,
)


# --------------------------------------------------
# 8. Display results
# --------------------------------------------------

print("\nSearch Results")
print("=" * 60)

for rank, (chunk, score) in enumerate(
    results,
    start=1,
):
    print(f"\nRank: {rank}")
    print(f"Similarity: {score:.4f}")
    print(f"Chunk ID: {chunk.chunk_id}")
    print(f"Page: {chunk.page_number}")
    print(f"Method: {chunk.extraction_method}")
    print(f"Text: {chunk.text}")