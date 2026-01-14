"""
AI/LLM integration for analysis
"""
import os
import re
import json
import logging
import time
from typing import List, Dict, Optional
from collections import Counter
from src.config import load_env

env = load_env()
OPENAI_API_KEY = env.get("OPENAI_API_KEY", "")

logger = logging.getLogger(__name__)

def _retry_openai_call(call_func, max_retries=3, operation_name="OpenAI API call"):
    """
    Retry an OpenAI API call with exponential backoff for connection errors.
    
    Args:
        call_func: Function that makes the OpenAI API call (should return the response)
        max_retries: Maximum number of retry attempts
        operation_name: Name of the operation for logging
    
    Returns:
        The response from the API call
    
    Raises:
        The last exception if all retries fail
    """
    retry_delay = 1  # Start with 1 second
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return call_func()
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            # Check if it's a connection error that we should retry
            is_connection_error = any(keyword in error_str for keyword in [
                "connection", "timeout", "network", "unreachable", 
                "refused", "reset", "broken pipe"
            ])
            
            if is_connection_error and attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"⚠️ [AI] Connection error in {operation_name}, attempt {attempt + 1}/{max_retries}. Retrying in {wait_time}s... Error: {e}")
                time.sleep(wait_time)
            else:
                # Not a retryable error or out of retries
                raise
    
    # Should never reach here, but just in case
    if last_error:
        raise last_error
    raise Exception(f"Failed {operation_name} after {max_retries} attempts")

def _get_openai_client():
    """
    Create OpenAI client with proper error handling for proxy issues.
    Handles cases where environment variables or library versions cause issues.
    """
    try:
        from openai import OpenAI
        import os
        
        # Temporarily remove proxy env vars - OpenAI library tries to use them
        # but the client constructor doesn't accept proxies parameter
        proxy_vars = {}
        proxy_vars_to_remove = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                               'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
        for var in proxy_vars_to_remove:
            if var in os.environ:
                proxy_vars[var] = os.environ.pop(var)
        
        try:
            # Try standard initialization with api_key as keyword argument
            # OpenAI 1.3.5 requires api_key as keyword, not positional
            client = OpenAI(api_key=OPENAI_API_KEY)
            # Restore proxy vars
            os.environ.update(proxy_vars)
            return client
        except (TypeError, ValueError) as e:
            error_msg = str(e).lower()
            if "proxies" in error_msg or "unexpected keyword" in error_msg:
                logger.warning("⚠️ [AI] OpenAI client initialization issue with proxies, trying alternative method")
                # Try creating client without any extra params, let it read from env
                # But keep proxy vars removed
                try:
                    # Set API key in environment temporarily
                    old_key = os.environ.get("OPENAI_API_KEY")
                    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
                    
                    # Create client (should work now that proxy vars are removed)
                    client = OpenAI()  # Read from environment
                    
                    # Restore environment
                    if old_key is None:
                        os.environ.pop("OPENAI_API_KEY", None)
                    else:
                        os.environ["OPENAI_API_KEY"] = old_key
                    os.environ.update(proxy_vars)
                    return client
                except Exception as e2:
                    # Restore environment even on error
                    if old_key is None:
                        os.environ.pop("OPENAI_API_KEY", None)
                    else:
                        os.environ["OPENAI_API_KEY"] = old_key
                    os.environ.update(proxy_vars)
                    logger.error(f"❌ [AI] Failed to create OpenAI client even with fallback: {e2}")
                    raise
            else:
                # Restore proxy vars before re-raising
                os.environ.update(proxy_vars)
                # Different error, re-raise it
                raise
    except ImportError:
        logger.error("❌ [AI] OpenAI library not installed. Install with: pip install openai")
        raise ValueError("OpenAI library not installed. Install with: pip install openai")
    except Exception as e:
        logger.error(f"❌ [AI] Failed to create OpenAI client: {e}")
        raise

