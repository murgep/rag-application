from app.ingestion.parser import parse_document
from app.ingestion.chunker import chunk_document
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

file_path = (
    PROJECT_ROOT
    / "data"
    / "sample"
    / "rag_test_mixed_pdf.pdf"
)

document = parse_document(file_path)

chunks = chunk_document(
    document,
    chunk_size=50,
    overlap=10,
)

print(f"Total chunks: {len(chunks)}")
print("=" * 60)

for chunk in chunks:
    print(f"Chunk ID: {chunk.chunk_id}")
    print(f"Page: {chunk.page_number}")
    print(f"Method: {chunk.extraction_method}")
    print(f"Source: {chunk.source}")
    print(f"Text: {chunk.text}")
    print("-" * 60)