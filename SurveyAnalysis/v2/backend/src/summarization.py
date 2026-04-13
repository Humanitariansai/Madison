"""
Multi-level summarization for survey analysis
Generates summaries at different levels: overall, by theme, by segment
"""
import pandas as pd
from typing import List, Dict, Optional
from src.config import load_env
from src.ai import summarize_overall

env = load_env()
OPENAI_API_KEY = env.get("OPENAI_API_KEY", "")

def summarize_by_theme(
    df: pd.DataFrame,
    text_col: str,
    theme: str,
    max_length: int = 200
) -> str:
    """
    Generate summary for a specific theme
    
    Args:
        df: DataFrame with survey responses
        text_col: Name of text column
        theme: Theme/keyword to filter by
        max_length: Maximum summary length
    
    Returns:
        Summary text
    """
    # Filter responses containing the theme
    theme_responses = df[
        df[text_col].astype(str).str.contains(theme, case=False, na=False)
    ]
    
    if len(theme_responses) == 0:
        return f"No responses found for theme: {theme}"
    
    # Get sample of responses
    sample_size = min(50, len(theme_responses))
    sample_texts = theme_responses[text_col].head(sample_size).astype(str).tolist()
    
    # Generate summary using OpenAI if available
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            # Combine sample texts
            combined_text = "\n".join([f"- {text}" for text in sample_texts[:20]])
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": f"Summarize the following customer feedback about '{theme}'. Focus on common patterns, pain points, and suggestions. Keep it under {max_length} words."
                }, {
                    "role": "user",
                    "content": f"Feedback about {theme}:\n{combined_text}"
                }],
                max_tokens=min(max_length * 2, 500)
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Fallback to simple summary
            pass
    
    # Fallback: Simple statistical summary
    total = len(theme_responses)
    avg_length = theme_responses[text_col].astype(str).str.len().mean()
    return f"Found {total} responses mentioning '{theme}'. Average response length: {avg_length:.0f} characters."

def summarize_by_segment(
    df: pd.DataFrame,
    text_col: str,
    segment_col: str,
    segment_value: str,
    max_length: int = 200
) -> str:
    """
    Generate summary for a specific segment (e.g., region, product)
    
    Args:
        df: DataFrame with survey responses
        text_col: Name of text column
        segment_col: Name of segment column
        segment_value: Value to filter by
        max_length: Maximum summary length
    
    Returns:
        Summary text
    """
    # Filter by segment
    segment_df = df[df[segment_col] == segment_value]
    
    if len(segment_df) == 0:
        return f"No responses found for segment: {segment_value}"
    
    # Get sample of responses
    sample_texts = segment_df[text_col].head(50).astype(str).tolist()
    
    # Generate summary using OpenAI if available
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            combined_text = "\n".join([f"- {text}" for text in sample_texts[:20]])
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": f"Summarize customer feedback for {segment_col}={segment_value}. Focus on key themes and insights. Keep it under {max_length} words."
                }, {
                    "role": "user",
                    "content": f"Feedback:\n{combined_text}"
                }],
                max_tokens=min(max_length * 2, 500)
            )
            return response.choices[0].message.content.strip()
        except Exception:
            pass
    
    # Fallback
    total = len(segment_df)
    return f"Found {total} responses for {segment_col}={segment_value}."

def generate_multi_level_summaries(
    df: pd.DataFrame,
    text_col: str,
    themes: List[str],
    segment_col: Optional[str] = None,
    time_col: Optional[str] = None
) -> Dict:
    """
    Generate multi-level summaries: overall, by theme, by segment
    
    Args:
        df: DataFrame with survey responses
        text_col: Name of text column
        themes: List of themes to summarize
        segment_col: Optional segment column (e.g., 'region', 'product')
        time_col: Optional time column for temporal analysis
    
    Returns:
        Dictionary with summaries at different levels
    """
    summaries = {
        "overall": None,
        "by_theme": {},
        "by_segment": {},
        "statistics": {
            "total_responses": len(df),
            "themes_analyzed": len(themes)
        }
    }
    
    # Overall summary
    try:
        # Get sample of all responses
        sample_texts = df[text_col].head(100).astype(str).tolist()
        combined_text = "\n".join([f"- {text}" for text in sample_texts[:50]])
        
        if OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_API_KEY)
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{
                        "role": "system",
                        "content": "Summarize the overall customer feedback. Highlight main themes, sentiment trends, and key insights. Keep it concise (150-200 words)."
                    }, {
                        "role": "user",
                        "content": f"Customer feedback:\n{combined_text}"
                    }],
                    max_tokens=400
                )
                summaries["overall"] = response.choices[0].message.content.strip()
            except Exception:
                summaries["overall"] = f"Analyzed {len(df)} responses across {len(themes)} themes."
        else:
            summaries["overall"] = f"Analyzed {len(df)} responses across {len(themes)} themes."
    except Exception:
        summaries["overall"] = "Unable to generate overall summary."
    
    # Summaries by theme
    for theme in themes[:10]:  # Limit to top 10 themes
        try:
            summaries["by_theme"][theme] = summarize_by_theme(df, text_col, theme)
        except Exception as e:
            summaries["by_theme"][theme] = f"Error summarizing theme {theme}: {str(e)}"
    
    # Summaries by segment (if segment column exists)
    if segment_col and segment_col in df.columns:
        try:
            unique_segments = df[segment_col].dropna().unique()[:5]  # Top 5 segments
            for segment_value in unique_segments:
                summaries["by_segment"][str(segment_value)] = summarize_by_segment(
                    df, text_col, segment_col, segment_value
                )
        except Exception:
            pass
    
    return summaries

def generate_executive_summary(
    summaries: Dict,
    sentiment_dist: Dict,
    top_themes: List[str]
) -> str:
    """
    Generate executive-level summary combining all insights
    
    Args:
        summaries: Multi-level summaries dictionary
        sentiment_dist: Sentiment distribution
        top_themes: Top themes list
    
    Returns:
        Executive summary text
    """
    total = summaries.get("statistics", {}).get("total_responses", 0)
    positive = sentiment_dist.get("positive", 0)
    negative = sentiment_dist.get("negative", 0)
    neutral = sentiment_dist.get("neutral", 0)
    
    # Calculate percentages
    if total > 0:
        pos_pct = (positive / total) * 100
        neg_pct = (negative / total) * 100
    else:
        pos_pct = neg_pct = 0
    
    summary_parts = [
        f"## Executive Summary",
        f"",
        f"**Total Responses:** {total:,}",
        f"**Sentiment Distribution:**",
        f"  - Positive: {pos_pct:.1f}% ({positive:,})",
        f"  - Negative: {neg_pct:.1f}% ({negative:,})",
        f"  - Neutral: {100 - pos_pct - neg_pct:.1f}% ({neutral:,})",
        f"",
        f"**Top Themes:**",
    ]
    
    for i, theme in enumerate(top_themes[:5], 1):
        summary_parts.append(f"  {i}. {theme}")
    
    summary_parts.append("")
    summary_parts.append("**Key Insights:**")
    
    if summaries.get("overall"):
        summary_parts.append(summaries["overall"][:300])  # First 300 chars
    
    return "\n".join(summary_parts)

