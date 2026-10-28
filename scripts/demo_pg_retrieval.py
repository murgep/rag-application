from app.embeddings.embedder import Embedder
from app.retrieval.pg_vector_store import PostgreSQLVectorStore
from app.retrieval.retriever import Retriever


# --------------------------------------------------
# 1. Create services
# --------------------------------------------------

embedder = Embedder()

vector_store = PostgreSQLVectorStore()

retriever = Retriever(
    embedder=embedder,
    vector_store=vector_store,
)


# --------------------------------------------------
# 2. Query
# --------------------------------------------------

query = (
    "How many annual leave days "
    "does an employee get?"
)


# --------------------------------------------------
# 3. Retrieve
# --------------------------------------------------

results = retriever.retrieve(
    query=query,
    top_k=3,
)


# --------------------------------------------------
# 4. Display results
# --------------------------------------------------

print("PostgreSQL Semantic Search")
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