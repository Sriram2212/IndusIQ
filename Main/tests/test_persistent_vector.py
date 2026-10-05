from backend.retrieval.vector_retriever import VectorRetriever

retriever = VectorRetriever()

results = retriever.retrieve(
    "Why did Pump P101 fail?"
)

print()

for item in results:

    print(item)