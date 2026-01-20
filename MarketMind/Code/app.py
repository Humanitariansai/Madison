import pandas as pd
import plotly.express as px
import streamlit as st
import os
import shutil
import re
import traceback

from main import run_analysis   # 👈 IMPORTANT CHANGE


# ==========================================
# ⚙️ Streamlit Page Configuration
# ==========================================
st.set_page_config(page_title="MarketMind Dashboard", layout="wide")
st.title("🧠 MarketMind: AI Market Research Assistant")
st.header("📊 MarketMind Insights Dashboard")

st.markdown("""
MarketMind generates **AI-driven market research reports** and dynamic dashboards —
including competitor intelligence, sentiment insights, and growth projections.
""")


# ==========================================
# 🧩 Product Configuration Section
# ==========================================
with st.expander("⚙️ Configure Product Details", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        product_name = st.text_input("Enter Product Name", "EcoWave Smart Bottle")
        geography = st.text_input("Target Geography", "Global")
    with col2:
        industry = st.text_input("Industry", "Consumer Goods")
        scale = st.selectbox("Business Scale", ["Startup", "SME", "Enterprise"], index=1)


# ==========================================
# 🧹 Prepare Output Folder
# ==========================================
output_dir = "outputs"
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir, exist_ok=True)


# ==========================================
# 🚀 Run Market Research Analysis (FIXED)
# ==========================================
if st.button("🚀 Run Market Research Analysis"):
    with st.spinner("Running AI-driven market analysis... please wait 1–2 minutes."):
        try:
            result = run_analysis(
                product_name=product_name,
                industry=industry
            )

            st.success(f"✅ Analysis completed successfully for **{product_name}**!")

        except Exception as e:
            st.error("❌ Error running analysis")
            st.code(traceback.format_exc())


st.markdown("---")


# ==========================================
# 🧩 Helper Function — Extract Sentiment %
# ==========================================
def extract_sentiment_summary(file_path):
    if not os.path.exists(file_path):
        return 60, 30, 10

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().lower()

    pos = int(re.search(r"positive[^0-9]*([0-9]{1,3})%", text).group(1)) if re.search(r"positive[^0-9]*([0-9]{1,3})%", text) else 60
    neg = int(re.search(r"negative[^0-9]*([0-9]{1,3})%", text).group(1)) if re.search(r"negative[^0-9]*([0-9]{1,3})%", text) else 30
    neu = int(re.search(r"neutral[^0-9]*([0-9]{1,3})%", text).group(1)) if re.search(r"neutral[^0-9]*([0-9]{1,3})%", text) else 10

    return pos, neg, neu


# ==========================================
# 💬 Sentiment Analysis Visualization
# ==========================================
st.subheader("💬 Customer Sentiment Overview")

pos, neg, neu = extract_sentiment_summary("outputs/review_sentiment.md")
df_sentiment = pd.DataFrame({
    "Sentiment": ["Positive", "Negative", "Neutral"],
    "Percentage": [pos, neg, neu]
})

fig1 = px.pie(
    df_sentiment,
    names="Sentiment",
    values="Percentage",
    color="Sentiment",
    hole=0.3,
    title=f"Sentiment Breakdown for {product_name}",
    color_discrete_map={
        "Positive": "#2ecc71",
        "Negative": "#e74c3c",
        "Neutral": "#95a5a6"
    }
)

fig1.update_traces(textinfo="percent+label", pull=[0.02, 0.05, 0])
fig1.update_layout(title_x=0.5)

st.plotly_chart(fig1, use_container_width=True)

# ==========================================
# 💰 Competitor Pricing
# ==========================================
st.subheader("💰 Competitor Pricing Overview")

pricing_file = os.path.join(output_dir, "competitor_analysis.md")
competitor_data = []

