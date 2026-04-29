import faiss
import numpy as np
import json
import os

class VectorIndex:
    """
    FAISS-backed vector index.
    Owns all embeddings.
    No other service talks to this directly — only EmbeddingService.
    """

    def __init__(self, dim=128):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)  # L2 distance search
        self.image_ids = []  # maps index position → image_id
        self.index_file = "faiss.index"
        self.ids_file = "faiss_ids.json"
        self._load()

    def add(self, image_id: str, vector: list):
        """Add an embedding vector for an image."""
        vec = np.array([vector], dtype=np.float32)
        self.index.add(vec)
        self.image_ids.append(image_id)
        self._save()
        print(f"[FAISS] Indexed: {image_id}")

    def search(self, query_vector: list, k: int = 3):
        """Find top-k similar images to a query vector."""
        if self.index.ntotal == 0:
            return []
        k = min(k, self.index.ntotal)
        vec = np.array([query_vector], dtype=np.float32)
        distances, indices = self.index.search(vec, k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.image_ids):
                results.append({
                    "image_id": self.image_ids[idx],
                    "distance": round(float(dist), 4)
                })
        return results

    def _save(self):
        """Persist index to disk."""
        faiss.write_index(self.index, self.index_file)
        with open(self.ids_file, "w") as f:
            json.dump(self.image_ids, f)

    def _load(self):
        """Load index from disk if it exists."""
        if os.path.exists(self.index_file) and os.path.exists(self.ids_file):
            self.index = faiss.read_index(self.index_file)
            with open(self.ids_file, "r") as f:
                self.image_ids = json.load(f)
            print(f"[FAISS] Loaded {self.index.ntotal} vectors")

    def count(self):
        return self.index.ntotal