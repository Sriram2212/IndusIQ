from sentence_transformers import SentenceTransformer

print("Loading model...")

model = SentenceTransformer("BAAI/bge-base-en-v1.5")

print("Model loaded successfully!")

text = "Pump P101 failed due to bearing overheating."

embedding = model.encode(text)

print(f"Embedding Dimension: {len(embedding)}")

print("First 10 values:")

print(embedding[:10])