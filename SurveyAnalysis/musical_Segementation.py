import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

# ===== GOOGLE COLAB PATHS - MUSICAL INSTRUMENTS =====
IN_CSV = "/content/musical_processed_week2.csv"
OUT_REPORT = "/content/musical_week3_report.json"
OUT_FINAL_CSV = "/content/musical_processed_final.csv"

print("="*60)
print("WEEK 3: MUSICAL INSTRUMENTS - SEGMENTATION & PCA")
print("="*60)

# Load data
print("\nLoading Week 2 processed data...")
df = pd.read_csv(IN_CSV, low_memory=False)
print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

# Feature Engineering
print("\n1. Feature Engineering...")

numeric_features = []
feature_names = []

if "overall" in df.columns:
    numeric_features.append(df["overall"].fillna(df["overall"].median()))
    feature_names.append("overall_rating")

if "reviewtext" in df.columns:
    df["review_length"] = df["reviewtext"].fillna("").astype(str).str.len()
    df["word_count"] = df["reviewtext"].fillna("").astype(str).str.split().str.len()
    numeric_features.extend([df["review_length"], df["word_count"]])
    feature_names.extend(["review_length", "word_count"])

# Sentiment encoding
if "sentiment" in df.columns:
    sentiment_dummies = pd.get_dummies(df["sentiment"], prefix="sentiment")
    for col in sentiment_dummies.columns:
        numeric_features.append(sentiment_dummies[col])
        feature_names.append(col)

# Theme cluster encoding
if "theme_cluster" in df.columns:
    theme_dummies = pd.get_dummies(df["theme_cluster"], prefix="theme")
    for col in theme_dummies.columns:
        numeric_features.append(theme_dummies[col])
        feature_names.append(col)

X = np.column_stack(numeric_features)
print(f"Feature matrix shape: {X.shape}")

