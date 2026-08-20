from pydantic import BaseModel


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    file_type: str
    source: str


class ParsedPage(BaseModel):
    page_number: int
    text: str
    extraction_method: str


class ParsedDocument(BaseModel):
    text: str
    metadata: DocumentMetadata
    pages: list[ParsedPage]


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    page_number: int
    source: str
    extraction_method: str

class RAGSource(BaseModel):
    document_id: str
    source: str
    page_number: int
    similarity: float


class RAGResponse(BaseModel):
    answer: str
    sources: list[RAGSource]