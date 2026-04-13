"""
Sentiment analysis using VADER
"""
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def analyze_sentiment(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    """
    Analyze sentiment using VADER
    
    Returns dataframe with sent_label and sent_compound columns
    """
    analyzer = SentimentIntensityAnalyzer()
    df_proc = df.copy()
    
    def get_sentiment(text):
        scores = analyzer.polarity_scores(str(text))
        compound = scores['compound']
        if compound >= 0.05:
            return 'positive'
        elif compound <= -0.05:
            return 'negative'
        else:
            return 'neutral'
    
    df_proc['sent_label'] = df_proc[text_col].apply(get_sentiment)
    df_proc['sent_compound'] = df_proc[text_col].apply(
        lambda x: analyzer.polarity_scores(str(x))['compound']
    )
    
    return df_proc