def classify_sentiments(texts: List[str], batch_size: int = 40) -> List[str]:
    """
    Classify sentiment using OpenAI GPT-3.5-turbo
    
    Args:
        texts: List of text strings to classify
        batch_size: Number of texts to process per API call
    
    Returns:
        List of sentiment labels: "positive", "negative", or "neutral"
    """
    if not OPENAI_API_KEY:
        logger.warning("❌ OpenAI API key not configured - cannot use AI sentiment classification")
        raise ValueError("OpenAI API key not configured")
    
    if not texts:
        logger.warning("⚠️ No texts provided for sentiment classification")
        return []
    
    logger.info(f"🤖 [AI] Starting OpenAI sentiment classification for {len(texts)} texts (batch_size={batch_size})")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ [AI] OpenAI client initialized successfully")
        
        labels = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"📤 [AI] Calling OpenAI API - Batch {batch_num}/{total_batches} ({len(batch)} texts)")
            
            # Create a numbered list for better parsing
            batch_text = "\n".join([f"{idx+1}. {text}" for idx, text in enumerate(batch)])
            
            try:
                # Use retry helper for connection errors
                def make_api_call():
                    logger.debug(f"🔍 [AI] Sending request to OpenAI GPT-3.5-turbo for sentiment classification")
                    return client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{
                            "role": "system",
                            "content": "You are a sentiment classifier. For each text, respond with ONLY one word: 'positive', 'negative', or 'neutral'. Return the labels in the same order, one per line, numbered 1, 2, 3, etc."
                        }, {
                            "role": "user",
                            "content": f"Classify the sentiment of these texts:\n{batch_text}\n\nRespond with one label per line, numbered 1, 2, 3, etc."
                        }],
                        temperature=0.3,
                        max_tokens=200,
                        timeout=30.0  # 30 second timeout
                    )
                
                response = _retry_openai_call(make_api_call, max_retries=3, operation_name=f"sentiment classification batch {batch_num}")
                
                logger.info(f"✅ [AI] OpenAI API response received for batch {batch_num}")
                logger.debug(f"📥 [AI] Response tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
                
                # Parse response
                content = response.choices[0].message.content.strip()
                batch_labels = []
                
                # Try to extract labels from numbered list or plain list
                lines = [l.strip() for l in content.split('\n') if l.strip()]
                
                for line in lines:
                    # Remove numbering (e.g., "1. positive" or "1) positive" -> "positive")
                    line = re.sub(r'^\d+[\.\)]\s*', '', line, flags=re.IGNORECASE)
                    line = line.lower().strip()
                    
                    # Normalize to our labels
                    if any(word in line for word in ['positive', 'pos', '+']):
                        batch_labels.append("positive")
                    elif any(word in line for word in ['negative', 'neg', '-']):
                        batch_labels.append("negative")
                    elif any(word in line for word in ['neutral', 'neu', '0']):
                        batch_labels.append("neutral")
                    # If we have enough labels, stop parsing
                    if len(batch_labels) >= len(batch):
                        break
                
                # Ensure we have the right number of labels
                while len(batch_labels) < len(batch):
                    batch_labels.append("neutral")
                
                labels.extend(batch_labels[:len(batch)])
                
                # Log sentiment distribution for this batch
                pos_count = batch_labels.count("positive")
                neg_count = batch_labels.count("negative")
                neu_count = batch_labels.count("neutral")
                logger.info(f"📊 [AI] Batch {batch_num} results: {pos_count} positive, {neg_count} negative, {neu_count} neutral")
                
            except Exception as e:
                error_str = str(e).lower()
                error_type = type(e).__name__
                
                # Log detailed error information
                if "connection" in error_str or "network" in error_str:
                    logger.error(f"❌ [AI] Connection error classifying batch {batch_num}: {error_type} - {e}")
                    logger.warning(f"⚠️ [AI] This may be due to network issues or OpenAI API being temporarily unavailable")
                elif "timeout" in error_str:
                    logger.error(f"❌ [AI] Timeout error classifying batch {batch_num}: {error_type} - {e}")
                elif "rate limit" in error_str or "429" in error_str:
                    logger.error(f"❌ [AI] Rate limit error classifying batch {batch_num}: {error_type} - {e}")
                    logger.warning(f"⚠️ [AI] OpenAI API rate limit reached. Consider reducing batch size or adding delays.")
                elif "authentication" in error_str or "401" in error_str or "403" in error_str:
                    logger.error(f"❌ [AI] Authentication error classifying batch {batch_num}: {error_type} - {e}")
                    logger.error(f"❌ [AI] Check that OPENAI_API_KEY is correctly configured in secrets")
                else:
                    logger.error(f"❌ [AI] Error classifying batch {batch_num}: {error_type} - {e}")
                
                logger.warning(f"⚠️ [AI] Falling back to neutral labels for batch {batch_num}")
                # Fallback: assign neutral to this batch
                labels.extend(["neutral"] * len(batch))
        
        # Log final distribution
        pos_total = labels.count("positive")
        neg_total = labels.count("negative")
        neu_total = labels.count("neutral")
        logger.info(f"✅ [AI] Sentiment classification complete: {pos_total} positive, {neg_total} negative, {neu_total} neutral (total: {len(labels)})")
        
        return labels
        
    except ImportError:
        logger.error("❌ [AI] OpenAI library not installed. Install with: pip install openai")
        raise ValueError("OpenAI library not installed. Install with: pip install openai")
    except Exception as e:
        logger.error(f"❌ [AI] Fatal error in classify_sentiments: {e}")
        raise

def extract_keyphrases(texts: List[str], top_k: int = 20) -> List[str]:
    """
    Extract keyphrases using AI
    
    Args:
        texts: List of text strings
        top_k: Number of keyphrases to return
    
    Returns:
        List of keyphrase strings
    """
    weighted = extract_weighted_keyphrases(texts, top_k)
    return [item["keyphrase"] for item in weighted]

def extract_weighted_keyphrases(texts: List[str], top_k: int = 20) -> List[Dict]:
    """
    Extract weighted keyphrases using OpenAI
    
    Args:
        texts: List of text strings
        top_k: Number of keyphrases to return
    
    Returns:
        List of dicts with "keyphrase" and "weight" keys
    """
    if not OPENAI_API_KEY:
        logger.warning("❌ OpenAI API key not configured - cannot use AI theme extraction")
        raise ValueError("OpenAI API key not configured")
    
    if not texts:
        logger.warning("⚠️ No texts provided for theme extraction")
        return []
    
    logger.info(f"🤖 [AI] Starting OpenAI theme extraction for {len(texts)} texts (top_k={top_k})")
    
    try:
        client = _get_openai_client()
        logger.info("✅ [AI] OpenAI client initialized successfully")
        
        # Combine texts (limit to avoid token limits)
        max_texts = 100
        sample_texts = texts[:max_texts] if len(texts) > max_texts else texts
        if len(texts) > max_texts:
            logger.info(f"📊 [AI] Sampling {max_texts} texts from {len(texts)} total (to avoid token limits)")
        combined_text = "\n".join([f"- {text}" for text in sample_texts[:50]])  # Limit to 50 for prompt
        logger.debug(f"📝 [AI] Using {len(sample_texts[:50])} texts in prompt")
        
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
            logger.info(f"📤 [AI] Calling OpenAI API for theme extraction (requesting {top_k} themes)")
            logger.debug(f"🔍 [AI] Sending request to OpenAI GPT-3.5-turbo for keyphrase extraction")
            # Use structured output if available, otherwise rely on prompt
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
                logger.debug("✅ [AI] Using JSON response format")
            except TypeError:
                # Fallback for older OpenAI versions that don't support response_format
                logger.warning("⚠️ [AI] response_format not supported, using standard format")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a data analyst extracting key themes from customer feedback. Always return valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
            
            logger.info("✅ [AI] OpenAI API response received for theme extraction")
            logger.debug(f"📥 [AI] Response tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                # Handle both {"themes": [...]} and [...] formats
                data = json.loads(content)
                if isinstance(data, dict):
                    # Look for common keys
                    themes = data.get("themes", data.get("keyphrases", data.get("results", [])))
                else:
                    themes = data
                
                if not isinstance(themes, list):
                    themes = []
                
                # Validate and normalize
                result = []
                for item in themes[:top_k]:
                    if isinstance(item, dict):
                        keyphrase = item.get("keyphrase", item.get("phrase", item.get("theme", "")))
                        weight = float(item.get("weight", item.get("score", 0.5)))
                    elif isinstance(item, str):
                        keyphrase = item
                        weight = 0.5
                    else:
                        continue
                    
                    if keyphrase:
                        result.append({
                            "keyphrase": str(keyphrase).strip(),
                            "weight": max(0.0, min(1.0, weight))  # Clamp to [0, 1]
                        })
                
                if result:
                    # Sort by weight descending
                    result.sort(key=lambda x: x["weight"], reverse=True)
                    logger.info(f"✅ [AI] Successfully extracted {len(result)} themes from OpenAI response")
                    logger.debug(f"📊 [AI] Top themes: {[r['keyphrase'] for r in result[:5]]}")
                    return result[:top_k]
                else:
                    logger.warning("⚠️ [AI] No themes extracted from JSON response")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ [AI] JSON parsing failed: {e}, attempting alternative parsing")
                # Try to extract JSON from markdown code blocks
                json_match = re.search(r'```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    logger.debug("🔍 [AI] Found JSON in markdown code block")
                    data = json.loads(json_match.group(1))
                    themes = data if isinstance(data, list) else data.get("themes", [])
                    result = []
                    for item in themes[:top_k]:
                        if isinstance(item, dict):
                            keyphrase = item.get("keyphrase", "")
                            weight = float(item.get("weight", 0.5))
                            if keyphrase:
                                result.append({"keyphrase": str(keyphrase).strip(), "weight": max(0.0, min(1.0, weight))})
                    if result:
                        result.sort(key=lambda x: x["weight"], reverse=True)
                        logger.info(f"✅ [AI] Extracted {len(result)} themes from markdown JSON")
                        return result[:top_k]
                
                # Fallback: try to extract phrases from text
                logger.warning("⚠️ [AI] Failed to parse JSON, attempting text extraction")
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                result = []
                for line in lines[:top_k]:
                    # Try to extract phrase and weight
                    match = re.match(r'["\']?([^"\']+)["\']?\s*[:=]\s*([\d.]+)', line)
                    if match:
                        keyphrase = match.group(1).strip()
                        weight = float(match.group(2))
                        result.append({"keyphrase": keyphrase, "weight": min(1.0, weight / 10.0)})
                    elif line:
                        result.append({"keyphrase": line.strip(), "weight": 0.5})
                
                if result:
                    return result[:top_k]
        
        except Exception as e:
            logger.error(f"❌ [AI] Error in OpenAI API call for theme extraction: {e}")
            raise
        
        logger.warning("⚠️ [AI] No themes extracted, returning empty list")
        return []
        
    except ImportError:
        logger.error("❌ [AI] OpenAI library not installed. Install with: pip install openai")
        raise ValueError("OpenAI library not installed. Install with: pip install openai")
    except Exception as e:
        logger.error(f"❌ [AI] Fatal error in extract_weighted_keyphrases: {e}")
        raise

def extract_impact_terms(texts: List[str], top_k: int = 50) -> List[Dict]:
    """
    Extract impact terms for word cloud using AI
    
    Args:
        texts: List of text strings
        top_k: Number of terms to return
    
    Returns:
        List of dicts with "term", "freq", and "sentiment" keys
        Format: [{"term": "mobile app crashes", "freq": 12, "sentiment": -0.85}, ...]
    """
    if not OPENAI_API_KEY:
        logger.warning("❌ OpenAI API key not configured - cannot use AI impact terms extraction")
        raise ValueError("OpenAI API key not configured")
    
    if not texts:
        logger.warning("⚠️ No texts provided for impact terms extraction")
        return []
    
    logger.info(f"🤖 [AI] Starting OpenAI impact terms extraction for {len(texts)} texts (top_k={top_k})")
    
    try:
        client = _get_openai_client()
        logger.info("✅ [AI] OpenAI client initialized successfully")
        
        # Sample texts to avoid token limits
        max_texts = 100
        sample_texts = texts[:max_texts] if len(texts) > max_texts else texts
        if len(texts) > max_texts:
            logger.info(f"📊 [AI] Sampling {max_texts} texts from {len(texts)} total (to avoid token limits)")
        combined_text = "\n".join([f"- {text}" for text in sample_texts[:50]])
        logger.debug(f"📝 [AI] Using {len(sample_texts[:50])} texts in prompt")
        
        prompt = f"""Analyze the following customer feedback and extract the top {top_k} most impactful terms/phrases.

For each term, provide:
- The term/phrase itself
- How frequently it appears (freq: integer)
- Average sentiment (-1.0 to +1.0, where -1 is very negative, +1 is very positive)

Feedback:
{combined_text}

Return a JSON array of objects with "term", "freq", and "sentiment" keys.
Example:
[
  {{"term": "app crashes", "freq": 15, "sentiment": -0.9}},
  {{"term": "fast checkout", "freq": 8, "sentiment": 0.85}},
  ...
]

Return ONLY valid JSON, no other text."""

        try:
            logger.info(f"📤 [AI] Calling OpenAI API for impact terms extraction (requesting {top_k} terms)")
            logger.debug(f"🔍 [AI] Sending request to OpenAI GPT-3.5-turbo for impact terms")
            # Use structured output if available, otherwise rely on prompt
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a data analyst extracting impactful terms from customer feedback with frequency and sentiment scores. Always return valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500,
                    response_format={"type": "json_object"}
                )
                logger.debug("✅ [AI] Using JSON response format")
            except TypeError:
                logger.warning("⚠️ [AI] response_format not supported, using standard format")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a data analyst extracting impactful terms from customer feedback with frequency and sentiment scores. Always return valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
            
            logger.info("✅ [AI] OpenAI API response received for impact terms")
            logger.debug(f"📥 [AI] Response tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    terms = data.get("terms", data.get("results", data.get("impact_terms", [])))
                else:
                    terms = data
                
                if not isinstance(terms, list):
                    terms = []
                
                # Validate and normalize
                result = []
                for item in terms[:top_k]:
                    if isinstance(item, dict):
                        term = item.get("term", item.get("phrase", ""))
                        freq = int(item.get("freq", item.get("frequency", 1)))
                        sentiment = float(item.get("sentiment", item.get("sent", 0.0)))
                        
                        if term:
                            result.append({
                                "term": str(term).strip(),
                                "freq": max(1, freq),
                                "sentiment": max(-1.0, min(1.0, sentiment))
                            })
                
                if result:
                    logger.info(f"✅ [AI] Successfully extracted {len(result)} impact terms from OpenAI response")
                    logger.debug(f"📊 [AI] Top terms: {[r['term'] for r in result[:5]]}")
                    return result[:top_k]
                else:
                    logger.warning("⚠️ [AI] No impact terms extracted from JSON response")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ [AI] JSON parsing failed: {e}, attempting alternative parsing")
                # Try to extract from markdown
                json_match = re.search(r'```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    logger.debug("🔍 [AI] Found JSON in markdown code block")
                    data = json.loads(json_match.group(1))
                    terms = data if isinstance(data, list) else data.get("terms", [])
                    result = []
                    for item in terms[:top_k]:
                        if isinstance(item, dict):
                            term = item.get("term", "")
                            freq = int(item.get("freq", 1))
                            sentiment = float(item.get("sentiment", 0.0))
                            if term:
                                result.append({
                                    "term": str(term).strip(),
                                    "freq": max(1, freq),
                                    "sentiment": max(-1.0, min(1.0, sentiment))
                                })
                    if result:
                        logger.info(f"✅ [AI] Extracted {len(result)} impact terms from markdown JSON")
                        return result[:top_k]
        
        except Exception as e:
            logger.error(f"❌ [AI] Error in OpenAI API call for impact terms: {e}")
            raise
        
        logger.warning("⚠️ [AI] No impact terms extracted, returning empty list")
        return []
        
    except ImportError:
        logger.error("❌ [AI] OpenAI library not installed. Install with: pip install openai")
        raise ValueError("OpenAI library not installed. Install with: pip install openai")
    except Exception as e:
        logger.error(f"❌ [AI] Fatal error in extract_impact_terms: {e}")
        raise

def summarize_overall(trend_text: str, prio_text: str, max_bullets: int = 5) -> str:
    """Generate overall summary"""
    if not OPENAI_API_KEY:
        return "Enable OpenAI to generate summaries"
    
    try:
        client = _get_openai_client()
        
        prompt = f"""Based on the following analysis data, create a concise executive summary with {max_bullets} key points.

Trend Analysis:
{trend_text}

Priority Themes:
{prio_text}

Provide a clear, actionable summary focusing on the most important insights."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a business analyst creating executive summaries from data analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.warning(f"Error generating summary: {e}")
        return f"Summary generation failed: {str(e)}"

def recommend_actions(themes: List[str]) -> str:
    """Generate action recommendations"""
    if not OPENAI_API_KEY:
        return "Enable OpenAI to generate recommendations"
    
    if not themes:
        return "No themes provided for recommendations"
    
    try:
        client = _get_openai_client()
        
        themes_text = "\n".join([f"- {theme}" for theme in themes[:20]])
        
        prompt = f"""Based on these key themes from customer feedback, provide actionable recommendations:

Themes:
{themes_text}

Provide 3-5 specific, actionable recommendations to address these issues."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a business consultant providing actionable recommendations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.warning(f"Error generating recommendations: {e}")
        return f"Recommendation generation failed: {str(e)}"

