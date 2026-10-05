from backend.services.vector_service import VectorService
from backend.retrieval.models import RetrievalResult


class VectorRetriever:

    def __init__(self):

        self.vector_service = VectorService()

    def retrieve(self, question: str):

        results = self.vector_service.search(question)

        output = []

        for item in results:

            distance = item.get("distance", 2.0)
            similarity = max(0.0, min(1.0, 1.0 - (distance / 2.0)))

            output.append(

                RetrievalResult(

                    source="vector",

                    content=item["text"],

                    metadata={

                        "document":      item["document"],

                        "chunk_id":      item["chunk_id"],

                        "page":          item.get("page"),

                        "sheet":         item.get("sheet"),

                        "section":       item.get("section"),

                        "entity_ids":    item.get("entity_ids", []),

                        "evidence_type": item.get("evidence_type", "UNKNOWN"),

                        "similarity":    similarity

                    }

                )

            )

        return output