from backend.agents.extraction_agent import ExtractionAgent

agent = ExtractionAgent()

sample_text = """
Pump P101 failed due to bearing overheating.
Technician Raj replaced the bearing.
Lubrication completed.
"""

sample_pages = [{"text": sample_text, "metadata": {"source": "test_extraction.py"}}]
results = agent.process(sample_pages)

for item in results:

    print("\n========================")

    print("\nCHUNK")
    print(item["chunk"])

    print("\nENTITIES")
    print(item["entities"])

    print("\nRELATIONSHIPS")
    print(item["relationships"])