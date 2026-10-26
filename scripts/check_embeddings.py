from app.embeddings.embedder import Embedder


embedder = Embedder()

text = "Employees are entitled to 18 days of annual leave."

vector = embedder.embed_text(text)

print("Embedding generated successfully!")
print("-" * 50)

print(f"Embedding dimensions: {len(vector)}")

print("\nFirst 10 values:")
print(vector[:10])