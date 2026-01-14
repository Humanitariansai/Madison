"""
Redis caching layer for analysis results
Prevents reprocessing same data and improves response times
"""
import redis
import json
import hashlib
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Redis client (lazy initialization)
_redis_client = None

def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        try:
            import os
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            
            _redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Caching disabled.")
            _redis_client = None
    return _redis_client

def get_cache_key(operation: str, file_id: int, params: Dict[str, Any]) -> str:
    """Generate cache key from operation and parameters"""
    # Sort params for consistent keys
    param_str = json.dumps(params, sort_keys=True, default=str)
    param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
    return f"analysis:{operation}:{file_id}:{param_hash}"

def get_cached_result(cache_key: str) -> Optional[Dict]:
    """Get cached result if exists"""
    client = get_redis_client()
    if not client:
        return None
    
    try:
        cached = client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Error reading cache: {e}")
    return None

def cache_result(cache_key: str, result: Dict, ttl: int = 3600) -> bool:
    """Cache result with TTL (default 1 hour)"""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.setex(
            cache_key,
            ttl,
            json.dumps(result, default=str)
        )
        return True
    except Exception as e:
        logger.warning(f"Error writing cache: {e}")
        return False

def invalidate_cache(file_id: int, operation: Optional[str] = None) -> int:
    """Invalidate all cache entries for a file (or specific operation)"""
    client = get_redis_client()
    if not client:
        return 0
    
    try:
        pattern = f"analysis:{operation or '*'}:{file_id}:*"
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"Error invalidating cache: {e}")
        return 0

def cache_theme_result(file_id: int, params: Dict, result: Dict, ttl: int = 3600) -> bool:
    """Cache theme extraction results"""
    cache_key = get_cache_key("themes", file_id, params)
    return cache_result(cache_key, result, ttl)

def get_cached_theme_result(file_id: int, params: Dict) -> Optional[Dict]:
    """Get cached theme extraction results"""
    cache_key = get_cache_key("themes", file_id, params)
    return get_cached_result(cache_key)

def cache_sentiment_result(file_id: int, params: Dict, result: Dict, ttl: int = 3600) -> bool:
    """Cache sentiment analysis results"""
    cache_key = get_cache_key("sentiment", file_id, params)
    return cache_result(cache_key, result, ttl)

def get_cached_sentiment_result(file_id: int, params: Dict) -> Optional[Dict]:
    """Get cached sentiment analysis results"""
    cache_key = get_cache_key("sentiment", file_id, params)
    return get_cached_result(cache_key)

def cache_trend_result(file_id: int, params: Dict, result: Dict, ttl: int = 3600) -> bool:
    """Cache trend analysis results"""
    cache_key = get_cache_key("trends", file_id, params)
    return cache_result(cache_key, result, ttl)

def get_cached_trend_result(file_id: int, params: Dict) -> Optional[Dict]:
    """Get cached trend analysis results"""
    cache_key = get_cache_key("trends", file_id, params)
    return get_cached_result(cache_key)

