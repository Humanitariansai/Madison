"""
Theme extraction using YAKE and TF-IDF
"""
import pandas as pd
import yake
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Optional
import logging

def extract_themes(
    df: pd.DataFrame,
    text_col: str,
    top_k: int = 20,
    ngram_range: tuple = (1, 3)
) -> pd.DataFrame:
    """
    Extract themes/keyphrases using YAKE and TF-IDF
    Falls back to TF-IDF if YAKE fails
    """
    texts = [t for t in df[text_col].astype(str).tolist() if isinstance(t, str) and t.strip()]
    
    if not texts:
        return pd.DataFrame(columns=["keyphrase", "weight"])
    
    # Try YAKE first
    try:
        combined_text = ' '.join(texts)
        
        kw_extractor = yake.KeywordExtractor(
            lan="en",
            n=ngram_range[1],
            dedupLim=0.7,
            top=top_k
        )
        keywords = kw_extractor.extract_keywords(combined_text)
        
        # YAKE returns (score, keyword) where score is float and lower is better
        # Convert to DataFrame with proper handling
        themes_list = []
        for kw in keywords:
            try:
                # Handle both (score, keyword) and (keyword, score) formats
                if isinstance(kw[0], (int, float)):
                    # Format: (score, keyword)
                    score = float(kw[0])
                    keyphrase = str(kw[1])
                else:
                    # Format: (keyword, score) - reversed
                    keyphrase = str(kw[0])
                    score = float(kw[1])
                
                # Lower score = better, so invert for weight
                weight = 1.0 / (score + 1e-9)
                themes_list.append({"keyphrase": keyphrase, "weight": weight})
            except (IndexError, ValueError, TypeError) as e:
                # Skip invalid entries
                continue
        
        if themes_list:
            return pd.DataFrame(themes_list)
    except Exception as e:
        # YAKE failed, fall back to TF-IDF
        logging.warning(f"YAKE extraction failed: {e}. Falling back to TF-IDF.")
    
    # Fallback to TF-IDF
    return extract_tfidf_themes(texts, top_k=top_k, ngram_range=ngram_range)

def extract_tfidf_themes(
    texts: List[str],
    top_k: int = 20,
    ngram_range: tuple = (1, 3)
) -> pd.DataFrame:
    """
    Extract themes using TF-IDF (fallback method)
    """
    import re
    
    def _clean_text(s: str) -> str:
        s = s.lower()
        s = re.sub(r"[^a-z0-9\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s
    
    # Clean texts
    cleaned_texts = [_clean_text(t) for t in texts if isinstance(t, str) and t.strip()]
    
    if not cleaned_texts:
        return pd.DataFrame(columns=["keyphrase", "weight"])
    
    try:
        vec = TfidfVectorizer(
            ngram_range=ngram_range,
            stop_words="english",
            min_df=1,
            max_df=0.9
        )
        X = vec.fit_transform(cleaned_texts)
        scores = X.sum(axis=0).A1
        terms = vec.get_feature_names_out()
        
        pairs = list(zip(terms, scores))
        pairs.sort(key=lambda x: x[1], reverse=True)
        
        themes_list = [
            {"keyphrase": term, "weight": float(score)}
            for term, score in pairs[:top_k]
        ]
        
        return pd.DataFrame(themes_list)
    except Exception as e:
        logging.error(f"TF-IDF extraction failed: {e}")
        return pd.DataFrame(columns=["keyphrase", "weight"])

