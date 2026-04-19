# pipeline.py
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = "index/legal_index.faiss"
CHUNKS_PATH = "index/legal_index.chunks.json"

_model = None
_index = None
_chunks = None


def _load():
    global _model, _index, _chunks
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    if _index is None:
        _index = faiss.read_index(INDEX_PATH)
    if _chunks is None:
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            _chunks = json.load(f)


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """Return top_k relevant chunks for a query."""
    _load()
    embedding = _model.encode([query], convert_to_numpy=True).astype("float32")
    distances, indices = _index.search(embedding, top_k)
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(_chunks):
            chunk = _chunks[idx].copy()
            chunk["score"] = float(dist)
            results.append(chunk)
    return results


def answer(query: str, top_k: int = 5) -> str:
    """Formatted answer with retrieved context."""
    hits = retrieve(query, top_k)
    lines = [f"Query: {query}\n", "=" * 60]
    for i, hit in enumerate(hits, 1):
        meta = hit.get("meta", {})
        lines.append(
            f"\n[{i}] Case: {meta.get('case_name', 'Unknown')}"
            f"\n    Score: {hit['score']:.4f}"
            f"\n    Excerpt: {hit['text'][:300].strip()}..."
        )
    return "\n".join(lines)