from backend.services.embedding_service import EmbeddingService
from backend.vectorstore.faiss_manager import FaissManager


class VectorService:

    def __init__(self):
        print("[INFO] VectorService initialized with deduplication support")
        self.embedding_service = EmbeddingService()
        self.faiss = FaissManager()

    def store_chunks(self, chunks_data, document_name="Unknown"):
        """
        Stores chunks into FAISS with deduplication and document-level replacement.
        """
        print("\n================ VECTOR SERVICE (DEDUPLICATED) ================")
        print(f"Document Name : {document_name}")
        print(f"Total Chunks  : {len(chunks_data)}")

        # First, purge old vectors from any previous upload of this document
        if document_name and document_name != "Unknown":
            self.faiss.remove_document(document_name)

        chunks_with_embeddings = []
        for idx, item in enumerate(chunks_data):
            if isinstance(item, str):
                chunk = item
                page_meta = {}
            else:
                chunk = item.get("text", "")
                page_meta = item.get("metadata", {})

            if not chunk or not chunk.strip():
                continue

            embedding = self.embedding_service.create_embedding(chunk)
            metadata = {
                "chunk_id":      idx,
                "document":      document_name,
                "text":          chunk,
                "page":          page_meta.get("page", 1),
                "sheet":         page_meta.get("sheet"),
                "section":       page_meta.get("section"),
                "entity_ids":    page_meta.get("entity_ids", []),
                "evidence_type": page_meta.get("evidence_type", "UNKNOWN"),
            }

            chunks_with_embeddings.append({
                "metadata": metadata,
                "embedding": embedding
            })

        stored_count = self.faiss.add_chunks_batch(chunks_with_embeddings, document_name)
        print(f"\n[OK] Stored {stored_count} unique chunks for '{document_name}' in FAISS.")

    def search(self, query, k=5):
        print("\n=============== VECTOR SEARCH ===============")
        print("Query :", query)

        embedding = self.embedding_service.create_embedding(query)
        results = self.faiss.search(embedding, k=k)

        print("Retrieved :", len(results), "unique chunks")
        return results

    def delete_document_vectors(self, document_name: str) -> int:
        """
        Deletes vector embeddings associated with a document from the FAISS index.
        """
        return self.faiss.remove_document(document_name)