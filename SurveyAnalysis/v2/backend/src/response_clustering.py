"""
Cluster survey responses using stored embeddings.
Flow: CSV rows → Embeddings → Vector DB → Clustering (DBSCAN / HDBSCAN / KMeans) → Grouped records → LLM themes + sentiment.
"""
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from src.vector_db import get_points_for_upload

logger = logging.getLogger(__name__)

# Defaults
DEFAULT_EPS = 0.35
DEFAULT_MIN_SAMPLES = 2
DEFAULT_MIN_CLUSTER_SIZE = 5  # HDBSCAN: auto clusters; lower = more clusters for smaller datasets
DEFAULT_N_CLUSTERS = 10  # KMeans: you choose K
MAX_SAMPLE_TEXTS_PER_CLUSTER = 5

# Methods: dbscan (eps + min_samples), hdbscan (min_cluster_size, auto K), kmeans (n_clusters)
CLUSTER_METHOD_DBSCAN = "dbscan"
CLUSTER_METHOD_HDBSCAN = "hdbscan"
CLUSTER_METHOD_KMEANS = "kmeans"


def _cluster_vectors(
    vectors: np.ndarray,
    method: str = CLUSTER_METHOD_DBSCAN,
    eps: float = DEFAULT_EPS,
    min_samples: int = DEFAULT_MIN_SAMPLES,
    min_cluster_size: int = DEFAULT_MIN_CLUSTER_SIZE,
    n_clusters: int = DEFAULT_N_CLUSTERS,
) -> np.ndarray:
    """Return cluster labels (array of int; -1 = noise for DBSCAN/HDBSCAN)."""
    if method == CLUSTER_METHOD_KMEANS:
        from sklearn.cluster import KMeans
        n_clusters = min(n_clusters, len(vectors))
        if n_clusters < 2:
            return np.zeros(len(vectors), dtype=np.int32)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        return kmeans.fit_predict(vectors).astype(np.int32)
    if method == CLUSTER_METHOD_HDBSCAN:
        try:
            import hdbscan
            # HDBSCAN expects distance; use precomputed cosine distance (1 - cosine_sim)
            # Convert to float64 to avoid dtype mismatch error
            from sklearn.metrics.pairwise import cosine_distances
            vectors_f64 = vectors.astype(np.float64)
            dist = cosine_distances(vectors_f64)
            clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric="precomputed")
            return clusterer.fit_predict(dist).astype(np.int32)
        except ImportError:
            logger.warning("hdbscan not installed, falling back to DBSCAN")
            method = CLUSTER_METHOD_DBSCAN
    # DBSCAN (default)
    from sklearn.cluster import DBSCAN
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine")
    return clustering.fit_predict(vectors).astype(np.int32)


def cluster_upload_responses(
    user_id: int,
    file_id: int,
    eps: float = DEFAULT_EPS,
    min_samples: int = DEFAULT_MIN_SAMPLES,
    min_cluster_size: int = DEFAULT_MIN_CLUSTER_SIZE,
    n_clusters: int = DEFAULT_N_CLUSTERS,
    method: str = CLUSTER_METHOD_DBSCAN,
    max_points: int = 50000,
) -> Dict[str, Any]:
    """
    Load points for this upload from Qdrant, cluster by embedding similarity,
    return point-level cluster labels and per-cluster summaries (sample texts).

    Methods:
      - dbscan: eps + min_samples (density-based; -1 = noise). Default.
      - hdbscan: min_cluster_size (auto number of clusters; -1 = noise). Good when you don't know K.
      - kmeans: n_clusters (you choose K; no noise).
    """
    points = get_points_for_upload(user_id, file_id, limit=max_points)
    if not points:
        return {
            "point_clusters": [],
            "clusters": [],
            "message": "No embeddings found. Run Themes or re-upload to create embeddings.",
        }
    vectors = np.array([p["vector"] for p in points], dtype=np.float32)
    min_pts = min_samples if method == CLUSTER_METHOD_DBSCAN else min_cluster_size
    if len(vectors) < max(2, min_pts):
        return {
            "point_clusters": [{"index": p["index"], "cluster_id": 0} for p in points],
            "clusters": [{"id": 0, "size": len(points), "sample_texts": [p["text"][:200] for p in points[:MAX_SAMPLE_TEXTS_PER_CLUSTER]]}],
            "message": "Too few points to cluster; all in one group.",
        }
    try:
        labels = _cluster_vectors(
            vectors,
            method=method,
            eps=eps,
            min_samples=min_samples,
            min_cluster_size=min_cluster_size,
            n_clusters=min(n_clusters, len(vectors)),
        )
    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        return {
            "point_clusters": [],
            "clusters": [],
            "message": f"Clustering error: {e}",
        }
    # Build point_clusters (index -> cluster_id); -1 is noise, remap to non-negative for display
    unique_ids = sorted(set(labels))
    noise_id = -1
    id_to_display = {noise_id: -1}
    display = 0
    for uid in unique_ids:
        if uid != noise_id:
            id_to_display[uid] = display
            display += 1
    point_clusters = [
        {"index": points[i]["index"], "cluster_id": int(labels[i]) if labels[i] != noise_id else -1}
        for i in range(len(points))
    ]
    # Build clusters: id, size, sample_texts, row_indices (original CSV row indices for Summaries by theme)
    cluster_to_indices: Dict[int, List[int]] = {}
    for i, lab in enumerate(labels):
        if lab not in cluster_to_indices:
            cluster_to_indices[lab] = []
        cluster_to_indices[lab].append(i)
    clusters = []
    for cid in unique_ids:
        indices = cluster_to_indices.get(cid, [])
        sample_texts = [points[i]["text"][:300].strip() for i in indices[:MAX_SAMPLE_TEXTS_PER_CLUSTER] if points[i].get("text")]
        row_indices = [points[i]["index"] for i in indices if points[i].get("index") is not None]
        clusters.append({
            "id": int(cid) if cid != noise_id else -1,
            "size": len(indices),
            "sample_texts": sample_texts,
            "row_indices": row_indices,
        })
    return {
        "point_clusters": point_clusters,
        "clusters": clusters,
        "message": None,
    }
