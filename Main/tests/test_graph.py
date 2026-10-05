from backend.agents.extraction_agent import ExtractionAgent
from backend.services.graph_service import GraphService

text = """
Pump P101 failed due to bearing overheating.

Technician Raj replaced the bearing.

Lubrication completed.
"""

extractor = ExtractionAgent()

graph = GraphService()

results = extractor.process(text)

for item in results:

    graph.store(item)

print("Knowledge stored successfully.")