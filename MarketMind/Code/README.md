# 🧠 MarketMind  
**AI-Powered Market Research & Strategy Assistant**

🔗 **Live App:** https://marketmind-17.onrender.com/

MarketMind is an AI-driven market research platform that automates **competitor analysis, customer sentiment insights, feature comparison, and executive strategy synthesis** using a multi-agent architecture powered by large language models.

It is built for **founders, product managers, and strategy teams** who want fast, structured market intelligence without manual research overhead.

---

## 🚀 What MarketMind Does

MarketMind runs a **multi-stage AI research pipeline** to generate:

- 📊 Competitor intelligence (pricing, positioning, differentiation)
- 💬 Customer sentiment analysis (VADER-based NLP)
- ⚙️ Feature comparison & benchmarking
- 📈 Market growth projections
- 🧾 Executive-ready strategy reports (Markdown)

All outputs are generated dynamically and visualized in an interactive dashboard.

---

## 🧩 Key Features

- **Multi-Agent Architecture (CrewAI)**
  - Strategy Consultant
  - Competitor Analyst
  - Customer Persona Analyst
  - Review Sentiment Analyst
  - Strategy Synthesizer

- **Automated Web Intelligence**
  - Web search + scraping
  - Content extraction (Readability + Trafilatura)
  - Language detection with fallback logic

- **Interactive Dashboard**
  - Sentiment pie charts
  - Competitor pricing bar charts
  - Feature comparison radar
  - Market growth trendlines

- **Exportable Research**
  - Generates structured `.md` reports for presentations & decks

---

## 🏗️ Architecture Overview

.
Streamlit UI (app.py)
|
v
run_analysis() ←── main.py
|
v
CrewAI Orchestration
├─ Agents (agents.py)
├─ Tasks (tasks.py)
├─ Web Scraping (scrape_pipeline.py)
└─ Sentiment NLP (review_scraper.py)
|
v
Markdown Reports → ./outputs/
---


## 📁 Project Structure
MarketMind/
│
├── app.py # Streamlit dashboard (UI)
├── main.py # Analysis runner & orchestration entrypoint
├── agents.py # CrewAI agent definitions
├── tasks.py # Task definitions for agents
├── models.py # Data models / schemas
│
├── tools/
│ ├── scrape_pipeline.py # Web search, scraping & content extraction
│ └── review_scraper.py # Review scraping & sentiment analysis (NLTK VADER)
│
├── outputs/ # Generated research reports (.md)
│ ├── research_plan.md
│ ├── competitor_analysis.md
│ ├── customer_analysis.md
│ ├── review_sentiment.md
│ ├── feature_comparison.md
│ ├── executive_summary.md
│ └── final_market_strategy_report.md
│
├── requirements.txt # Python dependencies
├── runtime.txt # Python version pin (3.11)
└── README.md

## 📦 Tech Stack

### Frontend / UI
- Streamlit
- Plotly
- Pandas
- Matplotlib

### AI & Agents
- OpenAI API
- CrewAI

### Web Scraping & NLP
- BeautifulSoup
- Readability-lxml
- Trafilatura
- LangDetect
- NLTK (VADER sentiment)

### Deployment
- Render
- Python 3.11

---

## ⚙️ Environment Variables

Set the following variables in **Render → Environment Variables** (or locally via `.env`):

```env
OPENAI_API_KEY=your_openai_api_key
SERPER_API_KEY=your_serper_api_key

