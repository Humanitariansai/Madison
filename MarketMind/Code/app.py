# app.py
import os
import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from main import run_analysis

OUTPUT_DIR = "outputs"


# ----------------------------
# Helpers
# ----------------------------
def safe_load_json(path: str):
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def safe_read_text(path: str):
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def parse_csv_list(text: str):
    # accepts comma or newline separated
    items = []
    for part in (text or "").replace("\n", ",").split(","):
        p = part.strip()
        if p:
            items.append(p)

    # de-duplicate preserving order (case-insensitive)
    seen = set()
    out = []
    for x in items:
        k = x.lower()
        if k not in seen:
            out.append(x)
            seen.add(k)
    return out


def ensure_outputs_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def fmt_price(x):
    try:
        return float(x)
    except Exception:
        return None


def clamp_int(x, lo=0, hi=100, default=0):
    try:
        v = int(round(float(x)))
        return max(lo, min(hi, v))
    except Exception:
        return default


# ----------------------------
# Page + Styles
# ----------------------------
st.set_page_config(page_title="MarketMind", page_icon="🧠", layout="wide")

CUSTOM_CSS = """
<style>
.block-container { padding-top: 1.25rem; }

/* Hero */
.mm-hero {
  padding: 18px 18px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.08);
  background: linear-gradient(135deg, rgba(59,130,246,0.18), rgba(236,72,153,0.10));
}
.mm-hero h1 { margin: 0; font-size: 2rem; }
.mm-hero p { margin: .4rem 0 0; opacity: .9; }

/* Card */
.mm-card {
  padding: 16px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.03);
}

/* Sidebar header */
.mm-side-h { font-weight: 700; margin-top: .5rem; }

/* Buttons */
div.stButton > button { border-radius: 12px; padding: 0.6rem 1rem; }

/* Expander */
div[data-testid="stExpander"] details { border-radius: 14px; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

ensure_outputs_dir()

# A single shared palette for charts (pie + bars + lines)
MM_PALETTE = [
    "#60A5FA",  # blue
    "#F472B6",  # pink
    "#34D399",  # green
    "#FBBF24",  # amber
    "#A78BFA",  # purple
    "#FB7185",  # rose
    "#22C55E",  # emerald
    "#38BDF8",  # sky
    "#F59E0B",  # orange
]


# ----------------------------
# Hero
# ----------------------------
st.markdown(
    """
<div class="mm-hero">
  <h1>🧠 MarketMind</h1>
  <p>AI market research reports + dashboards for competitor intel, source-aware sentiment, feature benchmarking, and product demand trend.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")

# ----------------------------
# Sidebar Inputs
# ----------------------------
with st.sidebar:
    st.markdown("### ⚙️ Configure your analysis")
    st.caption("Tip: add 2–4 competitors and 4–7 features for best results.")

    with st.form("mm_form", clear_on_submit=False):
        product_name = st.text_input("Product Name", value="Lao Gan Ma Chili Crisp")
        industry = st.text_input("Industry", value="Food & Beverage")
        geography = st.text_input("Geography", value="US")
        scale = st.selectbox("Business Scale", ["Startup", "SME", "Enterprise"], index=1)

        st.markdown("---")
        st.markdown("<div class='mm-side-h'>🧩 Custom comparison inputs</div>", unsafe_allow_html=True)

        competitors_raw = st.text_area(
            "Competitors (comma or newline separated)",
            value="Fly By Jing Sichuan Chili Crisp, Momofuku Chili Crunch, Trader Joe’s Chili Onion Crunch",
            height=80,
        )
        features_raw = st.text_area(
            "Features (comma or newline separated)",
            value="Ingredients, Spice Level, Texture, Flavor Profile, Packaging, Price",
            height=80,
        )

        run_btn = st.form_submit_button("🚀 Run Market Research")

competitors_list = parse_csv_list(competitors_raw)
features_list = parse_csv_list(features_raw)

# ----------------------------
# Run Analysis
# ----------------------------
if run_btn:
    if len(competitors_list) < 1:
        st.error("Please enter at least 1 competitor.")
    elif len(features_list) < 3:
        st.warning("Radar works best with 3+ features (you can still run).")
    else:
        with st.spinner("Running AI analysis..."):
            try:
                result = run_analysis(
                    product_name=product_name,
                    industry=industry,
                    geography=geography,
                    scale=scale,
                    competitors=competitors_list,
                    features=features_list,
                )
                st.success("✅ Analysis completed")
                st.session_state["last_run"] = datetime.utcnow().isoformat()
                st.session_state["last_files"] = result.get("files_written", [])
            except Exception as e:
                st.error("❌ Error running analysis. Check Render logs for details.")
                st.exception(e)

st.write("")

