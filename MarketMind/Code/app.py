import os
import json
import shutil
import pandas as pd
import plotly.express as px
import streamlit as st

from main import run_analysis

OUTPUT_DIR = "outputs"


def safe_load_json(path: str):
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def parse_csv_list(text: str):
    # accepts comma or newline separated
    items = []
    for part in text.replace("\n", ",").split(","):
        p = part.strip()
        if p:
            items.append(p)
    # de-duplicate preserving order
    seen = set()
    out = []
    for x in items:
        key = x.lower()
        if key not in seen:
            out.append(x)
            seen.add(key)
    return out


# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="MarketMind Dashboard", layout="wide")
st.title("🧠 MarketMind: AI Market Research Assistant")
st.header("📊 MarketMind Insights Dashboard")

st.markdown("""
MarketMind generates **AI-driven market research reports** and dynamic dashboards —
including competitor intelligence, sentiment insights, and growth projections.
""")

# IMPORTANT: never delete outputs at top-level (Streamlit reruns constantly)
os.makedirs(OUTPUT_DIR, exist_ok=True)

with st.expander("⚙️ Configure Product Details", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input("Product Name", "EcoWave Smart Bottle")
        geography = st.text_input("Target Geography", "US")
    with col2:
        industry = st.text_input("Industry", "Consumer Goods")
        scale = st.selectbox("Business Scale", ["Startup", "SME", "Enterprise"], index=1)

    st.markdown("### 🧩 Custom Comparison Inputs")
    competitors_raw = st.text_input(
        "Competitors (comma-separated)",
        "HidrateSpark Pro, LARQ Bottle PureVis, Ozmo Smart Bottle"
    )
    features_raw = st.text_input(
        "Features (comma-separated)",
        "Design, Performance, Battery, Integration, Price"
    )

    # ✅ FIX: use the correct function name
    competitors_list = parse_csv_list(competitors_raw)
    features_list = parse_csv_list(features_raw)

    if len(competitors_list) == 0:
        st.warning("Enter at least 1 competitor.")
    if len(features_list) < 3:
        st.info("Radar works best with 3+ features.")

st.markdown("---")

# ----------------------------
# Run Analysis
# ----------------------------
if st.button("🚀 Run Market Research Analysis"):
    with st.spinner("Running AI analysis... this can take 1–3 minutes."):

        # ✅ Clear outputs ONLY when button is clicked (optional but recommended)
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        try:
            result = run_analysis(
                product_name=product_name,
                industry=industry,
                geography=geography,
                scale=scale,
                competitors=competitors_list,
                features=features_list
            )
            st.success("✅ Analysis completed successfully!")
            st.json({
                "outputs_dir": result.get("outputs_dir"),
                "files_written": result.get("files_written", [])
            })
        except Exception as e:
            st.error("❌ Error running analysis. Check logs in Render.")
            st.exception(e)

st.markdown("---")

# ----------------------------
# Load AI JSON outputs
# ----------------------------
prices_json = safe_load_json(os.path.join(OUTPUT_DIR, "competitor_prices.json"))
scores_json = safe_load_json(os.path.join(OUTPUT_DIR, "feature_scores.json"))
growth_json = safe_load_json(os.path.join(OUTPUT_DIR, "market_growth.json"))
sentiment_json = safe_load_json(os.path.join(OUTPUT_DIR, "sentiment_metrics.json"))

# ==========================================
# 💬 Sentiment Analysis Visualization
# ==========================================
st.subheader("💬 Customer Sentiment Overview")

if not sentiment_json:
    st.info("Run analysis to generate sentiment metrics.")
else:
    pos = int(sentiment_json.get("positive", 60))
    neg = int(sentiment_json.get("negative", 30))
    neu = int(sentiment_json.get("neutral", 10))

    df_sentiment = pd.DataFrame({
        "Sentiment": ["Positive", "Negative", "Neutral"],
        "Percentage": [pos, neg, neu]
    })

    fig1 = px.pie(
        df_sentiment,
        names="Sentiment",
        values="Percentage",
        hole=0.3,
        title=f"Sentiment Breakdown for {product_name}"
    )
    fig1.update_traces(textinfo="percent+label")
    st.plotly_chart(fig1, use_container_width=True)

# ----------------------------
# Competitor Pricing Chart 
# ----------------------------
st.subheader("💰 Competitor Pricing Overview (AI-Fetched)")

if not prices_json:
    st.info("Run analysis to generate AI competitor pricing.")
else:
    df_price = pd.DataFrame(prices_json.get("prices", []))

    if not df_price.empty:
        df_price = df_price.rename(columns={"name": "Competitor", "price": "Price ($)"})
        df_price["Price ($)"] = pd.to_numeric(df_price["Price ($)"], errors="coerce")
        df_price = df_price.dropna(subset=["Price ($)"])

        # ✅ include main product + competitors the user entered
        allowed = set([product_name] + competitors_list)
        df_price = df_price[df_price["Competitor"].isin(allowed)]

    if df_price.empty:
        st.warning("No AI prices found for the entered competitors (or product).")
    else:
        fig_price = px.bar(
            df_price,
            x="Competitor",
            y="Price ($)",
            title=f"Pricing for {product_name} vs Competitors",
            color="Competitor"
        )
        # ✅ remove value labels on bars (hover only)
        fig_price.update_traces(text=None, hovertemplate="$%{y}<extra></extra>")
        st.plotly_chart(fig_price, use_container_width=True)

st.markdown("---")

# ----------------------------
# Feature Radar 
# ----------------------------
st.subheader("⚙️ Feature Comparison Radar")

scores_json = safe_load_json(os.path.join(OUTPUT_DIR, "feature_scores.json"))
rows = (scores_json or {}).get("scores", [])

if not rows:
    st.info("No AI feature scores found. Try running analysis again.")
else:
    df_scores = pd.DataFrame(rows)
    df_scores.columns = [c.strip().lower() for c in df_scores.columns]

    required = {"product", "feature", "score"}
    if not required.issubset(set(df_scores.columns)):
        st.error(f"feature_scores.json missing required fields. Found: {list(df_scores.columns)}")
    else:
        df_scores["score"] = pd.to_numeric(df_scores["score"], errors="coerce")
        df_scores = df_scores.dropna(subset=["score"])

        # ✅ FIX: use the correct variables
        selected_products = [product_name] + competitors_list
        df_scores = df_scores[df_scores["product"].isin(selected_products)]

        # only filter by features if user entered them
        if features_list:
            df_scores = df_scores[df_scores["feature"].isin(features_list)]

        if df_scores.empty:
            st.info("No AI feature scores match your selected competitors/features. Run analysis again.")
        else:
            fig3 = px.line_polar(
                df_scores,
                r="score",
                theta="feature",
                color="product",
                line_close=True,
                title=f"Feature Comparison: {product_name} vs Selected Competitors"
            )
            fig3.update_traces(fill="toself", opacity=0.55)
            st.plotly_chart(fig3, use_container_width=True)

# ----------------------------
# Market Growth Trend 
# ----------------------------
st.subheader("📈 Market Growth Trend (AI-Estimated)")

if not growth_json:
    st.info("Run analysis to generate AI market growth trend.")
else:
    years = growth_json.get("years", [])
    growth = growth_json.get("growth_percent", [])

    if not years or not growth or len(years) != len(growth):
        st.warning("Market growth JSON is incomplete.")
    else:
        df_growth = pd.DataFrame({"Year": [str(y) for y in years], "Market Growth (%)": growth})
        fig_growth = px.line(
            df_growth,
            x="Year",
            y="Market Growth (%)",
            markers=True,
            title=f"Growth Trend in {industry} (Competitor-aware)"
        )
        fig_growth.update_layout(xaxis=dict(type="category"))
        st.plotly_chart(fig_growth, use_container_width=True)

        rationale = growth_json.get("rationale")
        if rationale:
            with st.expander("Why this trend?", expanded=False):
                st.write(rationale)

st.markdown("---")

# ==========================================
# 📘 Full Market Research Reports
# ==========================================
st.subheader("📘 Full Market Research Reports")

if os.path.exists(OUTPUT_DIR):
    md_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".md")]
    if md_files:
        for md_file in sorted(md_files):
            with open(os.path.join(OUTPUT_DIR, md_file), "r", encoding="utf-8") as f:
                content = f.read()
            with st.expander(f"📄 {md_file}", expanded=False):
                st.markdown(content)
    else:
        st.info("No markdown reports found yet. Run analysis first.")

# ==========================================
# 📘 Sidebar — How to Use
# ==========================================
st.sidebar.header("ℹ️ How to Use MarketMind")

st.sidebar.markdown("""
### 📌 Steps to Run the Analysis
1. **Enter your product details**
2. **Enter competitors + features**
3. **Click 'Run Market Research Analysis'**
4. Scroll down to view charts and reports
---

### 💡 Tips
- Try different industries to get different competitor profiles.
- Use reports directly in presentations or decks.

""")

