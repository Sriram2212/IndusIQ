import json

from backend.llm.gemini_service import GeminiService
from backend.prompts.knowledge_extraction_prompt import KNOWLEDGE_EXTRACTION_PROMPT
from backend.utils.helpers import safe_json_parse


class KnowledgeExtractionService:

    def __init__(self):

        self.llm = GeminiService()

    def extract_knowledge(self, chunk: str):

        prompt = KNOWLEDGE_EXTRACTION_PROMPT.format(
            text=chunk
        )

        response = self.llm.generate(prompt)
        parsed = safe_json_parse(response)
        if isinstance(parsed, dict) and ("entities" in parsed or "relationships" in parsed):
            return {
                "entities": parsed.get("entities", []),
                "relationships": parsed.get("relationships", [])
            }

        return {"entities": [], "relationships": []}