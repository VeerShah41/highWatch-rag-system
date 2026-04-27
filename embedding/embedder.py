import numpy as np
import torch
from sentence_transformers import SentenceTransformer

# Limit threads to reduce memory footprint on Render
torch.set_num_threads(1)

# Load model once at module level (singleton — avoids reloading on every call)
_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        print(f"[Embedder] Loading model '{_MODEL_NAME}'...")
        _model = SentenceTransformer(_MODEL_NAME)
        print("[Embedder] Model loaded.")
    return _model


def get_embeddings(texts: list[str]) -> np.ndarray:
    """
    Generate embeddings for a list of text strings.

    Args:
        texts: List of strings to embed.

    Returns:
        numpy array of shape (len(texts), 384), dtype float32.
    """
    model = _get_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,  # Normalize for cosine similarity
    )
    return embeddings.astype(np.float32)


def get_single_embedding(text: str) -> np.ndarray:
    """
    Generate embedding for a single text string.

    Returns:
        numpy array of shape (1, 384), dtype float32.
    """
    return get_embeddings([text])
