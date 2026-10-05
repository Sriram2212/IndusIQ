from backend.llm.gemini_service import GeminiService

gemini = GeminiService()

response = gemini.generate(
    "Say about the llm?"
)

print(response)