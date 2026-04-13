"""
Improved theme matching using semantic similarity
"""
import logging
import numpy as np
from typing import List, Dict, Set
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Track if embeddings are available (can be disabled if PyTorch fails)
EMBEDDINGS_AVAILABLE = False
_EMBEDDINGS_CHECKED = False

def _check_embeddings_availability():
    """Check if embeddings are available, set global flag"""
    global EMBEDDINGS_AVAILABLE, _EMBEDDINGS_CHECKED
    
    if _EMBEDDINGS_CHECKED:
        return EMBEDDINGS_AVAILABLE
    
    _EMBEDDINGS_CHECKED = True
    
    try:
        from src.embeddings import generate_embeddings
        # Try a simple test to see if PyTorch works
        test_embedding = generate_embeddings(["test"], batch_size=1)
        if len(test_embedding) > 0:
            EMBEDDINGS_AVAILABLE = True
            logger.info("✅ Semantic embeddings available (sentence-transformers)")
        else:
            EMBEDDINGS_AVAILABLE = False
            logger.warning("⚠️ Embeddings returned empty, using word-based matching")
    except (ImportError, RuntimeError) as e:
        EMBEDDINGS_AVAILABLE = False
        if "torch" in str(e).lower() or "pytorch" in str(e).lower() or "DLL" in str(e):
            logger.warning("⚠️ PyTorch initialization failed (Windows compatibility issue). Using word-based matching fallback.")
            logger.info("💡 To enable semantic matching, install PyTorch CPU version: pip install torch --index-url https://download.pytorch.org/whl/cpu")
        else:
            logger.warning(f"⚠️ Embeddings not available: {e}. Using word-based matching fallback.")
    except Exception as e:
        EMBEDDINGS_AVAILABLE = False
        logger.warning(f"⚠️ Embeddings check failed: {e}. Using word-based matching fallback.")
    
    return EMBEDDINGS_AVAILABLE


def match_theme_to_texts_semantic(
    theme: str,
    texts: List[str],
    similarity_threshold: float = 0.5
) -> List[int]:
    """
    Match a theme to texts using semantic similarity (embeddings).
    
    Args:
        theme: Theme keyphrase to match
        texts: List of text strings to search
        similarity_threshold: Minimum cosine similarity (0-1)
    
    Returns:
        List of indices of matching texts
    """
    global EMBEDDINGS_AVAILABLE  # Declare global at the top
    
    if not theme or not texts:
        return []
    
    # Check if embeddings are available (only check once)
    if not _EMBEDDINGS_CHECKED:
        _check_embeddings_availability()
    
    matches = []
    
    if EMBEDDINGS_AVAILABLE:
        try:
            # Generate embedding for theme
            theme_embedding = generate_embeddings([theme], batch_size=1)
            if len(theme_embedding) == 0:
                return _match_theme_to_texts_fallback(theme, texts)
            
            # Generate embeddings for all texts (batch for efficiency)
            text_embeddings = generate_embeddings(texts, batch_size=32)
            
            if len(text_embeddings) != len(texts):
                logger.warning(f"⚠️ Embedding count mismatch: {len(text_embeddings)} vs {len(texts)}")
                return _match_theme_to_texts_fallback(theme, texts)
            
            # Calculate cosine similarity
            similarities = cosine_similarity(theme_embedding, text_embeddings)[0]
            
            # Find matches above threshold
            for idx, sim in enumerate(similarities):
                if sim >= similarity_threshold:
                    matches.append(idx)
            
            logger.debug(f"   Semantic match: '{theme[:40]}' → {len(matches)}/{len(texts)} texts (threshold={similarity_threshold})")
            
        except (RuntimeError, ImportError) as e:
            # PyTorch/PyTorch-related errors - disable embeddings for this session
            if "torch" in str(e).lower() or "pytorch" in str(e).lower() or "DLL" in str(e):
                EMBEDDINGS_AVAILABLE = False
                logger.debug(f"⚠️ Disabling embeddings due to PyTorch error, using fallback for '{theme[:40]}'")
            else:
                logger.debug(f"⚠️ Semantic matching failed for theme '{theme[:40]}': {e}, using fallback")
            return _match_theme_to_texts_fallback(theme, texts)
        except Exception as e:
            logger.debug(f"⚠️ Semantic matching failed for theme '{theme[:40]}': {e}, using fallback")
            return _match_theme_to_texts_fallback(theme, texts)
    else:
        return _match_theme_to_texts_fallback(theme, texts)
    
    return matches


