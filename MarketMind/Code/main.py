import os
import json
import logging
import traceback
from typing import Optional, Dict, Any, List

from crewai import Crew
from agents import MarketResearchAgents
from tasks import MarketResearchTasks
from tools.feature_comparison import FeatureComparisonTool

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("MarketMind")


def _safe_json_loads(text: str) -> Optional[dict]:
    try:
        return json.loads(text)
    except Exception:
        return None


def _write_json(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _normalize_price(val: Any) -> str:
    s = str(val).strip()
    if not s:
        return ""
    s = s.replace("$", "").strip()
    return f"${s}"


def _write_review_sentiment_md(outputs_dir: str, payload: dict) -> str:
    sentiment = payload.get("sentiment", {})
    pos = sentiment.get("positive", 60)
    neg = sentiment.get("negative", 30)
    neu = sentiment.get("neutral", 10)

    pos_themes = payload.get("top_positive_themes", [])
    neg_themes = payload.get("top_negative_themes", [])
    quotes = payload.get("sample_quotes", {})

    lines = []
    lines.append("# Review Sentiment Summary\n")
    lines.append(f"**Positive:** {pos}%  ")
    lines.append(f"**Negative:** {neg}%  ")
    lines.append(f"**Neutral:** {neu}%\n")

    if pos_themes:
        lines.append("\n## Top Positive Themes")
        for t in pos_themes[:5]:
            lines.append(f"- {t}")

    if neg_themes:
        lines.append("\n## Top Negative Themes")
        for t in neg_themes[:5]:
            lines.append(f"- {t}")

    if quotes:
        lines.append("\n## Sample Customer Quotes")
        if quotes.get("positive"):
            lines.append("\n**Positive:**")
            for q in quotes["positive"][:3]:
                lines.append(f"> {q}")
        if quotes.get("negative"):
            lines.append("\n**Negative:**")
            for q in quotes["negative"][:3]:
                lines.append(f"> {q}")

    path = os.path.join(outputs_dir, "review_sentiment.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).strip() + "\n")
    return path


def feature_comparison_json_to_md(payload: dict) -> str:
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
        return "\n".join(md)

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


def patch_price_row_from_competitor_prices(
    fc_payload: dict,
    pricing_json: dict,
    product_name: str,
    competitors: List[str],
) -> dict:
    """
    Overwrites Price row using competitor_prices.json.
    Supports real column names AND generic Competitor A/B/C.
    Also case-insensitive so it doesn't miss.
    """
    if not fc_payload or "comparison_table" not in fc_payload:
        return fc_payload

    # lowercase map for matching
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

    # generic mapping: Competitor A -> competitors[0], etc.
    generic_map: Dict[str, str] = {}
    for i, comp in enumerate(competitors):
        generic_map[f"competitor {chr(ord('a') + i)}"] = comp.lower()

    # locate the price row
    for row in fc_payload["comparison_table"]:
        feat = str(row.get("feature", "")).strip().lower()
        if feat in {"price", "pricing"}:
            for col in list(row.keys()):
                if col == "feature":
                    continue
                col_key = str(col).strip().lower()

                # Case 1: real name column
                if col_key in price_map:
                    row[col] = fmt(price_map[col_key])
                    continue

                # Case 2: generic Competitor A/B/C
                if col_key in generic_map:
                    real_key = generic_map[col_key]
                    if real_key in price_map:
                        row[col] = fmt(price_map[real_key])

            # ensure main product is set even if column name differs slightly
            # (only if there is a column that "looks like" the product name)
            prod_key = product_name.strip().lower()
            if prod_key in price_map:
                for col in list(row.keys()):
                    if col == "feature":
                        continue
                    if col.strip().lower() == prod_key:
                        row[col] = fmt(price_map[prod_key])
                        break
            break

    return fc_payload


def run_analysis(
    product_name: Optional[str] = None,
    industry: Optional[str] = None,
    geography: Optional[str] = None,
    scale: Optional[str] = None,
    competitors: Optional[List[str]] = None,
    features: Optional[List[str]] = None,
) -> Dict[str, Any]:

    product_name = product_name or "EcoWave Smart Bottle"
    industry = industry or "Consumer Goods"
    geography = geography or "US"
    scale = scale or "SME"
    competitors = competitors or []
    features = features or []

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
        persona_task = tasks.customer_persona_task(persona_agent, product_name, industry)

        pricing_task = tasks.competitor_pricing_json_task(
            competitor_agent, product_name, industry, competitors
        )
        feature_scores_task = tasks.feature_scores_json_task(
            competitor_agent, product_name, industry, competitors, features
        )
        growth_task = tasks.market_growth_json_task(
            competitor_agent, product_name, industry, geography, scale, competitors
        )
        review_task = tasks.review_analysis_task(sentiment_agent, product_name)

        feature_tool = FeatureComparisonTool()
        raw_feature_output = (
            feature_tool.run(product_name, industry)
            if hasattr(feature_tool, "run")
            else feature_tool._run(product_name, industry)
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

        # ---- Pricing JSON (source of truth) ----
        pricing_json = _safe_json_loads(str(getattr(pricing_task, "output", ""))) or {
            "product": product_name,
            "currency": "USD",
            "prices": [{"name": product_name, "price": 0}],
        }
        prices_path = os.path.join(outputs_dir, "competitor_prices.json")
        _write_json(prices_path, pricing_json)
        files_written.append(prices_path)

        # ---- Feature comparison -> patch Price row -> markdown ----
        fc_payload = _safe_json_loads(str(raw_feature_output)) if raw_feature_output else None
        if fc_payload and isinstance(fc_payload, dict):
            fc_payload = patch_price_row_from_competitor_prices(
                fc_payload,
                pricing_json,
                product_name=product_name,
                competitors=competitors,
            )
            feature_md = feature_comparison_json_to_md(fc_payload)
        else:
            feature_md = str(raw_feature_output or "")

        feature_md_path = os.path.join(outputs_dir, "feature_comparison.md")
        with open(feature_md_path, "w", encoding="utf-8") as f:
            f.write(feature_md)
        files_written.append(feature_md_path)

        # ---- Feature scores JSON (flat schema) ----
        scores_json = _safe_json_loads(str(getattr(feature_scores_task, "output", ""))) or {
            "product": product_name,
            "scores": [],
        }
        scores_path = os.path.join(outputs_dir, "feature_scores.json")
        _write_json(scores_path, scores_json)
        files_written.append(scores_path)

        # ---- Market growth JSON ----
        growth_json = _safe_json_loads(str(getattr(growth_task, "output", ""))) or {
            "industry": industry,
            "geography": geography,
            "years": ["2023", "2024", "2025", "2026"],
            "growth_percent": [12, 18, 24, 33],
            "rationale": "Fallback growth curve.",
        }
        growth_path = os.path.join(outputs_dir, "market_growth.json")
        _write_json(growth_path, growth_json)
        files_written.append(growth_path)

        # ---- Sentiment (single source of truth) ----
        sentiment_payload = _safe_json_loads(str(getattr(review_task, "output", ""))) or {
            "product": product_name,
            "sentiment": {"positive": 60, "negative": 30, "neutral": 10},
            "top_positive_themes": [],
            "top_negative_themes": [],
            "sample_quotes": {"positive": [], "negative": []},
        }

        sentiment_metrics = sentiment_payload.get("sentiment", {"positive": 60, "negative": 30, "neutral": 10})
        sentiment_json_path = os.path.join(outputs_dir, "sentiment_metrics.json")
        _write_json(sentiment_json_path, sentiment_metrics)
        files_written.append(sentiment_json_path)

        review_md_path = _write_review_sentiment_md(outputs_dir, sentiment_payload)
        files_written.append(review_md_path)

        # ---- Markdown reports ----
        md_map = {
            "research_plan.md": getattr(planning_task, "output", ""),
            "customer_analysis.md": getattr(persona_task, "output", ""),
            "final_market_strategy_report.md": getattr(synthesis_task, "output", ""),
        }
        for name, content in md_map.items():
            if content:
                path = os.path.join(outputs_dir, name)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(str(content))
                files_written.append(path)

        return {"success": True, "outputs_dir": outputs_dir, "files_written": files_written}

    except Exception as e:
        logger.error("❌ Analysis failed: %s", e)
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    run_analysis()