# PCA
print("\n2. Applying PCA...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

n_components = min(5, X.shape[1])
pca = PCA(n_components=n_components)
X_pca = pca.fit_transform(X_scaled)

df["pca_1"] = X_pca[:, 0]
df["pca_2"] = X_pca[:, 1]

explained_var = pca.explained_variance_ratio_
print(f"Explained variance: {explained_var}")

# Viz 1: PCA Variance
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.bar(range(1, n_components + 1), explained_var, color='#3f51b5')
plt.xlabel("Principal Component")
plt.ylabel("Explained Variance Ratio")
plt.title("Musical Instruments - PCA Variance")
plt.xticks(range(1, n_components + 1))

plt.subplot(1, 2, 2)
plt.plot(range(1, n_components + 1), explained_var.cumsum(), 
         marker='o', color='#f44336', linewidth=2)
plt.xlabel("Number of Components")
plt.ylabel("Cumulative Variance")
plt.title("Cumulative Variance Explained")
plt.xticks(range(1, n_components + 1))
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("/content/musical_pca_variance.png", dpi=150)
plt.show()
print("  Saved: pca_variance.png")

# Viz 2: PCA Scatter
plt.figure(figsize=(10, 8))
scatter = plt.scatter(df["pca_1"], df["pca_2"], 
                     c=df["overall"].fillna(3), 
                     cmap='RdYlGn', alpha=0.6, s=30)
plt.colorbar(scatter, label="Overall Rating")
plt.xlabel(f"PC1 ({explained_var[0]:.1%} variance)")
plt.ylabel(f"PC2 ({explained_var[1]:.1%} variance)")
plt.title("Musical Instruments - PCA Projection")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("/content/musical_pca_scatter.png", dpi=150)
plt.show()
print("  Saved: pca_scatter.png")

# K-Means Segmentation
print("\n3. Customer Segmentation...")

inertias = []
K_range = range(2, 9)
for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    inertias.append(kmeans.inertia_)

# Elbow Plot
plt.figure(figsize=(8, 5))
plt.plot(K_range, inertias, marker='o', linewidth=2, markersize=8, color='#9c27b0')
plt.xlabel("Number of Clusters (k)")
plt.ylabel("Inertia")
plt.title("Musical Instruments - Elbow Method")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("/content/musical_elbow_plot.png", dpi=150)
plt.show()
print("  Saved: elbow_plot.png")

# Apply K-Means with k=4
optimal_k = 4
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
df["customer_segment"] = kmeans.fit_predict(X_scaled)

print(f"Segmentation complete with k={optimal_k}")
print(f"Segment distribution:\n{df['customer_segment'].value_counts().sort_index()}")

# Viz 4: Segments in PCA Space
plt.figure(figsize=(10, 8))
colors = ['#e91e63', '#2196f3', '#4caf50', '#ff9800']
for seg in range(optimal_k):
    mask = df["customer_segment"] == seg
    plt.scatter(df.loc[mask, "pca_1"], df.loc[mask, "pca_2"], 
               label=f"Segment {seg}", alpha=0.6, s=40, color=colors[seg])
plt.xlabel(f"PC1 ({explained_var[0]:.1%} variance)")
plt.ylabel(f"PC2 ({explained_var[1]:.1%} variance)")
plt.title("Musical Instruments - Customer Segments")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("/content/musical_customer_segments.png", dpi=150)
plt.show()
print("  Saved: customer_segments.png")

# Segment Profiling
print("\n4. Segment Profiling...")
segment_profiles = {}
for seg in range(optimal_k):
    seg_data = df[df["customer_segment"] == seg]
    profile = {
        "count": len(seg_data),
        "avg_rating": float(seg_data["overall"].mean()) if "overall" in seg_data.columns else None,
        "avg_review_length": float(seg_data["review_length"].mean()) if "review_length" in seg_data.columns else None,
        "sentiment_distribution": seg_data["sentiment"].value_counts().to_dict() if "sentiment" in seg_data.columns else {}
    }
    segment_profiles[f"segment_{seg}"] = profile
    print(f"\n  Segment {seg}:")
    print(f"    Size: {profile['count']} ({profile['count']/len(df)*100:.1f}%)")
    if profile['avg_rating']:
        print(f"    Avg Rating: {profile['avg_rating']:.2f}")

# Viz 5: Segment Comparison
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Segment sizes
ax1 = axes[0, 0]
seg_counts = df["customer_segment"].value_counts().sort_index()
ax1.bar(range(optimal_k), seg_counts.values, color=colors)
ax1.set_xlabel("Segment")
ax1.set_ylabel("Count")
ax1.set_title("Segment Sizes")
ax1.set_xticks(range(optimal_k))

# Average rating
ax2 = axes[0, 1]
if "overall" in df.columns:
    avg_ratings = df.groupby("customer_segment")["overall"].mean()
    ax2.bar(range(optimal_k), avg_ratings.values, color=colors)
    ax2.set_xlabel("Segment")
    ax2.set_ylabel("Average Rating")
    ax2.set_title("Average Rating by Segment")
    ax2.set_xticks(range(optimal_k))
    ax2.set_ylim([0, 5])

# Sentiment distribution
ax3 = axes[1, 0]
sentiment_by_seg = pd.crosstab(df["customer_segment"], df["sentiment"], normalize='index') * 100
sentiment_by_seg.plot(kind='bar', stacked=True, ax=ax3, 
                     color=['#d32f2f', '#ffa726', '#66bb6a'])
ax3.set_xlabel("Segment")
ax3.set_ylabel("Percentage")
ax3.set_title("Sentiment Distribution by Segment")
ax3.legend(title="Sentiment")
ax3.set_xticklabels(range(optimal_k), rotation=0)

# Review length
ax4 = axes[1, 1]
if "review_length" in df.columns:
    df.boxplot(column="review_length", by="customer_segment", ax=ax4)
    ax4.set_xlabel("Segment")
    ax4.set_ylabel("Review Length (characters)")
    ax4.set_title("Review Length by Segment")
    plt.sca(ax4)
    plt.xticks(range(1, optimal_k + 1), range(optimal_k))

plt.suptitle("")
plt.tight_layout()
plt.savefig("/content/musical_segment_analysis.png", dpi=150)
plt.show()
print("  Saved: segment_analysis.png")

# Save results
print("\n5. Saving final outputs...")
df.to_csv(OUT_FINAL_CSV, index=False)
print(f"  Saved: {OUT_FINAL_CSV}")

report = {
    "dataset": "Musical Instruments Reviews",
    "total_reviews": len(df),
    "pca": {
        "n_components": n_components,
        "explained_variance_ratio": explained_var.tolist(),
        "cumulative_variance": explained_var.cumsum().tolist()
    },
    "segmentation": {
        "method": "K-Means",
        "n_clusters": optimal_k,
        "segment_profiles": segment_profiles
    },
    "features_used": feature_names
}

with open(OUT_REPORT, "w") as f:
    json.dump(report, f, indent=2)
print(f"  Saved: {OUT_REPORT}")

print("\n" + "="*60)
print("WEEK 3: MUSICAL INSTRUMENTS ANALYSIS COMPLETE")
print("="*60)
print(f"\nKey Findings:")
print(f"  - {n_components} components explain {explained_var.sum():.1%} of variance")
print(f"  - Identified {optimal_k} customer segments")
