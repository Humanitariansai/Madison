import pandas as pd
import numpy as np
import re
import json
import math
import matplotlib.pyplot as plt
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# ===== GOOGLE COLAB PATHS - MUSICAL INSTRUMENTS =====
IN_CSV = "/content/musical_processed.csv"
OUT_CSV = "/content/musical_processed_week2.csv"
OUT_THEMES_JSON = "/content/musical_themes_summary.json"
TEXT_COL = "reviewtext"

print("="*60)
print("WEEK 2: MUSICAL INSTRUMENTS - IMPROVED THEME ANALYSIS")
print("="*60)

# Load processed data
print("\nLoading processed data...")
df = pd.read_csv(IN_CSV, low_memory=False)
print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

# Validate text column
if TEXT_COL not in df.columns:
    candidates = [c for c in df.columns if c.lower() in 
                  {"reviewtext", "comment", "feedback", "review", "text", "summary"}]
    TEXT_COL = candidates[0] if candidates else None

if TEXT_COL is None:
    raise ValueError("No text column found. Cannot proceed with theme analysis.")

print(f"Using text column: '{TEXT_COL}'")
texts = df[TEXT_COL].fillna("").astype(str).tolist()

# IMPROVED THEME CLUSTERING WITH MEANINGFUL KEYWORDS
print("\nExtracting keywords using TF-IDF with K-Means...")

# Stop words to remove (common meaningless words)
custom_stop_words = [
    'the', 'and', 'for', 'with', 'this', 'that', 'are', 'was', 'were', 'been',
    'have', 'has', 'had', 'but', 'not', 'you', 'your', 'from', 'they', 'can',
    'will', 'just', 'than', 'when', 'where', 'who', 'what', 'which', 'these',
    'those', 'some', 'all', 'would', 'there', 'their', 'about', 'into', 'through',
    'more', 'very', 'also', 'only', 'other', 'any', 'one', 'two', 'much', 'many',
    'most', 'such', 'out', 'well', 'like', 'really', 'little', 'get', 'got', 'use',
    'used', 'using'
]

# Create TF-IDF vectorizer with proper settings
vectorizer = TfidfVectorizer(
    max_features=1000,  # Top 1000 keywords
    stop_words=custom_stop_words,
    max_df=0.8,  # Ignore words in >80% of docs (too common)
    min_df=5,    # Must appear in at least 5 docs
    ngram_range=(1, 2),  # Single words and 2-word phrases
    token_pattern=r'\b[a-z]{3,}\b'  # Only words with 3+ letters
)

# Convert texts to TF-IDF matrix
print("Creating TF-IDF matrix...")
tfidf_matrix = vectorizer.fit_transform(texts)
feature_names = vectorizer.get_feature_names_out()

print(f"TF-IDF matrix shape: {tfidf_matrix.shape}")
print(f"Vocabulary size: {len(feature_names)}")

# Apply K-Means clustering on TF-IDF vectors
print("Performing K-Means clustering (k=6)...")
n_clusters = 6
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, max_iter=300)
df["theme_cluster"] = kmeans.fit_predict(tfidf_matrix)

# Get top keywords for each cluster
print("\nExtracting top keywords for each cluster...")
cluster_centers = kmeans.cluster_centers_
top_terms_per_cluster = []

for i in range(n_clusters):
    # Get indices of top features for this cluster
    center = cluster_centers[i]
    top_indices = center.argsort()[-15:][::-1]  # Top 15 keywords
    top_keywords = [feature_names[idx] for idx in top_indices]
    top_terms_per_cluster.append(top_keywords)

# Display theme clusters with meaningful names
print("\n" + "="*60)
print("DISCOVERED THEMES (with meaningful keywords):")
print("="*60)

theme_names = {
    0: "Product Quality & Performance",
    1: "Sound Quality & Audio",
    2: "Value & Price",
    3: "Durability & Issues",
    4: "Guitar-Specific Features",
    5: "Professional & Brand Focus"
}

for i, keywords in enumerate(top_terms_per_cluster):
    # Intelligently name the cluster based on keywords
    cluster_size = (df["theme_cluster"] == i).sum()
    print(f"\nCluster {i} ({cluster_size} reviews, {cluster_size/len(df)*100:.1f}%):")
    print(f"  Keywords: {', '.join(keywords[:10])}")

# Manual theme interpretation based on keywords
def interpret_themes(top_terms):
    """Intelligently categorize themes based on keywords"""
    interpretations = {}
    
    for i, keywords in enumerate(top_terms):
        keywords_str = ' '.join(keywords).lower()
        
        # Identify theme based on keyword patterns
        if any(word in keywords_str for word in ['cable', 'string', 'pick', 'case', 'stand', 'strap']):
            theme_type = "Accessories & Parts"
        elif any(word in keywords_str for word in ['sound', 'tone', 'audio', 'quality', 'clear', 'recording']):
            theme_type = "Sound Quality"
        elif any(word in keywords_str for word in ['price', 'money', 'worth', 'cheap', 'expensive', 'value']):
            theme_type = "Value & Pricing"
        elif any(word in keywords_str for word in ['broke', 'broken', 'failed', 'stopped', 'issue', 'problem']):
            theme_type = "Durability Issues"
        elif any(word in keywords_str for word in ['guitar', 'fret', 'neck', 'strings', 'tuning']):
            theme_type = "Guitar Features"
        elif any(word in keywords_str for word in ['professional', 'studio', 'fender', 'yamaha', 'brand']):
            theme_type = "Professional/Brand"
        else:
            theme_type = "General Satisfaction"
        
        interpretations[i] = theme_type
    
    return interpretations

theme_types = interpret_themes(top_terms_per_cluster)

