"""Embedding service with OpenAI and local fallbacks."""
import os
from typing import List
from typing import Optional

def _openai_embeddings(texts: List[str], model: str) -> Optional[List[List[float]]]:
    """Create embeddings via OpenAI, returns None on setup errors."""
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in response.data]


def _local_embeddings(texts: List[str]) -> List[List[float]]:
    """Create embeddings locally using sentence-transformers as a fallback."""
    try:
        from sentence_transformers import SentenceTransformer  # heavyweight, optional
        model = SentenceTransformer("all-MiniLM-L6-v2")
        vectors = model.encode(texts, convert_to_numpy=True)
        return [v.tolist() for v in vectors]
    except Exception:
        # Lightweight fallback: TF-IDF mean-pooled character n-grams
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
        vec = TfidfVectorizer(analyzer="word", ngram_range=(1,2), max_features=4096)
        X = vec.fit_transform(texts).astype(np.float32)
        # Convert sparse to dense safely
        dense = X.toarray()
        return dense.tolist()


def create_embeddings(texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    """Create embeddings for a list of texts using OpenAI or local fallback.
    
    - Uses OpenAI if `OPENAI_API_KEY` is set and works
    - Falls back to sentence-transformers if API key is missing/invalid
    """
    if not texts:
        return []
    # Try OpenAI first
    try:
        result = _openai_embeddings(texts, model)
        if result is not None:
            return result
    except Exception:
        # Fall back silently to local embeddings
        pass
    # Local fallback
    try:
        return _local_embeddings(texts)
    except Exception as e:
        raise Exception(f"Error creating embeddings (local fallback failed): {str(e)}")
