from sentence_transformers import SentenceTransformer


class EmbeddingService:

    def __init__(self):
        try:
            self.model = SentenceTransformer(
                "all-MiniLM-L6-v2",
                device="cpu",
                local_files_only=True
            )
        except Exception:
            self.model = SentenceTransformer(
                "all-MiniLM-L6-v2",
                device="cpu"
            )

    def create_embedding(self, text: str):

        embedding = self.model.encode(text)

        return embedding.tolist()