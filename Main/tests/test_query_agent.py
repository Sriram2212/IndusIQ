from backend.agents.query_agent import QueryAgent

# Initialize the QueryAgent
query_agent = QueryAgent()

# Define test questions
test_questions = [
    "Why did Pump P101 fail?",
    "Who replaced the bearing on Pump P101?",
    "What is the status of lubrication work?"
]

print("================ QUERY AGENT TEST ================")

for question in test_questions:
    print(f"\n--- Testing Query: '{question}' ---")
    try:
        result = query_agent.query(question)
        print("\n[ANSWER]")
        print(result["answer"])
        print(f"\n[CONFIDENCE] {result['confidence']}")
        print("\n[SOURCES]")
        for src in result["sources"]:
            print(f"- {src.get('document')}: {src.get('detail')}")
        print("\n[GRAPH CONTEXT]")
        for rel in result["graph_context"]:
            print(f"- {rel}")
        print("\n[KEY ENTITIES EXTRACTED]")
        print(result["key_entities"])
        print("\n[FOLLOW-UP SUGGESTIONS]")
        print(result["follow_up_suggestions"])
    except Exception as e:
        err_msg = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"\n[ERROR] Error executing query: {err_msg}")
