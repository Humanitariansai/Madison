"""
Enhanced theme analysis: sentiment per theme and temporal trends
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def analyze_theme_sentiment(
    df: pd.DataFrame,
    themes: List[str],
    text_col: str
) -> pd.DataFrame:
    """
    Analyze sentiment for each theme.
    
    Returns DataFrame with columns:
    - keyphrase: theme name
    - total_mentions: total number of mentions
    - positive_count: number of positive mentions
    - negative_count: number of negative mentions
    - neutral_count: number of neutral mentions
    - positive_pct: percentage of positive mentions
    - negative_pct: percentage of negative mentions
    - neutral_pct: percentage of neutral mentions
    - avg_sentiment: average sentiment compound score (-1 to 1)
    - dominant_sentiment: 'positive', 'negative', or 'neutral'
    """
    if not themes or df.empty:
        return pd.DataFrame(columns=[
            "keyphrase", "total_mentions", "positive_count", "negative_count", 
            "neutral_count", "positive_pct", "negative_pct", "neutral_pct",
            "avg_sentiment", "dominant_sentiment"
        ])
    
    # Ensure sentiment columns exist
    if "sent_label" not in df.columns or "sent_compound" not in df.columns:
        logger.warning("Sentiment columns not found. Run sentiment analysis first.")
        return pd.DataFrame(columns=[
            "keyphrase", "total_mentions", "positive_count", "negative_count", 
            "neutral_count", "positive_pct", "negative_pct", "neutral_pct",
            "avg_sentiment", "dominant_sentiment"
        ])
    
    results = []
    
    for theme in themes:
        if not isinstance(theme, str) or not theme.strip():
            continue
        
        # Find rows mentioning this theme
        mask = df[text_col].astype(str).str.contains(theme, case=False, na=False)
        
        if not mask.any():
            continue
        
        theme_df = df[mask]
        
        # Count sentiment labels
        sentiment_counts = theme_df["sent_label"].value_counts()
        positive_count = int(sentiment_counts.get("positive", 0))
        negative_count = int(sentiment_counts.get("negative", 0))
        neutral_count = int(sentiment_counts.get("neutral", 0))
        total_mentions = len(theme_df)
        
        # Calculate percentages
        positive_pct = (positive_count / total_mentions) * 100 if total_mentions > 0 else 0.0
        negative_pct = (negative_count / total_mentions) * 100 if total_mentions > 0 else 0.0
        neutral_pct = (neutral_count / total_mentions) * 100 if total_mentions > 0 else 0.0
        
        # Average sentiment compound score
        avg_sentiment = float(theme_df["sent_compound"].mean()) if total_mentions > 0 else 0.0
        
        # Determine dominant sentiment
        if positive_pct > negative_pct and positive_pct > neutral_pct:
            dominant_sentiment = "positive"
        elif negative_pct > positive_pct and negative_pct > neutral_pct:
            dominant_sentiment = "negative"
        else:
            dominant_sentiment = "neutral"
        
        results.append({
            "keyphrase": theme,
            "total_mentions": total_mentions,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "positive_pct": round(positive_pct, 2),
            "negative_pct": round(negative_pct, 2),
            "neutral_pct": round(neutral_pct, 2),
            "avg_sentiment": round(avg_sentiment, 3),
            "dominant_sentiment": dominant_sentiment
        })
    
    return pd.DataFrame(results)


def analyze_themes_over_time(
    df: pd.DataFrame,
    themes: List[str],
    text_col: str,
    time_col: Optional[str] = None,
    freq: str = "W"
) -> pd.DataFrame:
    """
    Analyze how themes change over time.
    
    Returns DataFrame with columns:
    - keyphrase: theme name
    - period: time period (date string)
    - mention_count: number of mentions in this period
    - positive_count: positive mentions
    - negative_count: negative mentions
    - neutral_count: neutral mentions
    - positive_pct: percentage positive
    - negative_pct: percentage negative
    - avg_sentiment: average sentiment for this period
    - sentiment_trend: change in sentiment from previous period
    """
    if not themes or df.empty:
        return pd.DataFrame(columns=[
            "keyphrase", "period", "mention_count", "positive_count", 
            "negative_count", "neutral_count", "positive_pct", "negative_pct",
            "avg_sentiment", "sentiment_trend"
        ])
    
    # Check if time column exists
    if not time_col or time_col not in df.columns:
        # Return overall stats without time dimension
        return _get_overall_theme_stats(df, themes, text_col)
    
    # Ensure sentiment columns exist
    if "sent_label" not in df.columns or "sent_compound" not in df.columns:
        logger.warning("Sentiment columns not found. Run sentiment analysis first.")
        return pd.DataFrame(columns=[
            "keyphrase", "period", "mention_count", "positive_count", 
            "negative_count", "neutral_count", "positive_pct", "negative_pct",
            "avg_sentiment", "sentiment_trend"
        ])
    
    results = []
    
    # Convert time column to datetime
    df_copy = df.copy()
    df_copy[time_col] = pd.to_datetime(df_copy[time_col], errors="coerce")
    df_copy = df_copy.dropna(subset=[time_col])
    
    if df_copy.empty:
        return _get_overall_theme_stats(df, themes, text_col)
    
    # Create period column based on frequency
    if freq == "D":
        df_copy["period"] = df_copy[time_col].dt.normalize()
    elif freq == "W":
        df_copy["period"] = df_copy[time_col].dt.to_period("W").dt.start_time.dt.normalize()
    elif freq == "M":
        df_copy["period"] = df_copy[time_col].dt.to_period("M").dt.start_time.dt.normalize()
    else:
        df_copy["period"] = df_copy[time_col].dt.normalize()
    
    # Analyze each theme
    for theme in themes:
        if not isinstance(theme, str) or not theme.strip():
            continue
        
        # Find rows mentioning this theme
        mask = df_copy[text_col].astype(str).str.contains(theme, case=False, na=False)
        theme_df = df_copy[mask]
        
        if theme_df.empty:
            continue
        
        # Group by period
        for period, period_df in theme_df.groupby("period"):
            mention_count = len(period_df)
            
            # Count sentiment labels
            sentiment_counts = period_df["sent_label"].value_counts()
            positive_count = int(sentiment_counts.get("positive", 0))
            negative_count = int(sentiment_counts.get("negative", 0))
            neutral_count = int(sentiment_counts.get("neutral", 0))
            
            # Calculate percentages
            positive_pct = (positive_count / mention_count) * 100 if mention_count > 0 else 0.0
            negative_pct = (negative_count / mention_count) * 100 if mention_count > 0 else 0.0
            
            # Average sentiment
            avg_sentiment = float(period_df["sent_compound"].mean()) if mention_count > 0 else 0.0
            
            results.append({
                "keyphrase": theme,
                "period": period.strftime("%Y-%m-%d") if hasattr(period, "strftime") else str(period),
                "mention_count": mention_count,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "neutral_count": neutral_count,
                "positive_pct": round(positive_pct, 2),
                "negative_pct": round(negative_pct, 2),
                "avg_sentiment": round(avg_sentiment, 3),
                "sentiment_trend": 0.0  # Will calculate below
            })
    
    # Calculate sentiment trends (change from previous period)
    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df = result_df.sort_values(["keyphrase", "period"])
        
        # Calculate trend: difference in avg_sentiment from previous period
        result_df["sentiment_trend"] = result_df.groupby("keyphrase")["avg_sentiment"].diff().fillna(0.0)
        result_df["sentiment_trend"] = result_df["sentiment_trend"].round(3)
    
    return result_df


def _get_overall_theme_stats(
    df: pd.DataFrame,
    themes: List[str],
    text_col: str
) -> pd.DataFrame:
    """Get overall theme stats when time column is not available."""
    if "sent_label" not in df.columns or "sent_compound" not in df.columns:
        return pd.DataFrame(columns=[
            "keyphrase", "period", "mention_count", "positive_count", 
            "negative_count", "neutral_count", "positive_pct", "negative_pct",
            "avg_sentiment", "sentiment_trend"
        ])
    
    results = []
    
    for theme in themes:
        if not isinstance(theme, str) or not theme.strip():
            continue
        
        mask = df[text_col].astype(str).str.contains(theme, case=False, na=False)
        theme_df = df[mask]
        
        if theme_df.empty:
            continue
        
        mention_count = len(theme_df)
        sentiment_counts = theme_df["sent_label"].value_counts()
        positive_count = int(sentiment_counts.get("positive", 0))
        negative_count = int(sentiment_counts.get("negative", 0))
        neutral_count = int(sentiment_counts.get("neutral", 0))
        
        positive_pct = (positive_count / mention_count) * 100 if mention_count > 0 else 0.0
        negative_pct = (negative_count / mention_count) * 100 if mention_count > 0 else 0.0
        avg_sentiment = float(theme_df["sent_compound"].mean()) if mention_count > 0 else 0.0
        
        results.append({
            "keyphrase": theme,
            "period": "all",
            "mention_count": mention_count,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "positive_pct": round(positive_pct, 2),
            "negative_pct": round(negative_pct, 2),
            "avg_sentiment": round(avg_sentiment, 3),
            "sentiment_trend": 0.0
        })
    
    return pd.DataFrame(results)


def get_overall_theme_trends(
    theme_temporal_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Get overall trends across all themes.
    
    Returns aggregated statistics per period showing:
    - Total mentions across all themes
    - Overall sentiment distribution
    - Average sentiment per period
    """
    if theme_temporal_df.empty:
        return pd.DataFrame(columns=[
            "period", "total_mentions", "total_positive", "total_negative", 
            "total_neutral", "avg_sentiment", "sentiment_index"
        ])
    
    # Group by period and aggregate
    agg_df = theme_temporal_df.groupby("period").agg({
        "mention_count": "sum",
        "positive_count": "sum",
        "negative_count": "sum",
        "neutral_count": "sum",
        "avg_sentiment": "mean"  # Average of theme-level averages
    }).reset_index()
    
    agg_df.columns = [
        "period", "total_mentions", "total_positive", "total_negative",
        "total_neutral", "avg_sentiment"
    ]
    
    # Calculate percentages
    agg_df["positive_pct"] = (agg_df["total_positive"] / agg_df["total_mentions"] * 100).round(2)
    agg_df["negative_pct"] = (agg_df["total_negative"] / agg_df["total_mentions"] * 100).round(2)
    agg_df["neutral_pct"] = (agg_df["total_neutral"] / agg_df["total_mentions"] * 100).round(2)
    
    # Calculate sentiment index (positive_pct - negative_pct, normalized to -1 to 1)
    agg_df["sentiment_index"] = ((agg_df["positive_pct"] - agg_df["negative_pct"]) / 100).round(3)
    
    # Calculate trend (change from previous period)
    agg_df["sentiment_trend"] = agg_df["sentiment_index"].diff().fillna(0.0).round(3)
    
    return agg_df.sort_values("period")