# ----------------------------
# Load Outputs
# ----------------------------
prices_json = safe_load_json(os.path.join(OUTPUT_DIR, "competitor_prices.json"))
scores_json = safe_load_json(os.path.join(OUTPUT_DIR, "feature_scores.json"))
growth_json = safe_load_json(os.path.join(OUTPUT_DIR, "market_growth.json"))

# Prefer the single source of truth if present
sentiment_verified = safe_load_json(os.path.join(OUTPUT_DIR, "sentiment_verified.json"))
sentiment_metrics = safe_load_json(os.path.join(OUTPUT_DIR, "sentiment_metrics.json"))
review_sent_md = safe_read_text(os.path.join(OUTPUT_DIR, "review_sentiment.md"))

# Resolve sentiment numbers:
# - before analysis: show 0/0/0 (per your request)
# - after analysis: prefer sentiment_verified, else sentiment_metrics
pos = neg = neu = 0
if isinstance(sentiment_verified, dict):
    s = sentiment_verified.get("sentiment", {}) or {}
    pos = clamp_int(s.get("positive", 0), default=0)
    neg = clamp_int(s.get("negative", 0), default=0)
    neu = clamp_int(s.get("neutral", 0), default=0)
elif isinstance(sentiment_metrics, dict):
    pos = clamp_int(sentiment_metrics.get("positive", 0), default=0)
    neg = clamp_int(sentiment_metrics.get("negative", 0), default=0)
    neu = clamp_int(sentiment_metrics.get("neutral", 0), default=0)

# ----------------------------
# Tabs
# ----------------------------
tab_overview, tab_pricing, tab_features, tab_growth, tab_reports = st.tabs(
    ["🏠 Overview", "💰 Pricing", "⚙️ Features", "📈 Product Trend", "📘 Reports"]
)

# ============================
# Overview
# ============================
with tab_overview:
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])

    with c1:
        st.markdown("<div class='mm-card'>", unsafe_allow_html=True)
        st.subheader("Study configuration")
        st.markdown(f"**Product:** {product_name}")
        st.markdown(f"**Industry:** {industry}")
        st.markdown(f"**Geography:** {geography}  |  **Scale:** {scale}")
        st.markdown(f"**Competitors:** {', '.join(competitors_list) if competitors_list else '—'}")
        st.markdown(f"**Features:** {', '.join(features_list) if features_list else '—'}")
        if st.session_state.get("last_run"):
            st.caption(f"Last run (UTC): {st.session_state['last_run']}")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='mm-card'>", unsafe_allow_html=True)
        st.metric("Positive", f"{pos}%")
        st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='mm-card'>", unsafe_allow_html=True)
        st.metric("Negative", f"{neg}%")
        st.markdown("</div>", unsafe_allow_html=True)
    with c4:
        st.markdown("<div class='mm-card'>", unsafe_allow_html=True)
        st.metric("Neutral", f"{neu}%")
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.subheader("💬 Sentiment (source-aware)")

    if not (sentiment_verified or sentiment_metrics):
        st.info("Run the analysis to generate sentiment analysis.")
    else:
        df_sentiment = pd.DataFrame(
            {"Sentiment": ["Positive", "Negative", "Neutral"], "Percentage": [pos, neg, neu]}
        )
        fig_sent = px.pie(
            df_sentiment,
            names="Sentiment",
            values="Percentage",
            hole=0.35,
            title=f"Sentiment Breakdown for {product_name}",
            color="Sentiment",
            color_discrete_sequence=MM_PALETTE[:3],  # keep consistent
        )
        fig_sent.update_traces(textinfo="percent+label")
        st.plotly_chart(fig_sent, use_container_width=True)

        # IMPORTANT: per your request, do NOT show quotes/sources under the pie chart.
        st.caption("Quotes + sources are available in the **review_sentiment.md** report (Reports tab).")

# ============================
# Pricing
# ============================
with tab_pricing:
    st.subheader("💰 Competitor Pricing Overview (AI-fetched)")
    st.caption("If a price couldn’t be verified, it may be missing (null).")

    if not prices_json:
        st.info("Run analysis to generate competitor pricing.")
    else:
        df_price = pd.DataFrame(prices_json.get("prices", []))
        if not df_price.empty:
            if "name" in df_price.columns:
                df_price = df_price.rename(columns={"name": "Competitor"})
            if "price" in df_price.columns:
                df_price = df_price.rename(columns={"price": "Price"})

            if "Competitor" not in df_price.columns:
                df_price["Competitor"] = None
            if "Price" not in df_price.columns:
                df_price["Price"] = None

            df_price["Price"] = df_price["Price"].apply(fmt_price)
            df_price = df_price.dropna(subset=["Competitor"])

            allowed = set([product_name] + competitors_list)
            df_price = df_price[df_price["Competitor"].isin(allowed)]
            df_price = df_price.dropna(subset=["Price"])

        if df_price.empty:
            st.warning("No verified prices found to plot for your selected competitors/product.")
        else:
            # Multi-color bars that match the palette (same family as pie)
            fig_price = px.bar(
                df_price,
                x="Competitor",
                y="Price",
                color="Competitor",
                title=f"Verified Pricing (USD) — {product_name} vs competitors",
                color_discrete_sequence=MM_PALETTE,
            )
            fig_price.update_traces(texttemplate=None)
            fig_price.update_layout(
                yaxis_title="Price (USD)",
                legend_title_text="",
            )
            st.plotly_chart(fig_price, use_container_width=True)

            with st.expander("🔎 Raw pricing JSON", expanded=False):
                st.json(prices_json)

