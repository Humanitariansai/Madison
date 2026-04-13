"""
AI theme extraction with batch processing that maintains context across batches
"""
import json
import re
import logging
from typing import List, Dict
from collections import Counter
from src.ai import _get_openai_client, OPENAI_API_KEY, logger

def extract_weighted_keyphrases_batched(
    texts: List[str], 
    top_k: int = 20,
    batch_size: int = 50,
    overlap_size: int = 10
) -> List[Dict]:
    """
    Extract themes from large datasets using batched processing with context preservation.
    
    Strategy: Two-pass approach
    1. First pass: Extract themes from each batch independently
    2. Second pass: Aggregate themes and refine with global context
    
    Args:
        texts: List of all text strings
        top_k: Number of final themes to return
        batch_size: Number of texts per batch
        overlap_size: Number of texts to overlap between batches (for context)
    
    Returns:
        List of dicts with "keyphrase" and "weight" keys
    """
    if not OPENAI_API_KEY:
        logger.warning("❌ OpenAI API key not configured")
        raise ValueError("OpenAI API key not configured")
    
    if not texts:
        return []
    
    logger.info(f"🤖 [AI-BATCHED] Processing {len(texts)} texts in batches (batch_size={batch_size}, overlap={overlap_size})")
    
    try:
        client = _get_openai_client()
        
        # ===== PASS 1: Extract themes from each batch =====
        logger.info("📊 [AI-BATCHED] Pass 1: Extracting themes from batches...")
        all_batch_themes = []
        
        # Create batches with overlap
        batches = []
        for i in range(0, len(texts), batch_size - overlap_size):
            batch = texts[i:i+batch_size]
            if batch:
                batches.append((i // (batch_size - overlap_size) + 1, batch))
        
        logger.info(f"📦 [AI-BATCHED] Created {len(batches)} batches")
        
        # Process each batch
        for batch_num, batch in batches:
            logger.info(f"🔄 [AI-BATCHED] Processing batch {batch_num}/{len(batches)} ({len(batch)} texts)")
            
            try:
                themes = _extract_themes_from_batch(client, batch, top_k=top_k * 2)  # Get more themes per batch
                all_batch_themes.extend(themes)
                logger.info(f"✅ [AI-BATCHED] Batch {batch_num}: Extracted {len(themes)} themes")
            except Exception as e:
                logger.warning(f"⚠️ [AI-BATCHED] Batch {batch_num} failed: {e}, continuing...")
                continue
        
        if not all_batch_themes:
            logger.warning("⚠️ [AI-BATCHED] No themes extracted from batches")
            return []
        
        # ===== AGGREGATION: Combine themes from all batches =====
        logger.info("🔗 [AI-BATCHED] Aggregating themes from all batches...")
        aggregated_themes = _aggregate_themes(all_batch_themes)
        
        logger.info(f"📊 [AI-BATCHED] Aggregated {len(aggregated_themes)} unique themes from {len(all_batch_themes)} batch themes")
        
        # ===== PASS 2: Refine themes with global context =====
        logger.info("🎯 [AI-BATCHED] Pass 2: Refining themes with global context...")
        
        # Sample texts from different parts of the dataset for context
        sample_indices = [
            0,  # Beginning
            len(texts) // 4,  # 25%
            len(texts) // 2,  # 50%
            3 * len(texts) // 4,  # 75%
            len(texts) - 1  # End
        ]
        context_texts = [texts[i] for i in sample_indices if i < len(texts)]
        
        # Add some random samples
        import random
        random_samples = random.sample(texts, min(20, len(texts)))
        context_texts.extend(random_samples[:20])
        
        # Refine themes using aggregated themes as context
        refined_themes = _refine_themes_with_context(
            client,
            context_texts,
            aggregated_themes[:top_k * 2],  # Top themes from aggregation
            top_k=top_k
        )
        
        logger.info(f"✅ [AI-BATCHED] Final: {len(refined_themes)} refined themes")
        return refined_themes[:top_k]
        
    except Exception as e:
        logger.error(f"❌ [AI-BATCHED] Error in batched extraction: {e}")
        raise


def _extract_themes_from_batch(client, batch: List[str], top_k: int = 20) -> List[Dict]:
    """Extract themes from a single batch"""
    combined_text = "\n".join([f"- {text}" for text in batch])
    
    prompt = f"""Analyze the following customer feedback and extract the top {top_k} most important themes/keyphrases.

Feedback:
{combined_text}

Return a JSON array of objects, each with "keyphrase" (the theme/phrase) and "weight" (importance score 0-1).
Example format:
[
  {{"keyphrase": "app crashes", "weight": 0.95}},
  {{"keyphrase": "slow loading", "weight": 0.87}},
  ...
]

Return ONLY valid JSON, no other text."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a data analyst extracting key themes from customer feedback. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
    except TypeError:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a data analyst extracting key themes from customer feedback. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
    
    content = response.choices[0].message.content.strip()
    
    # Parse JSON
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            themes = data.get("themes", data.get("keyphrases", data.get("results", [])))
        else:
            themes = data
        
        if not isinstance(themes, list):
            themes = []
        
        result = []
        for item in themes:
            if isinstance(item, dict):
                keyphrase = item.get("keyphrase", item.get("phrase", item.get("theme", "")))
                weight = float(item.get("weight", item.get("score", 0.5)))
                if keyphrase:
                    result.append({
                        "keyphrase": str(keyphrase).strip(),
                        "weight": max(0.0, min(1.0, weight))
                    })
        
        result.sort(key=lambda x: x["weight"], reverse=True)
        return result
        
    except json.JSONDecodeError:
        # Try markdown extraction
        json_match = re.search(r'```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            themes = data if isinstance(data, list) else data.get("themes", [])
            result = []
            for item in themes:
                if isinstance(item, dict):
                    keyphrase = item.get("keyphrase", "")
                    weight = float(item.get("weight", 0.5))
                    if keyphrase:
                        result.append({"keyphrase": str(keyphrase).strip(), "weight": max(0.0, min(1.0, weight))})
            result.sort(key=lambda x: x["weight"], reverse=True)
            return result
    
    return []


def _aggregate_themes(batch_themes: List[Dict]) -> List[Dict]:
    """
    Aggregate themes from multiple batches.
    Combines similar themes and weights them by frequency and average weight.
    """
    # Group similar themes
    theme_groups = {}
    
    for theme in batch_themes:
        keyphrase = theme["keyphrase"].lower().strip()
        weight = theme["weight"]
        
        # Find similar existing theme (simple matching - can be improved with embeddings)
        matched = False
        for existing_key in theme_groups:
            # Check if themes are similar (same words or one contains the other)
            existing_words = set(existing_key.split())
            current_words = set(keyphrase.split())
            
            # If significant overlap, merge
            if len(existing_words & current_words) >= min(len(existing_words), len(current_words)) * 0.6:
                theme_groups[existing_key].append(weight)
                matched = True
                break
        
        if not matched:
            theme_groups[keyphrase] = [weight]
    
    # Aggregate: calculate average weight and frequency
    aggregated = []
    for keyphrase, weights in theme_groups.items():
        avg_weight = sum(weights) / len(weights)
        frequency = len(weights)
        
        # Combined score: average weight * frequency factor
        # More frequent themes get higher score
        frequency_factor = min(1.0, frequency / 5.0)  # Cap at 5 occurrences
        combined_weight = avg_weight * (0.7 + 0.3 * frequency_factor)
        
        aggregated.append({
            "keyphrase": keyphrase,
            "weight": combined_weight,
            "frequency": frequency
        })
    
    # Sort by combined weight
    aggregated.sort(key=lambda x: x["weight"], reverse=True)
    return aggregated


def _refine_themes_with_context(
    client,
    context_texts: List[str],
    candidate_themes: List[Dict],
    top_k: int = 20
) -> List[Dict]:
    """
    Refine themes using global context.
    Takes candidate themes from batches and refines them with sample texts from entire dataset.
    """
    # Prepare context
    context_text = "\n".join([f"- {text}" for text in context_texts[:30]])  # Limit context
    
    # Prepare candidate themes list
    themes_list = "\n".join([
        f"- {theme['keyphrase']} (weight: {theme['weight']:.2f})"
        for theme in candidate_themes[:30]
    ])
    
    prompt = f"""You have analyzed customer feedback in batches and identified these candidate themes:

Candidate Themes:
{themes_list}

Now, analyze this sample of feedback from the ENTIRE dataset to refine and validate these themes:

Sample Feedback:
{context_text}

Tasks:
1. Validate which themes are truly important across the entire dataset
2. Merge similar themes that might have been phrased differently
3. Adjust weights based on global importance
4. Identify any missing important themes

Return a JSON array with the top {top_k} most important themes, each with "keyphrase" and "weight" (0-1).
Focus on themes that appear consistently across the dataset.

Return ONLY valid JSON, no other text."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a data analyst refining themes from customer feedback analysis. Always return valid JSON."},
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
                {"role": "system", "content": "You are a data analyst refining themes from customer feedback analysis. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
    
    content = response.choices[0].message.content.strip()
    
    # Parse JSON
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            themes = data.get("themes", data.get("keyphrases", data.get("results", [])))
        else:
            themes = data
        
        if not isinstance(themes, list):
            themes = []
        
        result = []
        for item in themes:
            if isinstance(item, dict):
                keyphrase = item.get("keyphrase", item.get("phrase", item.get("theme", "")))
                weight = float(item.get("weight", item.get("score", 0.5)))
                if keyphrase:
                    result.append({
                        "keyphrase": str(keyphrase).strip(),
                        "weight": max(0.0, min(1.0, weight))
                    })
        
        result.sort(key=lambda x: x["weight"], reverse=True)
        return result[:top_k]
        
    except json.JSONDecodeError:
        # Fallback: return candidate themes
        logger.warning("⚠️ [AI-BATCHED] Failed to parse refinement response, using aggregated themes")
        return candidate_themes[:top_k]
    
    return candidate_themes[:top_k]

