"""
Fallback embedding methods that don't require PyTorch
Uses simpler TF-IDF-based similarity when PyTorch is unavailable
"""
import numpy as np
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def generate_embeddings_tfidf(texts: List[str]) -> np.ndarray:
    """
    Generate TF-IDF embeddings as fallback when PyTorch is unavailable
    Less accurate than sentence transformers but works everywhere
    """
    if not texts:
        return np.array([])
    
    vectorizer = TfidfVectorizer(
        max_features=500,
        ngram_range=(1, 2),
        stop_words='english',
        min_df=1,
        max_df=0.95
    )
    
    try:
        embeddings = vectorizer.fit_transform(texts).toarray()
        # Normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        embeddings = embeddings / norms
        return embeddings
    except Exception as e:
        import logging
        logging.error(f"TF-IDF embedding generation failed: {e}")
        return np.array([])

def find_similar_responses_tfidf(
    query_text: str,
    embeddings: np.ndarray,
    texts: List[str],
    top_k: int = 10,
    threshold: float = 0.3  # Lower threshold for TF-IDF
) -> List[Tuple[str, float, int]]:
    """
    Find similar responses using TF-IDF cosine similarity
    """
    if embeddings.shape[0] == 0 or not texts:
        return []
    
    # Generate query embedding
    vectorizer = TfidfVectorizer(
        max_features=500,
        ngram_range=(1, 2),
        stop_words='english',
        min_df=1,
        max_df=0.95
    )
    
    # Fit on all texts including query
    all_texts = texts + [query_text]
    vectorizer.fit(all_texts)
    
    # Get query embedding
    query_embedding = vectorizer.transform([query_text]).toarray()[0]
    query_norm = np.linalg.norm(query_embedding)
    if query_norm > 0:
        query_embedding = query_embedding / query_norm
    
    # Compute similarities
    similarities = np.dot(embeddings, query_embedding)
    
    # Get top-k
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        similarity = float(similarities[idx])
        if similarity >= threshold:
            results.append((texts[idx], similarity, int(idx)))
    
    return results

