from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional, List

from wordcloud import WordCloud, STOPWORDS


def build_wordcloud_image(
    df,
    text_col: str,
    out_path: Path,
    sent_col: str = "sent_compound",   # or "sent_label"
    width: int = 1200,
    height: int = 800,
) -> Optional[Path]:
    """
    Impact-based sentiment word cloud from a DataFrame.

    - df[text_col]: free-text comments
    - df[sent_col]: sentiment per row (either:
        - string: 'positive' | 'neutral' | 'negative'
        - numeric: -1..+1)
    - SIZE = impact = frequency * |average_sentiment|
    - COLOR:
        positive → green (#2ecc71)
        negative → red   (#e74c3c)
        neutral  → gray  (#7f8c8d)
    """

    if text_col not in df.columns or sent_col not in df.columns:
        return None

    # ---------- 1) numeric sentiment per row ----------
    s = df[sent_col]
    if s.dtype == "O":  # string labels
        mapping = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        sent_scores = s.map(mapping).fillna(0.0)
    else:
        sent_scores = s.fillna(0.0)

    # ---------- 2) tokenize and filter stopwords ----------
    base_stop = set(STOPWORDS)
    extra_stop = {
        "update", "updates", "app", "very", "really", "nice",
        "good", "bad", "the", "this", "that", "now", "new",
        "experience", "overall", "great", "service",
    }
    stopwords = base_stop | extra_stop

    def tokenize(text: str):
        for w in str(text).split():
            w = "".join(ch for ch in w if ch.isalnum()).lower()
            if w and w not in stopwords and len(w) > 2:
                yield w

    # ---------- 3) accumulate per-word counts + sentiment sum ----------
    word_counts: Counter[str] = Counter()
    word_sent_sum: defaultdict[str, float] = defaultdict(float)

    for text, score in zip(df[text_col].astype(str), sent_scores):
        for w in tokenize(text):
            word_counts[w] += 1
            word_sent_sum[w] += float(score)

    if not word_counts:
        return None

    def avg_sent(word: str) -> float:
        c = word_counts[word]
        return (word_sent_sum[word] / c) if c else 0.0

    # ---------- 4) compute impact weights ----------
    impact_freqs: dict[str, float] = {}
    sentiments: dict[str, float] = {}

    for w, freq in word_counts.items():
        avg = avg_sent(w)
        impact = freq * abs(avg)  # core: freq × |avg_sentiment|
        if impact > 0:
            impact_freqs[w] = impact
            sentiments[w] = avg

    if not impact_freqs:
        return None

    # keep top N most impactful words to avoid clutter
    impact_freqs = dict(
        sorted(impact_freqs.items(), key=lambda kv: kv[1], reverse=True)[:150]
    )

    # ---------- 5) color function ----------
    def color_func(word, *args, **kwargs):
        s_val = sentiments.get(word.lower(), 0.0)
        if s_val > 0.05:
            return "#2ecc71"  # green
        elif s_val < -0.05:
            return "#e74c3c"  # red
        else:
            return "#7f8c8d"  # gray

    # ---------- 6) generate cloud ----------
    wc = WordCloud(
        width=width,
        height=height,
        background_color="white",
        color_func=color_func,
        collocations=False,
    )

    wc = wc.generate_from_frequencies(impact_freqs)
    img = wc.to_image()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def build_ai_impact_wordcloud(
    terms: List[dict],
    out_path: Path,
    width: int = 1200,
    height: int = 800,
) -> Optional[Path]:
    """
    Build an impact-based word cloud from AI-returned terms.

    terms = [
      {
        "term": "mobile app crashes",
        "freq": 12,
        "sentiment": -0.85   # avg sentiment for that term
      },
      ...
    ]

    - SIZE  = impact = freq * abs(sentiment)
    - COLOR = green (positive) / red (negative) / gray (neutral)
    """

    if not terms:
        return None

    freqs: dict[str, float] = {}
    sentiments: dict[str, float] = {}

    for t in terms:
        term = str(t.get("term", "")).lower().strip()
        if not term:
            continue

        try:
            freq = int(t.get("freq", 0))
        except Exception:
            freq = 0

        try:
            sent = float(t.get("sentiment", 0.0))
        except Exception:
            sent = 0.0

        impact = freq * abs(sent)
        if impact > 0:
            freqs[term] = impact
            sentiments[term] = sent

    if not freqs:
        return None

    def color_func(word, *args, **kwargs):
        s_val = sentiments.get(word.lower(), 0.0)
        if s_val > 0.05:
            return "#2ecc71"  # green
        elif s_val < -0.05:
            return "#e74c3c"  # red
        else:
            return "#7f8c8d"  # gray

    wc = WordCloud(
        width=width,
        height=height,
        background_color="white",
        color_func=color_func,
        collocations=False,
    )

    wc = wc.generate_from_frequencies(freqs)
    img = wc.to_image()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path