def _match_theme_to_texts_fallback(
    theme: str,
    texts: List[str]
) -> List[int]:
    """
    Fallback matching using word overlap and substring matching.
    This is used when semantic embeddings are unavailable (e.g., PyTorch fails on Windows).
    
    Args:
        theme: Theme keyphrase
        texts: List of text strings
    
    Returns:
        List of indices of matching texts
    """
    matches = []
    theme_lower = theme.lower().strip()
    theme_words = set(theme_lower.split())
    
    # Remove common stopwords for better matching
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'this', 'that', 'these', 'those'}
    theme_words_filtered = theme_words - stopwords
    
    # If theme is all stopwords or empty, use substring matching
    if len(theme_words_filtered) == 0:
        for idx, text in enumerate(texts):
            if theme_lower in text.lower():
                matches.append(idx)
        return matches
    
    # Try multiple matching strategies for better recall
    for idx, text in enumerate(texts):
        text_lower = text.lower()
        text_words = set(text_lower.split())
        
        # Strategy 1: Check word overlap (at least 40% of theme words)
        overlap = len(theme_words_filtered & text_words)
        word_overlap_ratio = overlap / len(theme_words_filtered) if len(theme_words_filtered) > 0 else 0
        
        # Strategy 2: Check substring match (for multi-word themes)
        substring_match = theme_lower in text_lower
        
        # Strategy 3: Check if any significant word from theme appears
        # (for themes like "integration limitations" matching "limited integration options")
        significant_words = [w for w in theme_words_filtered if len(w) > 3]  # Words longer than 3 chars
        if significant_words:
            significant_match = any(word in text_lower for word in significant_words)
        else:
            significant_match = False
        
        # Strategy 4: Check for word stems/variations (simple pluralization)
        # e.g., "limitation" matches "limitations", "integration" matches "integrations"
        stem_match = False
        for word in theme_words_filtered:
            if len(word) > 4:  # Only for longer words
                # Check if word or its plural form appears
                if word in text_lower or (word + 's') in text_lower or (word + 'es') in text_lower:
                    stem_match = True
                    break
                # Check reverse (plural -> singular)
                if word.endswith('s') and word[:-1] in text_lower:
                    stem_match = True
                    break
        
        # Match if any strategy succeeds
        # Lower threshold for word overlap to catch more matches
        if word_overlap_ratio >= 0.35 or substring_match or (significant_match and len(theme_words_filtered) <= 3) or stem_match:
            matches.append(idx)
    
    return matches


def create_theme_mask_semantic(
    df,
    text_col: str,
    theme: str,
    similarity_threshold: float = 0.5
) -> np.ndarray:
    """
    Create a boolean mask for rows that match the theme using semantic similarity.
    
    Args:
        df: DataFrame
        text_col: Name of text column
        theme: Theme keyphrase
        similarity_threshold: Minimum cosine similarity (0-1)
    
    Returns:
        Boolean numpy array (True for matching rows)
    """
    if df.empty or theme not in df.columns if text_col not in df.columns else False:
        return np.zeros(len(df), dtype=bool)
    
    texts = df[text_col].astype(str).tolist()
    matching_indices = match_theme_to_texts_semantic(theme, texts, similarity_threshold)
    
    mask = np.zeros(len(df), dtype=bool)
    mask[matching_indices] = True
    
    return mask