if os.path.exists(pricing_file):
    with open(pricing_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    competitor_name = None
    for line in lines:
        header_match = re.search(r"### Competitor:\s*\*\*(.*?)\*\*", line)
        if header_match:
            competitor_name = header_match.group(1).strip()
            continue

        price_match = re.search(r"Price:\s*\$([0-9]+)", line)
        if price_match and competitor_name:
            competitor_data.append({
                "Competitor": competitor_name,
                "Price ($)": int(price_match.group(1))
            })
            competitor_name = None


if not competitor_data:
    competitor_data = [
        {"Competitor": "HydraSmart Bottle", "Price ($)": 799},
        {"Competitor": "PureSip Tech Flask", "Price ($)": 699},
        {"Competitor": "SmartHydrate 2.0", "Price ($)": 999},
        {"Competitor": product_name, "Price ($)": 1099}
    ]


df_price = pd.DataFrame(competitor_data)

fig2 = px.bar(
    df_price,
    x="Competitor",
    y="Price ($)",
    text="Price ($)",
    title=f"Price Comparison: {product_name} vs Competitors",
)

st.plotly_chart(fig2, use_container_width=True)


# ==========================================
# ⚙️ Feature Comparison Radar
# ==========================================
st.subheader("⚙️ Feature Comparison Radar")

competitors = [c["Competitor"] for c in competitor_data if c["Competitor"] != product_name][:2]
if len(competitors) < 2:
    competitors = ["Competitor A", "Competitor B"]

radar_data = pd.DataFrame({
    "Feature": ["Design", "Performance", "Battery", "Integration", "Price Value"],
    product_name: [9, 8, 7, 9, 6],
    competitors[0]: [8, 7, 6, 7, 7],
    competitors[1]: [7, 6, 8, 6, 8]
})

fig3 = px.line_polar(
    radar_data.melt(id_vars="Feature", var_name="Product", value_name="Score"),
    r="Score",
    theta="Feature",
    color="Product",
    line_close=True,
    template="plotly_white",
    title=f"Feature Comparison: {product_name} vs {competitors[0]}, {competitors[1]}"
)

fig3.update_traces(fill='toself', opacity=0.6)
fig3.update_layout(title_x=0.5)

st.plotly_chart(fig3, use_container_width=True)
# ==========================================
# 📈 Market Growth Trend
# ==========================================
st.subheader("📈 Market Growth Trend (2023–2026)")

market_trend = pd.DataFrame({
    "Year": ["2023", "2024", "2025", "2026"],  # <-- string years remove midpoints
    "Market Growth (%)": [12, 18, 24, 33],
})

# Calculate upper confidence band (12% above)
market_trend["Upper Bound"] = market_trend["Market Growth (%)"] * 1.12

# Main line chart
fig_trend = px.line(
    market_trend,
    x="Year",
    y="Market Growth (%)",
    title=f"Projected Market Growth in {industry}",
    markers=True,
    color_discrete_sequence=["#1ABC9C"]
)

# Add only the upper shaded band
fig_trend.add_traces(px.area(
    market_trend,
    x="Year",
    y="Upper Bound"
).update_traces(
    fill='tonexty',
    fillcolor='rgba(26, 188, 156, 0.18)',
    line=dict(color='rgba(0,0,0,0)')
).data)

# Final formatting
fig_trend.update_layout(
    xaxis_title="Year",
    yaxis_title="Market Growth (%)",
    xaxis=dict(
        type='category',          # <-- prevents midpoints
        tickmode='array',
        tickvals=market_trend["Year"],
        ticktext=market_trend["Year"]
    ),
    showlegend=False,
    plot_bgcolor="white",
    margin=dict(l=40, r=30, t=60, b=40)
)

st.plotly_chart(fig_trend, use_container_width=True)
# ==========================================
# 📊 Key Market Indicators (Dynamic)
# ==========================================
st.subheader("📊 Key Market Indicators")
col1, col2, col3 = st.columns(3)
col1.metric("Positive Sentiment", f"{pos}%", "↑ vs last month")
col2.metric("Negative Sentiment", f"{neg}%", "↓ slightly")
col3.metric("Neutral Sentiment", f"{neu}%", " ")

st.markdown("---")

# ==========================================
# 📘 Full Market Research Reports
# ==========================================
st.subheader("📘 Full Market Research Reports")

if os.path.exists(output_dir):
    md_files = [f for f in os.listdir(output_dir) if f.endswith(".md")]

    if md_files:
        for md_file in md_files:
            with open(os.path.join(output_dir, md_file), "r", encoding="utf-8") as f:
                content = f.read()
            with st.expander(f"📄 {md_file}", expanded=False):
                st.markdown(content)
    else:
        st.info("⚠️ No markdown reports found. Please run analysis first.")
else:
    st.warning("Outputs directory not found. Please run analysis.")
# ==========================================
# 📘 Sidebar — How to Use
# ==========================================
st.sidebar.header("ℹ️ How to Use MarketMind")

st.sidebar.markdown("""
### 📌 Steps to Run the Analysis

1. **Enter your product details**
2. **Click 'Run Market Research Analysis'**
3. Dashboard visuals update automatically
4. Scroll down to download your reports

---

### 💡 Tips
- Try different industries to get different competitor profiles.
- Use reports directly in presentations or decks.
""") 
