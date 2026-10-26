from app.database.document_store import DocumentStore
from app.embeddings.embedder import Embedder
from app.ingestion.chunker import chunk_document
from app.ingestion.parser import parse_document


# --------------------------------------------------
# 1. Parse document
# --------------------------------------------------
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]

file_path = (
    PROJECT_ROOT
    / "data"
    / "sample"
    / "employee_handbook_rag_retrieval_test_v2.pdf"
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


# --------------------------------------------------
# 4. Save to PostgreSQL
# --------------------------------------------------

store = DocumentStore()

store.save_document(
    document_id=document.metadata.document_id,
    filename=document.metadata.filename,
    file_type=document.metadata.file_type,
    source=document.metadata.source,
)

store.save_chunks(
    chunks=chunks,
    embeddings=embeddings,
)

print("Document and chunks saved successfully!")