import os
import json
import logging
import traceback
from typing import Optional, Dict, Any, List

from crewai import Crew
from agents import MarketResearchAgents
from tasks import MarketResearchTasks

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("MarketMind")


# -------------------------
# helpers
# -------------------------
def _safe_json_loads(text: str) -> Optional[dict]:
    try:
        return json.loads(text)
    except Exception:
        return None


def _write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _normalize_price(val: Any) -> str:
    s = str(val).strip()
    if not s:
        return ""
    s = s.replace("$", "").strip()
    try:
        return f"${float(s):.2f}"
    except Exception:
        return f"${s}"


def _clamp_int(x: Any, lo: int, hi: int, default: int) -> int:
    try:
        v = int(round(float(x)))
        return max(lo, min(hi, v))
    except Exception:
        return default


def _normalize_sentiment_payload(payload: dict, product_name: str) -> dict:
    """
    Enforce consistent sentiment schema so:
    - pie chart and review_sentiment.md match (single source of truth)
    - sums are normalized to 100
    - quotes require url (source-backed)
    """
    if not isinstance(payload, dict):
        payload = {}

    payload.setdefault("product", product_name)
    payload.setdefault("no_verified_sources", True)
    payload.setdefault("sentiment", {"positive": 0, "negative": 0, "neutral": 0})
    payload.setdefault("quotes", [])

    sent = payload.get("sentiment", {})
    if not isinstance(sent, dict):
        sent = {"positive": 0, "negative": 0, "neutral": 0}

    pos = _clamp_int(sent.get("positive", 0), 0, 100, 0)
    neg = _clamp_int(sent.get("negative", 0), 0, 100, 0)
    neu = _clamp_int(sent.get("neutral", 0), 0, 100, 0)

    total = pos + neg + neu
    if total <= 0:
        # safe fallback (but still trustworthy because no sources)
        pos, neg, neu = 60, 30, 10
        total = 100

    # normalize to exactly 100
    pos = int(round(pos * 100 / total))
    neg = int(round(neg * 100 / total))
    neu = 100 - pos - neg

    payload["sentiment"] = {"positive": pos, "negative": neg, "neutral": neu}

    # trust: if no_verified_sources -> quotes empty
    if payload.get("no_verified_sources") is True:
        payload["quotes"] = []

    # keep only source-backed quotes
    quotes = payload.get("quotes", [])
    cleaned = []
    if isinstance(quotes, list):
        for q in quotes:
            if not isinstance(q, dict):
                continue
            qt = str(q.get("quote", "")).strip()
            url = str(q.get("url", "")).strip()
            pol = str(q.get("polarity", "")).strip().lower()
            if qt and url and pol in {"positive", "negative", "neutral"}:
                cleaned.append({"polarity": pol, "quote": qt, "url": url})
    payload["quotes"] = cleaned

    return payload


def feature_comparison_json_to_md(payload: dict) -> str:
    """
    Clean markdown table format (the “before format” you want).
    Uses actual competitor names as columns (no Competitor A/B).
    """
    title = payload.get("title", "Feature Comparison Report")
    industry = payload.get("industry", "")
    summary = payload.get("summary", "")
    table = payload.get("comparison_table", [])

    md = []
    md.append(f"# {title}\n")
    if industry:
        md.append(f"**Industry:** {industry}\n")
    if summary:
        md.append(f"**Summary:** {summary}\n")

    md.append("## Comparison Table\n")
    if not table:
        md.append("_No comparison table generated._\n")
        return "\n".join(md) + "\n"

    cols = [k for k in table[0].keys() if k != "feature"]

    md.append("| Feature | " + " | ".join(cols) + " |")
    md.append("|---|" + "|".join(["---"] * len(cols)) + "|")

    for row in table:
        feat = str(row.get("feature", "")).strip()
        values = []
        for c in cols:
            v = row.get(c, "")
            if feat.lower() in {"price", "pricing"}:
                v = _normalize_price(v)
            values.append(str(v).strip())
        md.append("| " + feat + " | " + " | ".join(values) + " |")

    return "\n".join(md) + "\n"


def patch_price_row_from_pricing_json(fc_payload: dict, pricing_json: dict) -> dict:
    """
    Ensure Price row comes from pricing_json (source of truth).
    """
    if not fc_payload or "comparison_table" not in fc_payload:
        return fc_payload

    price_map: Dict[str, Any] = {}
    for item in pricing_json.get("prices", []):
        nm = str(item.get("name", "")).strip()
        pr = item.get("price", None)
        if nm:
            price_map[nm.lower()] = pr

    def fmt(p: Any) -> str:
        if p is None or p == "":
            return ""
        try:
            return f"${float(p):.2f}"
        except Exception:
            return _normalize_price(p)

    for row in fc_payload["comparison_table"]:
        feat = str(row.get("feature", "")).strip().lower()
        if feat in {"price", "pricing"}:
            for col in list(row.keys()):
                if col == "feature":
                    continue
                key = col.strip().lower()
                if key in price_map:
                    row[col] = fmt(price_map[key])
            break

    return fc_payload


