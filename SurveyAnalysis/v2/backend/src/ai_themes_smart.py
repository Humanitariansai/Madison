"""
Smart AI Theme Extraction with Context Preservation
Follows the correct approach: Extract → Embed → Cluster → Merge → Count
"""
import json
import re
import logging
import numpy as np
from typing import List, Dict, Tuple
from collections import Counter
from sklearn.cluster import DBSCAN
from src.ai import _get_openai_client, OPENAI_API_KEY, logger

try:
    from src.embeddings import generate_embeddings
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("⚠️ sentence-transformers not available, will use TF-IDF fallback")


def extract_themes_smart(
    texts: List[str],
    top_k: int = 20,
    batch_size: int = 50,
    similarity_threshold: float = 0.75
) -> List[Dict]:
    """
    Smart theme extraction that preserves context across batches.
    
    Strategy:
    1. Extract raw themes from batches (don't worry about duplicates)
    2. Embed themes into vectors
    3. Group similar themes using cosine similarity
    4. Merge each cluster with GPT
    5. Count frequency from original data
    
    Args:
        texts: All survey responses
        top_k: Number of final themes to return
        batch_size: Number of texts per batch
        similarity_threshold: Cosine similarity threshold for grouping (0-1)
    
    Returns:
        List of dicts with "keyphrase", "weight", "frequency", "examples"
    """
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    
    if not texts:
        return []
    
    logger.info(f"🧠 [SMART-THEMES] Processing {len(texts)} texts (batch_size={batch_size})")
    
    client = _get_openai_client()
    
    # ===== STEP 1: Extract raw themes from batches =====
    logger.info("📝 [SMART-THEMES] Step 1: Extracting raw themes from batches...")
    raw_themes = _extract_raw_themes_from_batches(client, texts, batch_size)
    
    if not raw_themes:
        logger.warning("⚠️ [SMART-THEMES] No themes extracted")
        return []
    
    logger.info(f"✅ [SMART-THEMES] Extracted {len(raw_themes)} raw themes from batches")
    
    # ===== STEP 2: Embed themes into vectors =====
    logger.info("🔢 [SMART-THEMES] Step 2: Converting themes to embeddings...")
    theme_texts = [theme["keyphrase"] for theme in raw_themes]
    
    if EMBEDDINGS_AVAILABLE:
        theme_embeddings = generate_embeddings(theme_texts, batch_size=32)
        logger.info(f"✅ [SMART-THEMES] Generated {len(theme_embeddings)} embeddings")
    else:
        # Fallback to TF-IDF
        from src.embeddings_fallback import generate_embeddings_tfidf
        theme_embeddings = generate_embeddings_tfidf(theme_texts)
        logger.info(f"✅ [SMART-THEMES] Generated {len(theme_embeddings)} TF-IDF embeddings (fallback)")
    
    # ===== STEP 3: Group similar themes using cosine similarity =====
    logger.info(f"🔗 [SMART-THEMES] Step 3: Grouping similar themes (threshold={similarity_threshold})...")
    theme_clusters = _cluster_similar_themes(theme_embeddings, raw_themes, similarity_threshold)
    
    logger.info(f"✅ [SMART-THEMES] Grouped into {len(theme_clusters)} clusters")
    
    # ===== STEP 4: Merge each cluster with GPT =====
    logger.info("🎯 [SMART-THEMES] Step 4: Merging clusters with GPT...")
    merged_themes = []
    
    for i, cluster in enumerate(theme_clusters):
        if len(cluster) == 0:
            continue
        
        logger.info(f"🔄 [SMART-THEMES] Merging cluster {i+1}/{len(theme_clusters)} ({len(cluster)} themes)")
        
        merged_theme = _merge_cluster_with_gpt(client, cluster, texts)
        if merged_theme:
            merged_themes.append(merged_theme)
    
    logger.info(f"✅ [SMART-THEMES] Merged into {len(merged_themes)} final themes")
    
    # ===== STEP 5: Count frequency from original data =====
    logger.info("📊 [SMART-THEMES] Step 5: Counting frequencies from original data...")
    final_themes = _count_theme_frequencies(merged_themes, texts, top_k)
    
    logger.info(f"✅ [SMART-THEMES] Final: {len(final_themes)} themes with frequencies")
    
    return final_themes


