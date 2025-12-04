# embeddings.py
from sentence_transformers import SentenceTransformer
import numpy as np

_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


class VectorStore:
    def __init__(self, chunks: list[str]):
        self.chunks = chunks
        self.embeddings = self._encode(chunks)

    def _encode(self, texts: list[str]) -> np.ndarray:
        emb = _model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10
        return emb / norms

    def search(self, query: str, k: int = 5) -> list[str]:
        q_emb = _model.encode([query], convert_to_numpy=True)[0]
        q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-10)
        sims = self.embeddings @ q_emb
        idx = np.argsort(-sims)[:k]
        return [self.chunks[i] for i in idx]