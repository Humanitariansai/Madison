%%writefile app.py
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st
import os
import subprocess
import shutil
import re

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
# 🚀 Run Market Research Analysis
# ==========================================
if st.button("🚀 Run Market Research Analysis"):
    with st.spinner("Running AI-driven market analysis... please wait 1–2 minutes."):

        os.environ["PRODUCT_NAME"] = product_name
        os.environ["INDUSTRY"] = industry
        os.environ["GEOGRAPHY"] = geography
        os.environ["SCALE"] = scale

        process = subprocess.run(
            ["python3", "main.py"],
            text=True,
            capture_output=True
        )

        if process.returncode != 0:
            st.error("❌ Error running analysis. Check logs in main.py.")
        else:
            st.success(f"✅ Analysis completed successfully for **{product_name}**!")

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
# 💰 Competitor Pricing (Dynamic if available)
# ==========================================
st.subheader("💰 Competitor Pricing Overview")

pricing_file = os.path.join(output_dir, "competitor_analysis.md")
competitor_data = []

# ---- Extract competitors from markdown if available ----
if os.path.exists(pricing_file):
    with open(pricing_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    competitor_name = None
    price_value = None

    for line in lines:

        # Detect competitor header
        header_match = re.search(r"### Competitor:\s*\*\*(.*?)\*\*", line)
        if header_match:
            competitor_name = header_match.group(1).strip()
            price_value = None  # reset
            continue

        # Detect price line
        price_match = re.search(r"Price:\s*\$([0-9]+)", line)
        if price_match and competitor_name:
            price_value = int(price_match.group(1))
            competitor_data.append(
                {"Competitor": competitor_name, "Price ($)": price_value}
            )
            competitor_name = None  # reset for next competitor

# ---- Use fallback sample if nothing extracted ----
if not competitor_data:
    competitor_data = [
        {"Competitor": "HydraSmart Bottle", "Price ($)": 799},
        {"Competitor": "PureSip Tech Flask", "Price ($)": 699},
        {"Competitor": "SmartHydrate 2.0", "Price ($)": 999},
        {"Competitor": product_name, "Price ($)": 1099}
    ]
