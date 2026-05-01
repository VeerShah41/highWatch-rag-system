import os
import json
import numpy as np
import faiss

from config import get_faiss_index_path, get_metadata_path

# FAISS dimension must match the embedding model output (all-MiniLM-L6-v2 = 384)
EMBEDDING_DIM = 384


def _load_metadata() -> dict:
    """Load chunk metadata from JSON file."""
    if not os.path.exists(get_metadata_path()):
        return {}
    with open(get_metadata_path(), "r") as f:
        return json.load(f)


def _save_metadata(metadata: dict):
    """Save chunk metadata to JSON file."""
    with open(get_metadata_path(), "w") as f:
        json.dump(metadata, f, indent=2)


def _load_index() -> faiss.Index | None:
    """Load FAISS index from disk. Returns None if not found."""
    if not os.path.exists(get_faiss_index_path()):
        return None
    return faiss.read_index(get_faiss_index_path())


def _save_index(index: faiss.Index):
    """Save FAISS index to disk."""
    faiss.write_index(index, get_faiss_index_path())


def add_chunks(chunks: list[dict], embeddings: np.ndarray):
    """
    Add new chunks and their embeddings to the FAISS index.

    Args:
        chunks: List of chunk dicts (chunk_text, doc_id, file_name, source, chunk_index)
        embeddings: numpy array of shape (len(chunks), 384)
    """
    if len(chunks) == 0:
        return

    # Load or create FAISS index
    index = _load_index()
    if index is None:
        index = faiss.IndexFlatIP(EMBEDDING_DIM)  # Inner Product (cosine after normalization)

    # Load existing metadata
    metadata = _load_metadata()

    # Current offset = number of existing vectors
    offset = index.ntotal

    # Add embeddings to FAISS index
    index.add(embeddings)

    # Add metadata at corresponding positions
    for i, chunk in enumerate(chunks):
        metadata[str(offset + i)] = chunk

    # Persist
    _save_index(index)
    _save_metadata(metadata)
    print(f"[VectorStore] Added {len(chunks)} chunks. Total: {index.ntotal}")


def search(query_embedding: np.ndarray, top_k: int = 5) -> list[dict]:
    """
    Search the FAISS index for the most relevant chunks.

    Args:
        query_embedding: numpy array of shape (1, 384)
        top_k: Number of top results to return

    Returns:
        List of chunk dicts sorted by relevance.
    """
    index = _load_index()
    if index is None or index.ntotal == 0:
        return []

    metadata = _load_metadata()

    # Clamp top_k to available chunks
    top_k = min(top_k, index.ntotal)

    scores, indices = index.search(query_embedding, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = metadata.get(str(idx), {})
        chunk["relevance_score"] = float(score)
        results.append(chunk)

    return results


def get_index_stats() -> dict:
    """Return stats about the current FAISS index."""
    index = _load_index()
    metadata = _load_metadata()
    
    # Extract unique documents
    documents = []
    seen = set()
    for v in metadata.values():
        file_name = v.get("file_name")
        doc_id = v.get("doc_id")
        if file_name and file_name not in seen:
            seen.add(file_name)
            documents.append({"file_name": file_name, "doc_id": doc_id})
            
    return {
        "faiss_index_exists": index is not None,
        "total_chunks_indexed": index.ntotal if index else 0,
        "unique_documents": len(documents),
        "documents": documents
    }


def get_sample_chunks(n: int = 5) -> list[str]:
    """Retrieve up to n random chunks to provide context for dynamic AI recommendations."""
    import random
    metadata = _load_metadata()
    if not metadata:
        return []
    
    # Take up to n random chunks
    keys = list(metadata.keys())
    if len(keys) > n:
        keys = random.sample(keys, n)
        
    return [metadata[k].get("chunk_text", "") for k in keys]


def clear_index():
    """Delete the FAISS index and metadata (for fresh re-sync)."""
    if os.path.exists(get_faiss_index_path()):
        os.remove(get_faiss_index_path())
    if os.path.exists(get_metadata_path()):
        os.remove(get_metadata_path())
    print("[VectorStore] Index cleared.")