# ============================
# Features
# ============================
with tab_features:
    st.subheader("⚙️ Feature Comparison Radar")
    st.caption("Uses ONLY the features you entered. Compares product + each competitor.")

    rows = (scores_json or {}).get("scores", [])
    if not rows:
        st.info("No AI feature scores found. Run analysis again.")
    else:
        df_scores = pd.DataFrame(rows)
        df_scores.columns = [c.strip().lower() for c in df_scores.columns]

        required = {"product", "feature", "score"}
        if not required.issubset(set(df_scores.columns)):
            st.error(f"feature_scores.json missing fields. Found: {list(df_scores.columns)}")
        else:
            df_scores["score"] = pd.to_numeric(df_scores["score"], errors="coerce")
            df_scores = df_scores.dropna(subset=["score"])

            selected_products = [product_name] + competitors_list
            df_scores = df_scores[df_scores["product"].isin(selected_products)]
            df_scores = df_scores[df_scores["feature"].isin(features_list)]

            present = sorted(df_scores["product"].unique().tolist())
            missing = [p for p in selected_products if p not in present]
            if missing:
                st.warning(f"Missing score rows for: {', '.join(missing)} (your prompt should force full coverage).")

            if df_scores.empty:
                st.info("No scores matched your selected competitors/features. Run analysis again.")
            else:
                fig_radar = px.line_polar(
                    df_scores,
                    r="score",
                    theta="feature",
                    color="product",
                    line_close=True,
                    title=f"Feature Comparison: {product_name} vs Selected Competitors",
                    color_discrete_sequence=MM_PALETTE,
                )
                fig_radar.update_traces(fill="toself", opacity=0.55)
                st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("---")
    st.subheader("📄 Feature Comparison Report (table)")
    feat_md = safe_read_text(os.path.join(OUTPUT_DIR, "feature_comparison.md"))
    if not feat_md:
        st.info("feature_comparison.md not found yet. Run analysis.")
    else:
        st.markdown(feat_md)

# ============================
# Product Trend
# ============================
with tab_growth:
    st.subheader("📈 Product Demand / Growth Trend")
    st.caption("This should be product-specific (not generic industry growth).")

    if not growth_json:
        st.info("Run analysis to generate product trend.")
    else:
        years = growth_json.get("years", [])
        growth = growth_json.get("growth_percent", [])

        if not years or not growth or len(years) != len(growth):
            st.warning("market_growth.json is incomplete.")
        else:
            df_growth = pd.DataFrame({"Year": years, "Demand / Growth (%)": growth})
            fig_growth = px.line(
                df_growth,
                x="Year",
                y="Demand / Growth (%)",
                markers=True,
                title=f"{product_name} — Demand / Growth Trend ({geography})",
                color_discrete_sequence=[MM_PALETTE[0]],
            )
            fig_growth.update_layout(xaxis=dict(type="category"))
            st.plotly_chart(fig_growth, use_container_width=True)

            rationale = growth_json.get("rationale")
            if rationale:
                with st.expander("Why this trend?", expanded=False):
                    st.write(rationale)

        with st.expander("🔎 Raw trend JSON", expanded=False):
            st.json(growth_json)

# ============================
# Reports
# ============================
with tab_reports:
    st.subheader("📘 Full Market Research Reports")

    md_files = []
    if os.path.exists(OUTPUT_DIR):
        md_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".md")]

    if not md_files:
        st.info("No markdown reports found yet. Run analysis first.")
    else:
        preferred_order = [
            "research_plan.md",
            "customer_analysis.md",
            "review_sentiment.md",
            "feature_comparison.md",
            "final_market_strategy_report.md",
        ]
        ordered = [f for f in preferred_order if f in md_files] + sorted(
            [f for f in md_files if f not in preferred_order]
        )

        for md_file in ordered:
            content = safe_read_text(os.path.join(OUTPUT_DIR, md_file)) or ""
            with st.expander(f"📄 {md_file}", expanded=False):
                st.markdown(content)

        st.markdown("---")
        st.caption("Tip: If a report is missing, ensure main.py writes it even if empty (write the file anyway).")