print("\n" + "="*60)
print("THEME INTERPRETATIONS:")
print("="*60)
for i, theme_type in theme_types.items():
    cluster_size = (df["theme_cluster"] == i).sum()
    print(f"Cluster {i}: {theme_type} ({cluster_size} reviews)")

# Trend analysis over time
print("\nAnalyzing sentiment trends over time...")
date_col = None
for c in ["reviewtime", "unixreviewtime"]:
    if c in df.columns:
        date_col = c
        break

if date_col == "unixreviewtime":
    ts = pd.to_datetime(df["unixreviewtime"], unit="s", errors="coerce", utc=True)
elif date_col == "reviewtime":
    ts = pd.to_datetime(df["reviewtime"], errors="coerce", utc=True)
else:
    base = pd.Timestamp("2024-01-01", tz="UTC")
    ts = pd.to_datetime([base + pd.Timedelta(days=int(i / 25)) for i in range(len(df))], utc=True)
    print("Note: Using synthetic timeline")

df["_date"] = ts.dt.date

# Create trend data
trend = (df.groupby("_date")["sentiment"]
         .value_counts()
         .unstack(fill_value=0)
         .reset_index()
         .sort_values("_date"))

print(f"Trend data: {len(trend)} date points")

# Save artifacts
print("\nSaving artifacts...")
df.to_csv(OUT_CSV, index=False)
print(f"  Saved: {OUT_CSV}")

# Save themes with better structure
themes_output = {
    "dataset": "Musical Instruments Reviews",
    "text_column": TEXT_COL,
    "clustering_method": "TF-IDF + K-Means",
    "n_clusters": n_clusters,
    "clusters": {}
}

for i in range(n_clusters):
    themes_output["clusters"][f"cluster_{i}"] = {
        "keywords": top_terms_per_cluster[i][:12],
        "theme_type": theme_types.get(i, "General"),
        "size": int((df["theme_cluster"] == i).sum()),
        "percentage": float((df["theme_cluster"] == i).sum() / len(df) * 100)
    }

with open(OUT_THEMES_JSON, "w") as f:
    json.dump(themes_output, f, indent=2)
print(f"  Saved: {OUT_THEMES_JSON}")

# Visualizations
print("\nGenerating visualizations...")

# 1) Sentiment Distribution
plt.figure(figsize=(8, 5))
sentiment_counts = df["sentiment"].value_counts()
colors_sent = {'positive': '#66bb6a', 'neutral': '#ffa726', 'negative': '#d32f2f'}
bar_colors = [colors_sent.get(s, '#999') for s in sentiment_counts.index]
sentiment_counts.plot(kind="bar", color=bar_colors)
plt.title("Musical Instruments - Sentiment Distribution", fontsize=14, fontweight='bold')
plt.xlabel("Sentiment", fontsize=12)
plt.ylabel("Count", fontsize=12)
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig("/content/musical_sentiment_w2.png", dpi=150, bbox_inches='tight')
plt.show()
print("  Chart 1: Sentiment distribution saved")

# 2) Theme Cluster Distribution with labels
plt.figure(figsize=(12, 6))
cluster_counts = df["theme_cluster"].value_counts().sort_index()
colors_theme = plt.cm.Set3(range(n_clusters))

bars = plt.bar(range(n_clusters), cluster_counts.values, color=colors_theme)

# Add labels with theme names
labels = [f"C{i}: {theme_types.get(i, 'General')[:20]}" for i in range(n_clusters)]
plt.xticks(range(n_clusters), labels, rotation=45, ha='right')

plt.title("Musical Instruments - Theme Distribution", fontsize=14, fontweight='bold')
plt.xlabel("Theme Cluster", fontsize=12)
plt.ylabel("Count", fontsize=12)

# Add value labels on bars
for i, bar in enumerate(bars):
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'{int(height)}\n({height/len(df)*100:.1f}%)',
             ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig("/content/musical_theme_clusters.png", dpi=150, bbox_inches='tight')
plt.show()
print("  Chart 2: Theme clusters saved")

# 3) Sentiment Trend Over Time
if "negative" in trend.columns and len(trend) > 1:
    plt.figure(figsize=(12, 6))
    
    if "positive" in trend.columns:
        plt.plot(trend["_date"], trend["positive"], label="Positive", 
                color='#66bb6a', linewidth=2, marker='o', markersize=3)
    if "neutral" in trend.columns:
        plt.plot(trend["_date"], trend["neutral"], label="Neutral", 
                color='#ffa726', linewidth=2, marker='o', markersize=3)
    if "negative" in trend.columns:
        plt.plot(trend["_date"], trend["negative"], label="Negative", 
                color='#d32f2f', linewidth=2, marker='o', markersize=3)
    
    plt.title("Musical Instruments - Sentiment Trends Over Time", fontsize=14, fontweight='bold')
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Review Count", fontsize=12)
    plt.legend(loc='best')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("/content/musical_sentiment_trend.png", dpi=150, bbox_inches='tight')
    plt.show()
    print("  Chart 3: Sentiment trend saved")

# Final summary
summary = {
    "dataset": "Musical Instruments Reviews",
    "method": "TF-IDF + K-Means Clustering",
    "used_text_column": TEXT_COL,
    "themes_json": OUT_THEMES_JSON,
    "updated_csv": OUT_CSV,
    "trend_rows": len(trend),
    "total_reviews": len(df),
    "theme_clusters": n_clusters,
    "themes": {i: theme_types.get(i, "General") for i in range(n_clusters)}
}

print("\n" + "="*60)
print("WEEK 2: MUSICAL INSTRUMENTS ANALYSIS COMPLETE")
print("="*60)
print(json.dumps(summary, indent=2))
print("\nMeaningful themes discovered:")
for i, theme in theme_types.items():
    print(f"  - Cluster {i}: {theme}")