def _extract_raw_themes_from_batches(
    client,
    texts: List[str],
    batch_size: int = 50
) -> List[Dict]:
    """
    Step 1: Extract raw themes from each batch.
    Don't worry about duplicates or final naming - just collect themes.
    """
    all_raw_themes = []
    
    # Create batches
    num_batches = (len(texts) + batch_size - 1) // batch_size
    
    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(texts))
        batch = texts[start_idx:end_idx]
        
        if not batch:
            continue
        
        logger.info(f"📦 [SMART-THEMES] Processing batch {batch_num + 1}/{num_batches} ({len(batch)} texts)")
        
        try:
            themes = _extract_themes_from_batch(client, batch)
            all_raw_themes.extend(themes)
        except Exception as e:
            logger.warning(f"⚠️ [SMART-THEMES] Batch {batch_num + 1} failed: {e}")
            continue
    
    return all_raw_themes


def _extract_themes_from_batch(client, batch: List[str]) -> List[Dict]:
    """
    Extract themes from a single batch.
    GPT prompt: "List themes, don't worry about duplicates or final naming"
    """
    combined_text = "\n".join([f"- {text}" for text in batch])
    
    prompt = f"""Read these {len(batch)} survey answers and list the themes you notice.

Don't worry about:
- Duplicates (same theme might appear multiple times)
- Final naming (use whatever wording makes sense)
- Perfect formatting

Just list the main themes/keyphrases you see.

Survey Answers:
{combined_text}

Return a JSON array of objects, each with "keyphrase" (the theme) and "weight" (0-1, how important it seems).
Example:
[
  {{"keyphrase": "slow customer support", "weight": 0.8}},
  {{"keyphrase": "app crashes", "weight": 0.9}},
  {{"keyphrase": "hard to use UI", "weight": 0.7}}
]

Return ONLY valid JSON, no other text."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are extracting themes from survey responses. List all themes you notice, don't worry about duplicates. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
    except TypeError:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are extracting themes from survey responses. List all themes you notice, don't worry about duplicates. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
    
    content = response.choices[0].message.content.strip()
    
    # Parse JSON
    themes = []
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            themes_list = data.get("themes", data.get("keyphrases", data.get("results", [])))
        else:
            themes_list = data
        
        if not isinstance(themes_list, list):
            themes_list = []
        
        for item in themes_list:
            if isinstance(item, dict):
                keyphrase = item.get("keyphrase", item.get("phrase", item.get("theme", "")))
                weight = float(item.get("weight", item.get("score", 0.5)))
                if keyphrase:
                    themes.append({
                        "keyphrase": str(keyphrase).strip(),
                        "weight": max(0.0, min(1.0, weight))
                    })
    except json.JSONDecodeError:
        # Try markdown extraction
        json_match = re.search(r'```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                themes_list = data if isinstance(data, list) else data.get("themes", [])
                for item in themes_list:
                    if isinstance(item, dict):
                        keyphrase = item.get("keyphrase", "")
                        weight = float(item.get("weight", 0.5))
                        if keyphrase:
                            themes.append({
                                "keyphrase": str(keyphrase).strip(),
                                "weight": max(0.0, min(1.0, weight))
                            })
            except:
                pass
    
    return themes


def _cluster_similar_themes(
    embeddings: np.ndarray,
    raw_themes: List[Dict],
    similarity_threshold: float = 0.75
) -> List[List[Dict]]:
    """
    Step 3: Group similar themes using cosine similarity.
    Uses DBSCAN clustering with cosine distance.
    """
    if len(embeddings) == 0:
        return []
    
    # Convert similarity threshold to distance threshold
    # Cosine similarity 0.75 = cosine distance 0.25
    distance_threshold = 1.0 - similarity_threshold
    
    # Use DBSCAN for clustering (handles variable cluster sizes)
    # eps = distance threshold, min_samples = at least 2 themes per cluster
    clustering = DBSCAN(
        eps=distance_threshold,
        min_samples=1,  # Allow single-theme clusters
        metric='cosine'
    )
    
    clusters = clustering.fit_predict(embeddings)
    
    # Group themes by cluster
    theme_clusters = {}
    for idx, cluster_id in enumerate(clusters):
        if cluster_id not in theme_clusters:
            theme_clusters[cluster_id] = []
        theme_clusters[cluster_id].append(raw_themes[idx])
    
    # Convert to list (exclude noise points with cluster_id = -1)
    cluster_list = []
    for cluster_id, themes in theme_clusters.items():
        if cluster_id != -1:  # DBSCAN noise points
            cluster_list.append(themes)
        else:
            # Noise points become individual clusters
            for theme in themes:
                cluster_list.append([theme])
    
    return cluster_list


def _merge_cluster_with_gpt(
    client,
    cluster: List[Dict],
    all_texts: List[str]
) -> Dict:
    """
    Step 4: Merge a cluster of similar themes into one final theme.
    GPT prompt: "Here are similar themes, merge them into one clear theme"
    """
    if len(cluster) == 0:
        return None
    
    if len(cluster) == 1:
        # Single theme, just return it with some metadata
        theme = cluster[0]
        return {
            "keyphrase": theme["keyphrase"],
            "weight": theme["weight"],
            "cluster_size": 1,
            "description": "",
            "examples": []
        }
    
    # Prepare cluster themes list
    themes_list = "\n".join([
        f"- {theme['keyphrase']} (weight: {theme['weight']:.2f})"
        for theme in cluster
    ])
    
    # Find example texts that match these themes
    # Sample a few texts to help GPT understand context
    sample_texts = all_texts[:min(20, len(all_texts))]
    sample_context = "\n".join([f"- {text}" for text in sample_texts[:10]])
    
    prompt = f"""Here are {len(cluster)} similar themes extracted separately from survey responses:

