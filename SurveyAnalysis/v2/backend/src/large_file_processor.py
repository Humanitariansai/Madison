"""
Large file processing with chunking and memory efficiency
Handles files with 1M+ rows without running out of memory
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Iterator, Tuple, Dict, List, Optional
import gc
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

# Chunk size for reading CSV (adjust based on available RAM)
DEFAULT_CHUNK_SIZE = 10000  # Process 10k rows at a time

def read_csv_in_chunks(
    file_path: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    encoding: str = 'utf-8-sig'
) -> Iterator[pd.DataFrame]:
    """
    Read large CSV file in chunks to avoid memory issues
    
    Args:
        file_path: Path to CSV file
        chunk_size: Number of rows per chunk
        encoding: File encoding
    
    Yields:
        DataFrame chunks
    """
    try:
        for chunk in pd.read_csv(
            file_path,
            chunksize=chunk_size,
            encoding=encoding,
            on_bad_lines='skip',
            low_memory=False
        ):
            yield chunk
            gc.collect()  # Force garbage collection
    except Exception as e:
        logger.error(f"Error reading CSV chunks: {e}")
        raise

def get_file_info(file_path: str) -> Dict:
    """
    Get file information without loading entire file
    """
    # Read just first few rows to detect columns
    sample = pd.read_csv(file_path, nrows=100, encoding='utf-8-sig', on_bad_lines='skip')
    
    # Count total rows (efficient method)
    total_rows = sum(1 for _ in open(file_path, 'rb')) - 1  # Subtract header
    
    return {
        "columns": list(sample.columns),
        "estimated_rows": total_rows,
        "sample_data": sample.head(5).to_dict('records')
    }

def process_large_file_chunked(
    file_path: str,
    text_col: str,
    process_func,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    show_progress: bool = True,
    **process_kwargs
) -> Dict:
    """
    Process large file in chunks and aggregate results
    
    Args:
        file_path: Path to CSV file
        text_col: Name of text column
        process_func: Function to process each chunk (df_chunk) -> result_dict
        chunk_size: Rows per chunk
        show_progress: Show progress bar
        **process_kwargs: Additional arguments for process_func
    
    Returns:
        Aggregated results from all chunks
    """
    file_info = get_file_info(file_path)
    total_rows = file_info["estimated_rows"]
    
    # Initialize aggregated results
    aggregated_results = {
        "total_rows_processed": 0,
        "chunks_processed": 0,
        "errors": []
    }
    
    # Process chunks
    chunks = read_csv_in_chunks(file_path, chunk_size)
    
    if show_progress:
        chunks = tqdm(chunks, total=total_rows // chunk_size + 1, desc="Processing chunks")
    
    for chunk_idx, chunk in enumerate(chunks):
        try:
            # Validate text column exists
            if text_col not in chunk.columns:
                logger.warning(f"Text column '{text_col}' not found in chunk {chunk_idx}")
                continue
            
            # Process chunk
            chunk_result = process_func(chunk, text_col, **process_kwargs)
            
            # Aggregate results
            aggregated_results["total_rows_processed"] += len(chunk)
            aggregated_results["chunks_processed"] += 1
            
            # Merge chunk results into aggregated
            for key, value in chunk_result.items():
                if key not in aggregated_results:
                    aggregated_results[key] = []
                
                if isinstance(value, (list, dict)):
                    if isinstance(aggregated_results[key], list):
                        aggregated_results[key].extend(value if isinstance(value, list) else [value])
                    elif isinstance(aggregated_results[key], dict):
                        # Merge dictionaries (e.g., sentiment distribution)
                        for k, v in value.items():
                            aggregated_results[key][k] = aggregated_results[key].get(k, 0) + v
                elif isinstance(value, (int, float)):
                    aggregated_results[key] = aggregated_results.get(key, 0) + value
            
            # Force garbage collection
            del chunk
            gc.collect()
            
        except Exception as e:
            error_msg = f"Error processing chunk {chunk_idx}: {str(e)}"
            logger.error(error_msg)
            aggregated_results["errors"].append(error_msg)
            continue
    
    return aggregated_results

def analyze_sentiment_chunked(
    file_path: str,
    text_col: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> Dict:
    """
    Analyze sentiment for large file in chunks
    """
    from src.sentiment import analyze_sentiment
    
    def process_chunk(chunk: pd.DataFrame, text_col: str) -> Dict:
        df_proc = analyze_sentiment(chunk, text_col)
        distribution = df_proc["sent_label"].value_counts().to_dict()
        return {"sentiment_distribution": distribution}
    
    results = process_large_file_chunked(
        file_path,
        text_col,
        process_chunk,
        chunk_size=chunk_size
    )
    
    # Aggregate sentiment distribution
    final_distribution = {}
    if "sentiment_distribution" in results:
        for dist in results["sentiment_distribution"]:
            for label, count in dist.items():
                final_distribution[label] = final_distribution.get(label, 0) + count
    
    results["sentiment_distribution"] = final_distribution
    return results

def extract_themes_chunked(
    file_path: str,
    text_col: str,
    top_k: int = 20,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    use_topic_modeling: bool = False
) -> Dict:
    """
    Extract themes from large file
    For very large files, we sample or use streaming approach
    """
    if use_topic_modeling:
        # Topic modeling needs all data, so we sample
        return extract_themes_sampled(file_path, text_col, top_k, sample_size=100000)
    else:
        # YAKE can work on chunks and aggregate
        from src.themes import extract_themes
        
        all_texts = []
        chunks = read_csv_in_chunks(file_path, chunk_size=50000)  # Larger chunks for themes
        
        for chunk in tqdm(chunks, desc="Collecting texts"):
            if text_col in chunk.columns:
                all_texts.extend(chunk[text_col].astype(str).tolist())
            
            # Limit to prevent memory issues
            if len(all_texts) > 500000:  # Max 500k texts
                break
        
        # Extract themes from aggregated texts
        combined_df = pd.DataFrame({text_col: all_texts[:500000]})
        themes_df = extract_themes(combined_df, text_col, top_k=top_k)
        
        return {
            "themes": themes_df.to_dict("records"),
            "total_texts_analyzed": len(all_texts)
        }

def extract_themes_sampled(
    file_path: str,
    text_col: str,
    top_k: int = 20,
    sample_size: int = 100000
) -> Dict:
    """
    Extract themes using sampling for very large files
    """
    from src.topic_modeling import extract_topics_lda
    
    # Sample rows from file
    total_rows = sum(1 for _ in open(file_path, 'rb')) - 1
    
    if total_rows <= sample_size:
        # Small enough to load all
        df = pd.read_csv(file_path, encoding='utf-8-sig', on_bad_lines='skip')
        texts = df[text_col].astype(str).tolist()
    else:
        # Sample rows
        skip_rows = np.random.choice(
            range(1, total_rows + 1),
            size=total_rows - sample_size,
            replace=False
        )
        df = pd.read_csv(
            file_path,
            skiprows=skip_rows,
            encoding='utf-8-sig',
            on_bad_lines='skip'
        )
        texts = df[text_col].astype(str).tolist()
    
    # Extract topics
    topics, topic_dist = extract_topics_lda(texts, n_topics=top_k)
    
    return {
        "themes": topics,
        "total_texts_analyzed": len(texts),
        "sampling_used": total_rows > sample_size,
        "original_rows": total_rows
    }

def generate_embeddings_chunked(
    file_path: str,
    text_col: str,
    chunk_size: int = 1000,  # Smaller for embeddings (memory intensive)
    max_texts: int = 100000  # Limit total texts
) -> np.ndarray:
    """
    Generate embeddings in chunks to avoid memory issues
    """
    from src.embeddings import generate_embeddings
    
    all_embeddings = []
    texts_collected = 0
    
    chunks = read_csv_in_chunks(file_path, chunk_size=chunk_size)
    
    for chunk in tqdm(chunks, desc="Generating embeddings"):
        if text_col not in chunk.columns:
            continue
        
        chunk_texts = chunk[text_col].astype(str).tolist()
        
        # Limit total texts
        if texts_collected + len(chunk_texts) > max_texts:
            remaining = max_texts - texts_collected
            chunk_texts = chunk_texts[:remaining]
        
        if not chunk_texts:
            break
        
        # Generate embeddings for chunk
        chunk_embeddings = generate_embeddings(chunk_texts, batch_size=32)
        all_embeddings.append(chunk_embeddings)
        
        texts_collected += len(chunk_texts)
        
        if texts_collected >= max_texts:
            break
        
        gc.collect()
    
    if all_embeddings:
        return np.vstack(all_embeddings)
    else:
        return np.array([])

def estimate_processing_time(file_path: str, operation: str = "sentiment") -> Dict:
    """
    Estimate processing time for large file
    """
    file_info = get_file_info(file_path)
    total_rows = file_info["estimated_rows"]
    
    # Rough estimates (rows per second)
    estimates = {
        "sentiment": 10000,  # 10k rows/sec with VADER
        "themes": 1000,      # 1k rows/sec for YAKE
        "embeddings": 100,   # 100 rows/sec for embeddings
        "topic_modeling": 500  # 500 rows/sec for LDA
    }
    
    rows_per_sec = estimates.get(operation, 1000)
    estimated_seconds = total_rows / rows_per_sec
    
    return {
        "estimated_seconds": estimated_seconds,
        "estimated_minutes": estimated_seconds / 60,
        "total_rows": total_rows,
        "operation": operation
    }

