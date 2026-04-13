"""
Semantic embeddings using sentence transformers
Enables semantic search, similarity matching, and better clustering
"""
import numpy as np
from typing import List, Tuple, Optional, Dict
import warnings
warnings.filterwarnings('ignore')

# Lazy loading to avoid import errors if not installed
_EMBEDDING_MODEL = None

def get_embedding_model():
    """Lazy load embedding model"""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Use lightweight, fast model (80MB)
            _EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError as e:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            ) from e
        except Exception as e:
            error_msg = str(e)
            if "DLL" in error_msg or "torch" in error_msg.lower():
                raise RuntimeError(
                    "PyTorch initialization failed. This is often a Windows compatibility issue. "
                    "Try: pip install torch --index-url https://download.pytorch.org/whl/cpu"
                ) from e
            raise
    return _EMBEDDING_MODEL

def generate_embeddings(
    texts: List[str],
    batch_size: int = 32,
    show_progress: bool = False
) -> np.ndarray:
    """
    Generate embeddings for a list of texts
    
    Args:
        texts: List of text strings
        batch_size: Batch size for processing
        show_progress: Show progress bar
    
    Returns:
        numpy array of embeddings (n_texts, embedding_dim)
    """
    if not texts:
        return np.array([])
    
    model = get_embedding_model()
    
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
        normalize_embeddings=True  # Normalize for cosine similarity
    )
    
    return embeddings

def find_similar_responses(
    query_text: str,
    embeddings: np.ndarray,
    texts: List[str],
    top_k: int = 10,
    threshold: float = 0.5
) -> List[Tuple[str, float, int]]:
    """
    Find similar responses using cosine similarity
    
    Args:
        query_text: Query text to find similar responses to
        embeddings: Pre-computed embeddings for all texts
        texts: Original texts (for returning)
        top_k: Number of results to return
        threshold: Minimum similarity threshold
    
    Returns:
        List of (text, similarity_score, index) tuples
    """
    if embeddings.shape[0] == 0:
        return []
    
    model = get_embedding_model()
    query_embedding = model.encode(
        [query_text],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0]
    
    # Cosine similarity (embeddings are normalized)
    similarities = np.dot(embeddings, query_embedding)
    
    # Get top-k
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        similarity = float(similarities[idx])
        if similarity >= threshold:
            results.append((texts[idx], similarity, int(idx)))
    
    return results

def detect_near_duplicates(
    texts: List[str],
    embeddings: np.ndarray,
    similarity_threshold: float = 0.95
) -> List[Tuple[int, int, float]]:
    """
    Detect near-duplicate responses
    
    Args:
        texts: List of texts
        embeddings: Pre-computed embeddings
        similarity_threshold: Threshold for considering duplicates
    
    Returns:
        List of (index1, index2, similarity) tuples
    """
    if embeddings.shape[0] < 2:
        return []
    
    # Compute pairwise similarities
    similarities = np.dot(embeddings, embeddings.T)
    
    # Find pairs above threshold (excluding self-similarity)
    duplicates = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            similarity = float(similarities[i, j])
            if similarity >= similarity_threshold:
                duplicates.append((i, j, similarity))
    
    return duplicates

def cluster_with_embeddings(
    embeddings: np.ndarray,
    n_clusters: int = 20,
    random_state: int = 42
) -> np.ndarray:
    """
    Cluster texts using embeddings (better than TF-IDF)
    
    Args:
        embeddings: Pre-computed embeddings
        n_clusters: Number of clusters
        random_state: Random seed
    
    Returns:
        Cluster labels array
    """
    if embeddings.shape[0] == 0:
        return np.array([])
    
    from sklearn.cluster import KMeans
    
    n_clusters = min(n_clusters, embeddings.shape[0])
    if n_clusters < 2:
        n_clusters = 2
    
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init=10
    )
    clusters = kmeans.fit_predict(embeddings)
    
    return clusters

def compute_embedding_statistics(embeddings: np.ndarray) -> Dict:
    """
    Compute statistics about embeddings
    """
    if embeddings.shape[0] == 0:
        return {}
    
    return {
        "num_embeddings": embeddings.shape[0],
        "embedding_dim": embeddings.shape[1],
        "mean_norm": float(np.linalg.norm(embeddings, axis=1).mean()),
        "std_norm": float(np.linalg.norm(embeddings, axis=1).std())
    }

