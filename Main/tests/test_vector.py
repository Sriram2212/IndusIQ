from backend.services.vector_service import VectorService

vector_service = VectorService()

chunks = [
    "Pump P101 failed due to bearing overheating.",
    "Technician Raj replaced the bearing.",
    "Lubrication completed successfully."
]

vector_service.store_chunks(chunks)

results = vector_service.search(
    "Why did Pump P101 fail?"
)

print("\nRetrieved Chunks:\n")

for chunk in results:
    print(chunk)