def _write_review_sentiment_md(outputs_dir: str, payload: dict, show_themes: bool = False) -> str:
    """
    TRUST FIX:
    - Themes OFF by default
    - Quotes only if url present
    """
    sentiment = payload.get("sentiment", {})
    pos = int(sentiment.get("positive", 0) or 0)
    neg = int(sentiment.get("negative", 0) or 0)
    neu = int(sentiment.get("neutral", 0) or 0)

    quotes = payload.get("quotes", []) or []
    no_verified = bool(payload.get("no_verified_sources", False))

    lines = []
    lines.append("# Review Sentiment Summary\n")
    lines.append(f"**Positive:** {pos}%  ")
    lines.append(f"**Negative:** {neg}%  ")
    lines.append(f"**Neutral:** {neu}%\n")

    if no_verified:
        lines.append("\n> ⚠️ Sentiment could not be source-verified for this product (no usable review sources were found).")
        lines.append("> Quotes are intentionally omitted to avoid hallucinations.\n")

    if show_themes:
        pos_themes = payload.get("themes", {}).get("positive", []) or []
        neg_themes = payload.get("themes", {}).get("negative", []) or []
        if pos_themes:
            lines.append("\n## Top Positive Themes")
            for t in pos_themes[:5]:
                lines.append(f"- {t}")
        if neg_themes:
            lines.append("\n## Top Negative Themes")
            for t in neg_themes[:5]:
                lines.append(f"- {t}")

    source_quotes = [q for q in quotes if isinstance(q, dict) and q.get("quote") and q.get("url")]

    if source_quotes:
        lines.append("\n## Source-backed Customer Quotes")
        for q in source_quotes[:6]:
            pol = (q.get("polarity") or "").strip().lower()
            quote = str(q.get("quote")).strip()
            url = str(q.get("url")).strip()
            lines.append(f"\n**{pol.title()}:**")
            lines.append(f"> {quote}")
            lines.append(f"- Source: {url}")

    path = os.path.join(outputs_dir, "review_sentiment.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).strip() + "\n")
    return path


# -------------------------
# main entry
# -------------------------
def run_analysis(
    product_name: Optional[str] = None,
    industry: Optional[str] = None,
    geography: Optional[str] = None,
    scale: Optional[str] = None,
    competitors: Optional[List[str]] = None,
    features: Optional[List[str]] = None,
) -> Dict[str, Any]:

    product_name = (product_name or "EcoWave Smart Bottle").strip()
    industry = (industry or "Consumer Goods").strip()
    geography = (geography or "US").strip()
    scale = (scale or "SME").strip()
    competitors = competitors or []
    features = features or []

    def _dedupe(xs: List[str]) -> List[str]:
        out, seen = [], set()
        for x in xs:
            k = x.strip()
            if k and k.lower() not in seen:
                out.append(k)
                seen.add(k.lower())
        return out

    competitors = _dedupe(competitors)
    features = _dedupe(features)

    logger.info("🚀 Running MarketMind analysis for %s (%s)", product_name, industry)

    try:
        agents = MarketResearchAgents()
        tasks = MarketResearchTasks()

        consultant = agents.strategy_consultant()
        competitor_agent = agents.competitor_analyst()
        persona_agent = agents.customer_persona_analyst()
        sentiment_agent = agents.review_analyst()
        synthesizer = agents.lead_strategy_synthesizer()

        planning_task = tasks.research_planning_task(consultant, product_name, industry)
        persona_task = tasks.customer_persona_task(persona_agent, product_name, industry, geography, scale)

        pricing_task = tasks.competitor_pricing_json_task(
            competitor_agent, product_name, industry, competitors
        )

        feature_scores_task = tasks.feature_scores_json_task(
            competitor_agent, product_name, industry, competitors, features
        )

        # ✅ FIXED ORDER: tasks.py expects (agent, product_name, industry, geography, competitors)
        growth_task = tasks.market_growth_json_task(
            competitor_agent, product_name, industry, geography, competitors
        )

        # sentiment task (alias works if your tasks.py defines sentiment_verified_json_task)
        review_task = tasks.sentiment_verified_json_task(
            sentiment_agent, product_name, industry, sources=[]
        )

        synthesis_task = tasks.synthesis_task(
            synthesizer,
            product_name,
            industry,
            [planning_task, pricing_task, feature_scores_task, growth_task, persona_task, review_task],
        )

        crew = Crew(
            agents=[consultant, competitor_agent, persona_agent, sentiment_agent, synthesizer],
            tasks=[
                planning_task,
                pricing_task,
                feature_scores_task,
                growth_task,
                persona_task,
                review_task,
                synthesis_task,
            ],
            verbose=True,
        )

        crew.kickoff()

        outputs_dir = "outputs"
        os.makedirs(outputs_dir, exist_ok=True)
        files_written: List[str] = []

        # ---- Pricing JSON ----
        pricing_json = _safe_json_loads(str(getattr(pricing_task, "output", ""))) or {
            "product": product_name,
            "currency": "USD",
            "prices": [{"name": product_name, "price": None, "source": ""}],
            "notes": "fallback",
        }
        prices_path = os.path.join(outputs_dir, "competitor_prices.json")
        _write_json(prices_path, pricing_json)
        files_written.append(prices_path)

        # ---- Feature Comparison JSON task (with pricing_json) ----
        fc_task = tasks.feature_comparison_json_task(
            competitor_agent,
            product_name,
            industry,
            competitors,
            features,
            pricing_json,
        )

        fc_crew = Crew(agents=[competitor_agent], tasks=[fc_task], verbose=True)
        fc_crew.kickoff()

        fc_payload = _safe_json_loads(str(getattr(fc_task, "output", ""))) or {
            "title": f"Feature Comparison Report for {product_name}",
            "industry": industry,
            "summary": "Fallback feature comparison.",
            "comparison_table": [],
        }

        fc_payload = patch_price_row_from_pricing_json(fc_payload, pricing_json)

        feature_md = feature_comparison_json_to_md(fc_payload)
        feature_md_path = os.path.join(outputs_dir, "feature_comparison.md")
        with open(feature_md_path, "w", encoding="utf-8") as f:
            f.write(feature_md)
        files_written.append(feature_md_path)

        # ---- Feature scores JSON ----
        scores_json = _safe_json_loads(str(getattr(feature_scores_task, "output", ""))) or {
            "product": product_name,
            "competitors": competitors,
            "features": features,
            "scores": [],
        }
        scores_path = os.path.join(outputs_dir, "feature_scores.json")
        _write_json(scores_path, scores_json)
        files_written.append(scores_path)

        # ---- Product demand / growth JSON ----
        growth_json = _safe_json_loads(str(getattr(growth_task, "output", ""))) or {
            "product": product_name,
            "geography": geography,
            "years": ["2023", "2024", "2025", "2026"],
            "growth_percent": [0, 0, 0, 0],
            "rationale": "Fallback demand trend.",
        }

        # tolerate older schema that returns industry/geography
        if "product" not in growth_json:
            growth_json["product"] = product_name
        if "geography" not in growth_json:
            growth_json["geography"] = geography

        growth_path = os.path.join(outputs_dir, "market_growth.json")
        _write_json(growth_path, growth_json)
        files_written.append(growth_path)

        # ---- Sentiment (SINGLE SOURCE OF TRUTH) ----
        raw_sentiment = _safe_json_loads(str(getattr(review_task, "output", ""))) or {
            "product": product_name,
            "no_verified_sources": True,
            "sentiment": {"positive": 60, "negative": 30, "neutral": 10},
            "quotes": [],
        }

        sentiment_payload = _normalize_sentiment_payload(raw_sentiment, product_name)

        # ✅ This file should be used by BOTH pie chart + md (app.py should read this)
        sentiment_verified_path = os.path.join(outputs_dir, "sentiment_verified.json")
        _write_json(sentiment_verified_path, sentiment_payload)
        files_written.append(sentiment_verified_path)

        # optional convenience metrics file (derived from verified)
        sentiment_metrics = sentiment_payload.get("sentiment", {"positive": 60, "negative": 30, "neutral": 10})
        sentiment_json_path = os.path.join(outputs_dir, "sentiment_metrics.json")
        _write_json(sentiment_json_path, sentiment_metrics)
        files_written.append(sentiment_json_path)

        review_md_path = _write_review_sentiment_md(outputs_dir, sentiment_payload, show_themes=False)
        files_written.append(review_md_path)

        # ---- Markdown reports (always write like “before”) ----
        md_map = {
            "research_plan.md": getattr(planning_task, "output", ""),
            "customer_analysis.md": getattr(persona_task, "output", ""),
            "final_market_strategy_report.md": getattr(synthesis_task, "output", ""),
        }
        for name, content in md_map.items():
            path = os.path.join(outputs_dir, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(content or "").strip() + "\n")
            files_written.append(path)

        return {"success": True, "outputs_dir": outputs_dir, "files_written": files_written}

    except Exception as e:
        logger.error("❌ Analysis failed: %s", e)
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    run_analysis()




