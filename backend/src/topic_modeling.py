"""
Topic modeling using LDA and NMF
Production-ready classical NLP approach
"""
import pandas as pd
import numpy as np
from sklearn.decomposition import LatentDirichletAllocation, NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

def extract_topics_lda(
    texts: List[str],
    n_topics: int = 10,
    max_features: int = 1000,
    ngram_range: tuple = (1, 2),
    random_state: int = 42
) -> Tuple[List[Dict], np.ndarray]:
    """
    Extract topics using Latent Dirichlet Allocation (LDA)
    
    Args:
        texts: List of text strings
        n_topics: Number of topics to extract
        max_features: Maximum features for TF-IDF
        ngram_range: N-gram range for vectorization
        random_state: Random seed for reproducibility
    
    Returns:
        Tuple of (topics list, topic distribution matrix)
    """
    # Vectorize texts
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        stop_words='english',
        min_df=2,  # Ignore terms that appear in < 2 documents
        max_df=0.95  # Ignore terms that appear in > 95% of documents
    )
    
    try:
        X = vectorizer.fit_transform(texts)
    except ValueError:
        # Fallback if no features found
        return [], np.array([])
    
    if X.shape[0] == 0 or X.shape[1] == 0:
        return [], np.array([])
    
    # Adjust n_topics if we have fewer documents
    n_topics = min(n_topics, X.shape[0] - 1)
    if n_topics < 2:
        n_topics = 2
    
    # Fit LDA
    lda = LatentDirichletAllocation(
        n_components=n_topics,
        random_state=random_state,
        max_iter=10,
        learning_method='batch',
        n_jobs=-1
    )
    lda.fit(X)
    
    # Extract topics
    feature_names = vectorizer.get_feature_names_out()
    topics = []
    
    for topic_idx, topic in enumerate(lda.components_):
        top_words_idx = topic.argsort()[-15:][::-1]  # Top 15 words
        top_words = [feature_names[i] for i in top_words_idx]
        top_weights = topic[top_words_idx].tolist()
        
        topics.append({
            "topic_id": topic_idx,
            "top_words": top_words,
            "weights": top_weights,
            "topic_weight": float(topic.sum())  # Overall topic importance
        })
    
    # Get topic distribution for each document
    topic_dist = lda.transform(X)
    
    return topics, topic_dist

def extract_topics_nmf(
    texts: List[str],
    n_topics: int = 10,
    max_features: int = 1000,
    ngram_range: tuple = (1, 2),
    random_state: int = 42
) -> Tuple[List[Dict], np.ndarray]:
    """
    Extract topics using Non-negative Matrix Factorization (NMF)
    Often produces more interpretable topics than LDA
    """
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        stop_words='english',
        min_df=2,
        max_df=0.95
    )
    
    try:
        X = vectorizer.fit_transform(texts)
    except ValueError:
        return [], np.array([])
    
    if X.shape[0] == 0 or X.shape[1] == 0:
        return [], np.array([])
    
    n_topics = min(n_topics, X.shape[0] - 1)
    if n_topics < 2:
        n_topics = 2
    
    # Fit NMF
    nmf = NMF(
        n_components=n_topics,
        random_state=random_state,
        max_iter=200,
        alpha=0.1,
        l1_ratio=0.5
    )
    nmf.fit(X)
    
    # Extract topics
    feature_names = vectorizer.get_feature_names_out()
    topics = []
    
    for topic_idx, topic in enumerate(nmf.components_):
        top_words_idx = topic.argsort()[-15:][::-1]
        top_words = [feature_names[i] for i in top_words_idx]
        top_weights = topic[top_words_idx].tolist()
        
        topics.append({
            "topic_id": topic_idx,
            "top_words": top_words,
            "weights": top_weights,
            "topic_weight": float(topic.sum())
        })
    
    topic_dist = nmf.transform(X)
    
    return topics, topic_dist

def cluster_similar_responses(
    texts: List[str],
    n_clusters: int = 20,
    max_features: int = 500,
    random_state: int = 42
) -> Tuple[np.ndarray, KMeans]:
    """
    Cluster similar responses using K-means on TF-IDF vectors
    """
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        stop_words='english',
        min_df=2
    )
    
    try:
        X = vectorizer.fit_transform(texts)
    except ValueError:
        return np.array([]), None
    
    if X.shape[0] == 0:
        return np.array([]), None
    
    # Adjust n_clusters
    n_clusters = min(n_clusters, X.shape[0])
    if n_clusters < 2:
        n_clusters = 2
    
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init=10,
        max_iter=300
    )
    clusters = kmeans.fit_predict(X)
    
    return clusters, kmeans

def assign_topics_to_documents(
    texts: List[str],
    topics: List[Dict],
    topic_dist: np.ndarray
) -> List[Dict]:
    """
    Assign dominant topic to each document
    """
    if topic_dist.shape[0] == 0:
        return []
    
    assignments = []
    for i, text in enumerate(texts):
        if i < topic_dist.shape[0]:
            dominant_topic_idx = int(topic_dist[i].argmax())
            dominant_topic_weight = float(topic_dist[i][dominant_topic_idx])
            
            assignments.append({
                "text": text,
                "dominant_topic_id": dominant_topic_idx,
                "topic_confidence": dominant_topic_weight,
                "topic_words": topics[dominant_topic_idx]["top_words"][:5] if dominant_topic_idx < len(topics) else []
            })
    
    return assignments

def get_topic_statistics(
    topics: List[Dict],
    topic_dist: np.ndarray,
    df: pd.DataFrame = None
) -> Dict:
    """
    Get statistics about topics
    """
    if topic_dist.shape[0] == 0:
        return {}
    
    stats = {
        "total_topics": len(topics),
        "topic_distribution": {},
        "avg_topic_confidence": float(topic_dist.max(axis=1).mean())
    }
    
    # Count documents per topic
    dominant_topics = topic_dist.argmax(axis=1)
    for topic_idx in range(len(topics)):
        count = int((dominant_topics == topic_idx).sum())
        stats["topic_distribution"][f"topic_{topic_idx}"] = count
    
    return stats

