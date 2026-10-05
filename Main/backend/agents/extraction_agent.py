from backend.services.chunking_service import ChunkingService
from backend.services.knowledge_extraction_service import KnowledgeExtractionService


class ExtractionAgent:

    def __init__(self):

        self.chunker = ChunkingService()
        self.knowledge_service = KnowledgeExtractionService()

    def process(self, pages):
        if isinstance(pages, str):
            pages = [{"text": pages, "metadata": {}}]

        results = []

        for page in pages:
            if isinstance(page, str):
                page_text = page
                page_meta = {}
            elif isinstance(page, dict):
                page_text = page.get("text", "")
                page_meta = page.get("metadata", {})
            else:
                continue

            if not page_text or not page_text.strip():
                continue

            chunks = self.chunker.split_text(page_text)

            for chunk in chunks:
                if not chunk or not chunk.strip():
                    continue

                try:
                    knowledge = self.knowledge_service.extract_knowledge(chunk)
                    results.append(
                        {
                            "chunk": chunk,
                            "metadata": page_meta,
                            "entities": knowledge.get("entities", []) if isinstance(knowledge, dict) else [],
                            "relationships": knowledge.get("relationships", []) if isinstance(knowledge, dict) else []
                        }
                    )
                except Exception as e:
                    print(f"   [WARNING] Knowledge extraction failed for chunk due to API error: {e}")
                    results.append(
                        {
                            "chunk": chunk,
                            "metadata": page_meta,
                            "entities": [],
                            "relationships": []
                        }
                    )

        return results