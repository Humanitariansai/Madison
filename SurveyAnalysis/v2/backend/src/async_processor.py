"""
Async/background processing for large files
Uses Celery for distributed task processing
"""
import os
from typing import Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Check if Celery is available
try:
    from celery import Celery
    from celery.result import AsyncResult
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not installed. Async processing disabled.")

# Redis URL for Celery broker
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

if CELERY_AVAILABLE:
    celery_app = Celery(
        'survey_analysis',
        broker=REDIS_URL,
        backend=REDIS_URL
    )
    
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1 hour max
        task_soft_time_limit=3300,  # 55 minutes soft limit
    )

@celery_app.task(bind=True, name='process_large_file')
def process_large_file_task(
    self,
    file_id: int,
    user_id: int,
    operation: str,
    **kwargs
) -> Dict:
    """
    Background task to process large files
    
    Args:
        file_id: File history ID
        user_id: User ID
        operation: 'sentiment', 'themes', 'embeddings', etc.
        **kwargs: Operation-specific parameters
    
    Returns:
        Processing results
    """
    from src.database import SessionLocal
    from src.models import FileHistory
    from src.large_file_processor import (
        analyze_sentiment_chunked,
        extract_themes_chunked,
        generate_embeddings_chunked
    )
    
    db = SessionLocal()
    
    try:
        # Get file info
        file_history = db.query(FileHistory).filter(
            FileHistory.id == file_id,
            FileHistory.user_id == user_id
        ).first()
        
        if not file_history:
            raise ValueError(f"File {file_id} not found")
        
        file_path = file_history.file_path
        text_col = kwargs.get('text_col', 'text')
        
        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={'progress': 0, 'status': f'Starting {operation}...'}
        )
        
        # Process based on operation
        if operation == 'sentiment':
            result = analyze_sentiment_chunked(
                file_path,
                text_col,
                chunk_size=kwargs.get('chunk_size', 10000)
            )
        elif operation == 'themes':
            result = extract_themes_chunked(
                file_path,
                text_col,
                top_k=kwargs.get('top_k', 20),
                use_topic_modeling=kwargs.get('use_topic_modeling', False)
            )
        elif operation == 'embeddings':
            embeddings = generate_embeddings_chunked(
                file_path,
                text_col,
                chunk_size=kwargs.get('chunk_size', 1000)
            )
            result = {
                "embeddings_shape": embeddings.shape,
                "num_embeddings": embeddings.shape[0]
            }
            # TODO: Store embeddings in database/cache
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        # Update final state
        self.update_state(
            state='SUCCESS',
            meta={'progress': 100, 'status': 'Completed', 'result': result}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in background task: {e}")
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
    finally:
        db.close()

def start_async_processing(
    file_id: int,
    user_id: int,
    operation: str,
    **kwargs
) -> Optional[str]:
    """
    Start async processing and return task ID
    
    Returns:
        Task ID if Celery available, None otherwise
    """
    if not CELERY_AVAILABLE:
        logger.warning("Celery not available, processing synchronously")
        return None
    
    task = process_large_file_task.delay(file_id, user_id, operation, **kwargs)
    return task.id

def get_task_status(task_id: str) -> Dict:
    """
    Get status of async task
    """
    if not CELERY_AVAILABLE:
        return {"status": "NOT_AVAILABLE"}
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "status": task_result.status,
        "progress": task_result.info.get("progress", 0) if task_result.info else 0,
        "message": task_result.info.get("status", "") if task_result.info else "",
        "result": task_result.result if task_result.ready() else None,
        "error": str(task_result.info.get("error")) if task_result.failed() else None
    }

def cancel_task(task_id: str) -> bool:
    """
    Cancel an async task
    """
    if not CELERY_AVAILABLE:
        return False
    
    celery_app.control.revoke(task_id, terminate=True)
    return True

