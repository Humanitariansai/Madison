# 🧠 MarketMind  
**AI-Powered Market Research & Strategy Assistant**

🔗 **Live App:** https://marketmind-17.onrender.com/

MarketMind is an AI-driven market research platform that automates **competitor pricing, sentiment insights, feature scoring (radar), market growth trends, and executive strategy synthesis** using a multi-agent architecture (CrewAI) powered by large language models.

Built for **founders, product managers, and strategy teams** who want fast, structured market intelligence without manual research overhead.

---

## 🚀 What MarketMind Does

MarketMind runs a multi-stage AI pipeline to generate:

- 💰 **Competitor + Product pricing (AI estimated)** saved as JSON
- 💬 **Customer sentiment (AI summary)** saved as JSON + Markdown
- ⚙️ **Feature scoring for product vs competitors (AI scores 0–10)** for radar chart
- 📈 **Market growth projection (AI estimated)** saved as JSON
- 🧾 **Executive-ready strategy report** (Markdown)

All outputs are written to `./outputs/` and visualized in the Streamlit dashboard.

---

## ✅ What’s New (Latest Changes)

### 1) Custom comparison inputs (user-driven)
Instead of hardcoded competitors/features, the app now lets users **enter their own**:

- **Competitors** (comma-separated)
- **Features to compare** (comma-separated)

These inputs are passed directly into `run_analysis()` so the AI generates pricing + feature scores specifically for the user’s selection.

### 2) Stable outputs handling (fix for Streamlit reruns)
Streamlit reruns the script often. The app now **does NOT delete outputs on every rerun**.

- `outputs/` is only cleared **when the user clicks** **Run Market Research Analysis**
- This prevents missing JSON files and fixes radar/pricing charts failing after UI updates

### 3) Feature radar now reads AI scores from JSON
The radar chart is now driven by:

- `outputs/feature_scores.json`

The app loads this JSON, validates required fields (`product`, `feature`, `score`), and renders a radar chart using Plotly.

### 4) Pricing chart uses AI JSON output (and hover-only values)
Competitor pricing is now driven by:

- `outputs/competitor_prices.json`

The chart:
- includes **product + competitors**
- removes bar labels (values shown on hover)

---

## 🧩 Key Features

- **Multi-Agent Architecture (CrewAI)**
  - Strategy Consultant
  - Competitor Analyst
  - Customer Persona Analyst
  - Review/Sentiment Analyst
  - Strategy Synthesizer

- **User-Entered Comparisons**
  - Add your own competitors + features
  - Charts update based on those inputs

- **Interactive Dashboard**
  - Sentiment pie chart (from JSON)
  - Pricing bar chart (from JSON)
  - Feature radar (from JSON)
  - Market growth line chart (from JSON)

- **Exportable Research**
  - Generates structured `.md` reports suitable for decks and docs

---

## 🏗️ Architecture Overview

Streamlit UI (app.py)
|
v
run_analysis() <-- main.py
|
v
CrewAI Orchestration
├─ Agents (agents.py)
├─ Tasks (tasks.py) -> outputs strict JSON artifacts
└─ Tools (feature comparison, scraping, sentiment, etc.)
|
v
Artifacts written to ./outputs/
├─ competitor_prices.json
├─ feature_scores.json
├─ market_growth.json
├─ sentiment_metrics.json
└─ Markdown reports (*.md)

---

## 📁 Project Structure

MarketMind/
│
├── app.py # Streamlit dashboard (UI)
├── main.py # Analysis runner & orchestration entrypoint
├── agents.py # CrewAI agent definitions
├── tasks.py # Task definitions for agents (STRICT JSON outputs)
├── models.py # Data models / schemas
│
├── tools/
│ ├── scrape_pipeline.py # Web search, scraping & content extraction
│ └── review_scraper.py # Review scraping & sentiment analysis (NLTK VADER)
│
├── outputs/ # Generated artifacts (JSON + Markdown)
│ ├── competitor_prices.json
│ ├── feature_scores.json
│ ├── market_growth.json
│ ├── sentiment_metrics.json
│ ├── review_sentiment.md
│ ├── feature_comparison.md
│ └── final_market_strategy_report.md
│
├── requirements.txt # Python dependencies
└── README.md

---

## 📦 Tech Stack

### Frontend / UI
- Streamlit
- Plotly
- Pandas

### AI & Agents
- OpenAI API
- CrewAI

### Web Scraping & NLP (if enabled in tools)
- BeautifulSoup
- Readability-lxml
- Trafilatura
- LangDetect
- NLTK (VADER sentiment)

### Deployment
- Render

---

## ⚙️ Environment Variables

Set the following variables in **Render → Environment Variables** (or locally via `.env`):

```env
OPENAI_API_KEY=your_openai_api_key
SERPER_API_KEY=your_serper_api_key

