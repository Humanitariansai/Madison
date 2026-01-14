"""
Vector database integration for semantic search and embeddings storage
Supports Qdrant (self-hosted) and Pinecone (managed)
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Vector DB client (lazy initialization)
_vector_db_client = None
_vector_db_type = None

def get_vector_db_client():
    """Get or create vector database client"""
    global _vector_db_client, _vector_db_type
    
    if _vector_db_client is None:
        import os
        
        # Try Qdrant first (self-hosted, free)
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            _vector_db_client = QdrantClient(url=qdrant_url)
            _vector_db_type = "qdrant"
            
            # Test connection
            _vector_db_client.get_collections()
            logger.info(f"Connected to Qdrant at {qdrant_url}")
        except ImportError:
            logger.warning("Qdrant client not installed. Install with: pip install qdrant-client")
        except Exception as e:
            logger.warning(f"Qdrant not available: {e}. Vector DB disabled.")
            _vector_db_client = None
    
    return _vector_db_client, _vector_db_type

def ensure_collection(collection_name: str, vector_size: int = 384):
    """Ensure collection exists in vector DB"""
    client, db_type = get_vector_db_client()
    if not client:
        return False
    
    try:
        if db_type == "qdrant":
            from qdrant_client.models import Distance, VectorParams
            
            # Check if collection exists
            collections = client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if collection_name not in collection_names:
                # Create collection
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {collection_name}")
            return True
    except Exception as e:
        logger.error(f"Error ensuring collection: {e}")
        return False

def store_embeddings(
    collection_name: str,
    embeddings: np.ndarray,
    texts: List[str],
    metadata: Optional[List[Dict]] = None
) -> bool:
    """
    Store embeddings in vector database
    
    Args:
        collection_name: Name of collection
        embeddings: numpy array of embeddings (n_texts, embedding_dim)
        texts: List of original texts
        metadata: Optional list of metadata dicts
    
    Returns:
        True if successful
    """
    client, db_type = get_vector_db_client()
    if not client:
        return False
    
    try:
        if db_type == "qdrant":
            from qdrant_client.models import PointStruct
            
            # Ensure collection exists
            vector_size = embeddings.shape[1]
            ensure_collection(collection_name, vector_size)
            
            # Prepare points
            points = []
            for i, (embedding, text) in enumerate(zip(embeddings, texts)):
                payload = {
                    "text": text,
                    "index": i
                }
                if metadata and i < len(metadata):
                    payload.update(metadata[i])
                
                points.append(
                    PointStruct(
                        id=i,
                        vector=embedding.tolist(),
                        payload=payload
                    )
                )
            
            # Upsert points
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"Stored {len(points)} embeddings in {collection_name}")
            return True
    except Exception as e:
        logger.error(f"Error storing embeddings: {e}")
        return False

def semantic_search(
    collection_name: str,
    query_embedding: np.ndarray,
    top_k: int = 10,
    score_threshold: float = 0.5
) -> List[Dict]:
    """
    Perform semantic search in vector database
    
    Args:
        collection_name: Name of collection
        query_embedding: Query embedding vector
        top_k: Number of results to return
        score_threshold: Minimum similarity score
    
    Returns:
        List of results with text, score, and metadata
    """
    client, db_type = get_vector_db_client()
    if not client:
        return []
    
    try:
        if db_type == "qdrant":
            results = client.search(
                collection_name=collection_name,
                query_vector=query_embedding.tolist(),
                limit=top_k,
                score_threshold=score_threshold
            )
            
            return [
                {
                    "text": hit.payload.get("text", ""),
                    "score": hit.score,
                    "metadata": {k: v for k, v in hit.payload.items() if k != "text"}
                }
                for hit in results
            ]
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        return []

def find_similar_responses(
    collection_name: str,
    query_text: str,
    top_k: int = 10,
    score_threshold: float = 0.5
) -> List[Dict]:
    """
    Find similar responses using semantic search
    Falls back to TF-IDF if PyTorch is unavailable
    """
    # Try PyTorch-based embeddings first
    try:
        from src.embeddings import generate_embeddings
        query_embedding = generate_embeddings([query_text])[0]
        
        # Search in vector DB
        return semantic_search(
            collection_name,
            query_embedding,
            top_k=top_k,
            score_threshold=score_threshold
        )
    except (ImportError, RuntimeError) as e:
        error_msg = str(e)
        if "DLL" in error_msg or "torch" in error_msg.lower() or "PyTorch" in error_msg:
            # PyTorch unavailable - return empty, will be handled in app.py with file_path
            logger.info("PyTorch unavailable, TF-IDF fallback will be used in app.py")
            return []
        else:
            logger.warning(f"Embeddings error: {e}")
            return []
    except Exception as e:
        logger.warning(f"Error in semantic search: {e}")
        return []

def find_similar_responses_tfidf_fallback(
    file_path: str,
    query_text: str,
    text_col: str,
    top_k: int = 10,
    score_threshold: float = 0.3
) -> List[Dict]:
    """
    Fallback semantic search using TF-IDF when PyTorch is unavailable
    This function is called directly from app.py with file_path
    """
    try:
        from src.embeddings_fallback import generate_embeddings_tfidf, find_similar_responses_tfidf
        from src.ingestion import ingest_and_prepare
        
        # Load data
        df_raw, report = ingest_and_prepare(file_path)
        texts = df_raw[text_col].astype(str).tolist()
        
        # Limit texts
        max_texts = 10000
        if len(texts) > max_texts:
            texts = texts[:max_texts]
        
        # Generate TF-IDF embeddings
        embeddings = generate_embeddings_tfidf(texts)
        
        if embeddings.shape[0] == 0:
            return []
        
        # Find similar using TF-IDF
        similar = find_similar_responses_tfidf(
            query_text,
            embeddings,
            texts,
            top_k=top_k,
            threshold=score_threshold
        )
        
        # Convert to expected format
        results = [
            {
                "text": text,
                "score": score,
                "metadata": {"index": idx, "method": "tfidf_fallback"}
            }
            for text, score, idx in similar
        ]
        
        return results
    except Exception as e:
        logger.error(f"TF-IDF fallback failed: {e}")
        return []

def delete_collection(collection_name: str) -> bool:
    """Delete a collection from vector DB"""
    client, db_type = get_vector_db_client()
    if not client:
        return False
    
    try:
        if db_type == "qdrant":
            client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
    except Exception as e:
        logger.error(f"Error deleting collection: {e}")
        return False

