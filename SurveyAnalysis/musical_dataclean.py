import pandas as pd
import numpy as np
import re
import sqlite3
import json
import matplotlib.pyplot as plt

# ===== GOOGLE COLAB PATHS - MUSICAL INSTRUMENTS =====
INPUT_CSV = "/content/Musical_instruments_reviews.csv"
PROCESSED_CSV = "/content/musical_processed.csv"
SQLITE_DB = "/content/musical_survey.sqlite"
SQL_TABLE = "musical_reviews"

# Column name constants
FORCE_TEXT_COL = "reviewtext"
ID_COLS_HINT = ["reviewerid", "asin", "unixreviewtime"]
PREFERRED_TIME_COL = "unixreviewtime"

print("="*60)
print("WEEK 1: MUSICAL INSTRUMENTS REVIEW ANALYSIS")
print("="*60)

# Load raw data
print("\nLoading raw data...")
df_raw = pd.read_csv(INPUT_CSV, low_memory=False)
print(f"Loaded {len(df_raw)} rows, {len(df_raw.columns)} columns")

def normalize_cols(cols):
    """Normalize column names to lowercase with underscores"""
    out = []
    for c in cols:
        c2 = re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_")
        out.append(c2 or "col")
    
    # Handle duplicates
    seen = {}
    final = []
    for c in out:
        if c not in seen:
            seen[c] = 1
            final.append(c)
        else:
            seen[c] += 1
            final.append(f"{c}_{seen[c]}")
    return final

# Normalize column names
df = df_raw.copy()
df.columns = normalize_cols(df.columns)
print(f"Normalized columns: {list(df.columns)}")

# Fast date coercion
def fast_date(series):
    """Try to convert series to datetime"""
    s = series.astype(str)
    sample = s[s.str.len() > 0].head(2000)
    m = pd.to_datetime(sample, errors="coerce", utc=True).notna().mean()
    if m >= 0.7:
        return pd.to_datetime(s, errors="coerce", utc=True), True
    return series, False

# Type inference and conversion
date_like = []
issues = []

for c in df.columns:
    if df[c].dtype == "object":
        # Try date conversion
        s, ok = fast_date(df[c])
        if ok:
            df[c] = s
            date_like.append(c)
            continue
        
        # Try numeric conversion
        num = pd.to_numeric(df[c], errors="coerce")
        if num.notna().mean() >= 0.7:
            xi = num.dropna()
            # Check if integer-like
            if len(xi) > 0 and (np.isclose(xi, xi.round())).mean() > 0.99:
                df[c] = num.round().astype("Int64")
            else:
                df[c] = num
            continue
        
        # Try boolean conversion
        t = df[c].astype(str).str.lower().str.strip()
        if t.isin({"true", "yes", "y", "1", "false", "no", "n", "0"}).mean() >= 0.8:
            df[c] = t.map(
                lambda x: True if x in {"true", "yes", "y", "1"} 
                else (False if x in {"false", "no", "n", "0"} else pd.NA)
            ).astype("boolean")

print(f"Date columns identified: {date_like}")

# Validation: drop sparse columns
na = df.isna().mean()
drop_cols = na[na > 0.9].index.tolist()
if drop_cols:
    df = df.drop(columns=drop_cols)
    issues.append(f"Dropped sparse columns (>90% missing): {drop_cols}")
    print(f"Dropped sparse columns: {drop_cols}")

# Check for duplicates
id_subset = [c for c in ID_COLS_HINT if c in df.columns]
if id_subset:
    dupe_ratio = df.duplicated(subset=id_subset).mean()
    if dupe_ratio > 0.05:
        issues.append(f"Duplicate ratio {dupe_ratio:.2%} on {id_subset}")
        print(f"Warning: {dupe_ratio:.2%} duplicates found")

# SENTIMENT ANALYSIS
print("\nGenerating sentiment labels...")

