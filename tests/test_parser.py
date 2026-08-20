from app.ingestion.parser import parse_document

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]

file_path = (
    PROJECT_ROOT
    / "data"
    / "sample"
    / "rag_test_mixed_pdf.pdf"
)

document = parse_document(file_path)

print("Document parsed successfully!")
print("-" * 50)

print("Metadata:")
print(document.metadata)

print("\nFull Text:")
print(document.text)

print("\nPages:")
for page in document.pages:
    print(
        f"Page {page.page_number} | "
        f"Method: {page.extraction_method}"
    )