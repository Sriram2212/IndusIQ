from backend.retrieval.graph_retriever import GraphRetriever

retriever = GraphRetriever()

results = retriever.retrieve(
    "Pump P101"
)

print()

for item in results:

    print(item)