import os
import pickle
import hashlib
import faiss
import numpy as np


class FaissManager:

    def __init__(self):
        print("[INFO] FaissManager Initialized with Deduplication Engine")

        self.dimension = 384

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data", "vector_store")
        self.index_path = os.path.join(data_dir, "faiss.index")
        self.metadata_path = os.path.join(data_dir, "metadata.pkl")

        os.makedirs(data_dir, exist_ok=True)
        print("Vector Store Folder Ready [OK]")

        if os.path.exists(self.index_path):
            print("Loading Existing FAISS Index")
            self.index = faiss.read_index(self.index_path)
        else:
            print("Creating New FAISS Index")
            self.index = faiss.IndexFlatL2(self.dimension)

        if os.path.exists(self.metadata_path):
            print("Loading Existing Metadata")
            try:
                with open(self.metadata_path, "rb") as f:
                    self.metadata = pickle.load(f)
            except Exception as e:
                print(f"[WARNING] Failed to load metadata: {e}, initializing empty.")
                self.metadata = []
        else:
            print("Creating Empty Metadata")
            self.metadata = []

        # Run startup deduplication to clean any existing redundant vectors
        self.deduplicate_index()

    @staticmethod
    def compute_content_hash(text: str, document: str = "") -> str:
        """
        Computes a normalized SHA-256 hash of the text content and document to detect duplicates.
        """
        normalized_text = " ".join(text.strip().split())
        key = f"{document}::{normalized_text}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def get_existing_hashes(self) -> set:
        """
        Collects set of all content hashes present in metadata.
        """
        hashes = set()
        for m in self.metadata:
            h = m.get("content_hash")
            if not h and "text" in m:
                h = self.compute_content_hash(m["text"], m.get("document", ""))
                m["content_hash"] = h
            if h:
                hashes.add(h)
        return hashes

    def deduplicate_index(self) -> int:
        """
        Scans all stored chunks and eliminates duplicate vectors from both metadata and FAISS index.
        """
        if not self.metadata or self.index.ntotal == 0:
            return 0

        seen_hashes = set()
        unique_indices = []

        for i, m in enumerate(self.metadata):
            text = m.get("text", "")
            doc = m.get("document", "")
            h = m.get("content_hash") or self.compute_content_hash(text, doc)
            m["content_hash"] = h

            if h not in seen_hashes:
                seen_hashes.add(h)
                unique_indices.append(i)

        duplicates_count = len(self.metadata) - len(unique_indices)
        if duplicates_count > 0:
            print(f"[FAISS DEDUPLICATION] Found {duplicates_count} duplicate chunks. Rebuilding clean index...")
            try:
                unique_vectors = np.array(
                    [self.index.reconstruct(i) for i in unique_indices],
                    dtype=np.float32
                )
                new_index = faiss.IndexFlatL2(self.dimension)
                new_index.add(unique_vectors)
                self.index = new_index
                self.metadata = [self.metadata[i] for i in unique_indices]
                self.save()
                print(f"[FAISS DEDUPLICATION] Rebuilt index. Clean vectors: {self.index.ntotal}")
            except Exception as e:
                print(f"[FAISS DEDUPLICATION ERROR] Could not reconstruct index: {e}")

        return duplicates_count

    def add_chunk(self, metadata: dict, embedding: list) -> bool:
        """
        Adds a single vector to FAISS with strict duplicate checking.
        Returns True if added, False if duplicate was skipped.
        """
        text = metadata.get("text", "")
        doc = metadata.get("document", "")
        content_hash = self.compute_content_hash(text, doc)
        metadata["content_hash"] = content_hash

        # Check if identical content hash already exists
        existing_hashes = self.get_existing_hashes()
        if content_hash in existing_hashes:
            print(f"[FAISS DE-DUP] Skipped duplicate chunk for document '{doc}'")
            return False

        vector = np.array([embedding], dtype=np.float32)
        self.index.add(vector)
        self.metadata.append(metadata)

        print(f"[FAISS] Added unique chunk. Total index size: {self.index.ntotal}")
        self.save()
        return True

    def add_chunks_batch(self, chunks_with_embeddings: list, document_name: str = None) -> int:
        """
        Adds a batch of (metadata, embedding) pairs.
        If document_name is given, previous vectors for that document are cleared first (idempotent re-indexing).
        """
        if document_name:
            self.remove_document(document_name)

        existing_hashes = self.get_existing_hashes()
        new_vectors = []
        new_metadata = []

        for item in chunks_with_embeddings:
            meta = item.get("metadata", {})
            emb = item.get("embedding", [])
            text = meta.get("text", "")
            doc = meta.get("document", document_name or "")
            content_hash = self.compute_content_hash(text, doc)
            meta["content_hash"] = content_hash

            if content_hash not in existing_hashes:
                existing_hashes.add(content_hash)
                new_vectors.append(emb)
                new_metadata.append(meta)

        if new_vectors:
            vectors_array = np.array(new_vectors, dtype=np.float32)
            self.index.add(vectors_array)
            self.metadata.extend(new_metadata)
            self.save()
            print(f"[FAISS] Batch added {len(new_vectors)} unique chunks. Total: {self.index.ntotal}")
            return len(new_vectors)

        return 0

    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)

    def search(self, embedding, k=5):
        if self.index.ntotal == 0:
            return []

        vector = np.array([embedding], dtype=np.float32)
        # Fetch up to 2x requested k to allow for deduplication
        fetch_k = min(self.index.ntotal, max(k * 2, 10))
        distances, indices = self.index.search(vector, fetch_k)

        results = []
        seen_texts = set()

        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                meta = self.metadata[idx].copy()
                text_normalized = " ".join(meta.get("text", "").strip().split())
                
                # Deduplicate returned search results by text
                if text_normalized and text_normalized not in seen_texts:
                    seen_texts.add(text_normalized)
                    meta["distance"] = float(distances[0][i])
                    results.append(meta)

                if len(results) >= k:
                    break

        return results

    def remove_document(self, document_name: str) -> int:
        """
        Removes all vector chunks and metadata corresponding to a document.
        Rebuilds the FAISS index from remaining vectors.
        """
        if not self.metadata or self.index.ntotal == 0:
            return 0

        clean_doc_name = os.path.basename(document_name)
        indices_to_keep = [
            i for i, m in enumerate(self.metadata)
            if m.get("document") != clean_doc_name and m.get("document") != document_name and m.get("filename") != clean_doc_name
        ]
        removed_count = len(self.metadata) - len(indices_to_keep)

        if removed_count == 0:
            return 0

        print(f"[FAISS] Removing {removed_count} chunk vectors for document '{document_name}'...")

        if len(indices_to_keep) > 0:
            try:
                remaining_vectors = np.array(
                    [self.index.reconstruct(i) for i in indices_to_keep],
                    dtype=np.float32
                )
                new_index = faiss.IndexFlatL2(self.dimension)
                new_index.add(remaining_vectors)
                self.index = new_index
                self.metadata = [self.metadata[i] for i in indices_to_keep]
            except Exception as e:
                print(f"[FAISS ERROR] Failed to reconstruct FAISS index on document removal: {e}")
                self.metadata = [self.metadata[i] for i in indices_to_keep]
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []

        self.save()
        print(f"[FAISS] Index updated. Remaining vectors: {self.index.ntotal}")
        return removed_count

    def clear_all(self):
        """
        Clears the entire FAISS index and metadata.
        """
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        self.save()
        print("[FAISS] Cleared all vectors and metadata.")