def from_rating(r):
    """Determine sentiment from rating (1-5 scale)"""
    try:
        r = float(r)
    except:
        return pd.NA
    if r >= 4:
        return "positive"
    if r <= 2:
        return "negative"
    return "neutral"

# Primary method: use rating column
if "overall" in df.columns:
    df["sentiment"] = df["overall"].map(from_rating)
    print("Sentiment derived from 'overall' rating column")
else:
    # Fallback: rule-based sentiment from text
    POS = {"good", "great", "love", "excellent", "amazing", "awesome", "best", 
           "nice", "fast", "smooth", "easy", "happy", "satisfied", "helpful", 
           "quick", "resolved", "improved", "friendly", "works", "recommend", 
           "perfect", "fantastic", "fine", "ok"}
    NEG = {"no", "not", "never", "bad", "terrible", "awful", "hate", "worst", 
           "poor", "slow", "crash", "bug", "issue", "late", "delay", "rude", 
           "unhelpful", "confusing", "broken", "return", "refund", "waste"}
    
    def rule_sentiment(t: str):
        if not isinstance(t, str) or not t.strip():
            return "neutral"
        s = t.lower()
        score = sum(w in s for w in POS) - sum(w in s for w in NEG)
        return "positive" if score > 0 else "negative" if score < 0 else "neutral"
    
    if FORCE_TEXT_COL in df.columns:
        df["sentiment"] = df[FORCE_TEXT_COL].astype(str).map(rule_sentiment)
        print(f"Sentiment derived from '{FORCE_TEXT_COL}' column using rules")
    else:
        df["sentiment"] = "neutral"
        issues.append("No rating or text column found; defaulting sentiment to 'neutral'")
        print("Warning: No suitable column for sentiment analysis")

# Create timestamp column
if PREFERRED_TIME_COL in df.columns:
    ts = pd.to_datetime(df[PREFERRED_TIME_COL], unit="s", errors="coerce", utc=True)
    df["_ts"] = ts
    print(f"Timestamp created from '{PREFERRED_TIME_COL}'")
elif "reviewtime" in df.columns:
    df["_ts"] = pd.to_datetime(df["reviewtime"], errors="coerce", utc=True)
    print("Timestamp created from 'reviewtime'")

# Sentiment distribution
sentiment_counts = df["sentiment"].value_counts()
print(f"\nSentiment Distribution:\n{sentiment_counts}")

# Save outputs
print("\nSaving processed data...")
df.to_csv(PROCESSED_CSV, index=False)
print(f"Saved CSV to: {PROCESSED_CSV}")

with sqlite3.connect(SQLITE_DB) as con:
    df.to_sql(SQL_TABLE, con, if_exists="replace", index=False)
print(f"Saved SQLite database to: {SQLITE_DB}")

# Visualization
plt.figure(figsize=(8, 5))
sentiment_counts.plot(kind="bar", color=['#d32f2f', '#ffa726', '#66bb6a'])
plt.title("Musical Instruments - Sentiment Distribution", fontsize=14, fontweight='bold')
plt.xlabel("Sentiment", fontsize=12)
plt.ylabel("Count", fontsize=12)
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("/content/musical_sentiment_distribution.png", dpi=150, bbox_inches='tight')
print("Saved sentiment chart")
plt.show()

# Summary report
summary = {
    "dataset": "Musical Instruments Reviews",
    "rows": len(df),
    "cols": len(df.columns),
    "text_column_used": FORCE_TEXT_COL if FORCE_TEXT_COL in df.columns else None,
    "sqlite_table": SQL_TABLE,
    "processed_csv": PROCESSED_CSV,
    "sqlite_db": SQLITE_DB,
    "sentiment_distribution": sentiment_counts.to_dict(),
    "issues": issues
}

print("\n" + "="*60)
print("WEEK 1: MUSICAL INSTRUMENTS PREPROCESSING COMPLETE")
print("="*60)
print(json.dumps(summary, indent=2))