Themes:
{themes_list}

Sample Survey Responses (for context):
{sample_context}

Task:
Merge these themes into ONE clear, well-named theme with:
1. A clean, concise name (2-5 words)
2. A short description (1-2 sentences explaining what this theme is about)
3. Why these themes are similar

Return JSON with:
{{
  "keyphrase": "clean theme name",
  "description": "short description",
  "reason": "why these themes are similar"
}}

Return ONLY valid JSON, no other text."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are merging similar themes into one clear theme. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
    except TypeError:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are merging similar themes into one clear theme. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
    
    content = response.choices[0].message.content.strip()
    
    try:
        data = json.loads(content)
        keyphrase = data.get("keyphrase", cluster[0]["keyphrase"])
        description = data.get("description", "")
        
        # Calculate average weight from cluster
        avg_weight = sum(theme["weight"] for theme in cluster) / len(cluster)
        
        return {
            "keyphrase": str(keyphrase).strip(),
            "weight": avg_weight,
            "description": str(description).strip(),
            "cluster_size": len(cluster),
            "original_themes": [theme["keyphrase"] for theme in cluster]
        }
    except json.JSONDecodeError:
        # Fallback: use first theme
        theme = cluster[0]
        return {
            "keyphrase": theme["keyphrase"],
            "weight": theme["weight"],
            "description": "",
            "cluster_size": len(cluster),
            "original_themes": [t["keyphrase"] for t in cluster]
        }


def _count_theme_frequencies(
    merged_themes: List[Dict],
    all_texts: List[str],
    top_k: int = 20
) -> List[Dict]:
    """
    Step 5: Count how many responses map to each theme.
    Uses simple text matching (can be improved with embeddings).
    """
    final_themes = []
    
    for theme in merged_themes:
        keyphrase = theme["keyphrase"].lower()
        keyphrase_words = set(keyphrase.split())
        
        # Count frequency: how many texts mention this theme
        matches = []
        for text in all_texts:
            text_lower = text.lower()
            text_words = set(text_lower.split())
            
            # Check if theme words appear in text
            # At least 50% of theme words must appear
            overlap = len(keyphrase_words & text_words)
            if overlap >= max(1, len(keyphrase_words) * 0.5):
                matches.append(text)
        
        frequency = len(matches)
        
        # Get example quotes
        examples = matches[:3] if matches else []
        
        final_themes.append({
            "keyphrase": theme["keyphrase"],
            "weight": theme["weight"],
            "frequency": frequency,
            "description": theme.get("description", ""),
            "examples": examples,
            "cluster_size": theme.get("cluster_size", 1)
        })
    
    # Sort by frequency (most common first), then by weight
    final_themes.sort(key=lambda x: (x["frequency"], x["weight"]), reverse=True)
    
    return final_themes[:top_k]

