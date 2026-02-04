import re
from collections import Counter
from typing import List, Dict, Any

from nltk.sentiment.vader import SentimentIntensityAnalyzer


_STOPWORDS = {
    "the","and","a","an","to","of","in","it","is","was","for","on","with","this","that","as",
    "are","be","but","not","have","had","my","we","they","you","i","at","so","if","or",
    "from","by","their","its","them","there","when","what","which","who","will","can","just",
    "very","really","too","also"
}

def _normalize_product_tokens(product_name: str) -> List[str]:
    # break into useful tokens: "Lao Gan Ma Chili Crisp" -> ["lao","gan","ma","chili","crisp","laoganma"]
    base = re.sub(r"[^a-zA-Z0-9\s]", " ", product_name.lower()).split()
    joined = "".join(base)
    tokens = [t for t in base if len(t) >= 3]
    if len(joined) >= 5:
        tokens.append(joined)
    return list(dict.fromkeys(tokens))  # dedupe preserving order


def _split_sentences(text: str) -> List[str]:
    # lightweight sentence split (no extra deps)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[\.\!\?])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) >= 20]


def _mentions_product(sentence: str, tokens: List[str]) -> bool:
    s = sentence.lower()
    # allow partial mentions to catch "laoganma" style
    return any(t in s for t in tokens)


def _extract_keywords(sentences: List[str], top_k: int = 6) -> List[str]:
    words = []
    for s in sentences:
        # words only
        ws = re.findall(r"[a-zA-Z]{3,}", s.lower())
        ws = [w for w in ws if w not in _STOPWORDS]
        words.extend(ws)
    counts = Counter(words)
    # remove super-generic review words
    for bad in ["product","buy","bought","use","used","using","great","good","bad","love"]:
        counts.pop(bad, None)
    return [w for w, _ in counts.most_common(top_k)]


def analyze_sources_sentiment(
    product_name: str,
    sources: List[Dict[str, Any]],
    max_quotes_per_bucket: int = 2
) -> Dict[str, Any]:
    """
    sources: list of {"url":..., "title":..., "text":...}
    Returns a VERIFIED sentiment payload:
    - quotes are verbatim sentences from sources
    - every quote has a url
    - if not enough product-linked sentences: no_verified_sources=true
    """
    analyzer = SentimentIntensityAnalyzer()
    tokens = _normalize_product_tokens(product_name)

    pos_sents = []
    neg_sents = []
    neu_sents = []

    quote_pool = {"positive": [], "negative": [], "neutral": []}

    for src in sources:
        url = src.get("url", "")
        text = src.get("text", "") or ""
        for sent in _split_sentences(text):
            if not _mentions_product(sent, tokens):
                continue

            score = analyzer.polarity_scores(sent)["compound"]
            if score >= 0.25:
                pos_sents.append(sent)
                quote_pool["positive"].append({"quote": sent, "url": url})
            elif score <= -0.25:
                neg_sents.append(sent)
                quote_pool["negative"].append({"quote": sent, "url": url})
            else:
                neu_sents.append(sent)
                quote_pool["neutral"].append({"quote": sent, "url": url})

    total = len(pos_sents) + len(neg_sents) + len(neu_sents)

    # If nothing matched the product, we refuse to pretend
    if total < 8:
        return {
            "product": product_name,
            "no_verified_sources": True,
            "sentiment": {"positive": 0, "negative": 0, "neutral": 0},
            "themes": {"positive": [], "negative": [], "neutral": []},
            "quotes": [],
            "note": "Not enough product-linked text found in sources to compute verified sentiment."
        }

    pos_pct = round((len(pos_sents) / total) * 100)
    neg_pct = round((len(neg_sents) / total) * 100)
    neu_pct = 100 - pos_pct - neg_pct  # ensure sums to 100

    # themes from actual sentences
    themes = {
        "positive": _extract_keywords(pos_sents, top_k=6),
        "negative": _extract_keywords(neg_sents, top_k=6),
        "neutral": _extract_keywords(neu_sents, top_k=6),
    }

    # pick quotes (verbatim) — also ensure they’re not generic duplicates
    def pick_quotes(bucket: str):
        seen = set()
        out = []
        for q in quote_pool[bucket]:
            key = q["quote"].lower()
            if key in seen:
                continue
            seen.add(key)
            out.append({"polarity": bucket, "quote": q["quote"], "url": q["url"]})
            if len(out) >= max_quotes_per_bucket:
                break
        return out

    quotes = pick_quotes("positive") + pick_quotes("negative")

    return {
        "product": product_name,
        "no_verified_sources": False,
        "sentiment": {"positive": pos_pct, "negative": neg_pct, "neutral": neu_pct},
        "themes": themes,
        "quotes": quotes
    }


