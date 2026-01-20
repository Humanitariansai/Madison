🧠 MarketMind

AI-Powered Market Research & Strategy Assistant

🔗 Live App: https://marketmind-17.onrender.com/

MarketMind is an AI-driven market research platform that automates competitor analysis, customer sentiment insights, feature comparison, and executive strategy synthesis using multi-agent orchestration and large language models.

It is designed for founders, product managers, and strategy teams who want fast, structured market intelligence without manual research overhead.


🚀 What MarketMind Does

MarketMind runs a multi-stage AI research pipeline to generate:

📊 Competitor intelligence (pricing, positioning, differentiation)

💬 Customer sentiment analysis (VADER-based NLP)

⚙️ Feature comparison & benchmarking

📈 Market growth projections

🧾 Executive-ready strategy reports (Markdown)

All outputs are generated dynamically and visualized in an interactive Streamlit dashboard.


🧩 Key Features

Multi-Agent Architecture (CrewAI)

Strategy Consultant

Competitor Analyst

Customer Persona Analyst

Review Sentiment Analyst

Strategy Synthesizer

Automated Web Intelligence

Web search + scraping

Content extraction (readability + trafilatura)

Language detection & fallback logic

Interactive Dashboard

Sentiment pie charts

Competitor pricing bar charts

Feature comparison radar

Market growth trendlines

Exportable Research

Generates structured .md reports for presentations & decks


🏗️ Architecture Overview
Streamlit UI (app.py)
        |
        v
run_analysis()  ←── main.py
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


📦 Tech Stack
Frontend / UI

Streamlit

Plotly

Pandas

Matplotlib

AI & Agents

OpenAI API

CrewAI

Web Scraping & NLP

BeautifulSoup

Readability-lxml

Trafilatura

LangDetect

NLTK (VADER sentiment)

Deployment

Render (Python Web Service)

Python 3.11


⚙️ Environment Variables

Set the following in Render → Environment Variables (or locally via .env):

OPENAI_API_KEY=your_openai_key
SERPER_API_KEY=your_serper_key



⚠️ Never commit API keys to GitHub.

🛠️ Local Setup
git clone https://github.com/<your-username>/MarketMind.git
cd MarketMind

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py


📁 Project Structure
.
├── app.py                  # Streamlit UI
├── main.py                 # Analysis runner
├── agents.py               # CrewAI agents
├── tasks.py                # Research tasks
├── models.py               # Data models
├── tools/
│   ├── scrape_pipeline.py  # Web scraping & extraction
│   └── review_scraper.py   # Sentiment analysis
├── outputs/                # Generated reports
├── requirements.txt
└── runtime.txt


📄 Generated Reports

After each run, MarketMind produces:

research_plan.md

competitor_analysis.md

customer_analysis.md

review_sentiment.md

feature_comparison.md

executive_summary.md

final_market_strategy_report.md

These are viewable directly in the app UI.


🔒 Security Notes

API keys are server-side only

No keys are exposed to the browser

Scraping includes fallback logic & safe parsing

Designed to run within free-tier cloud limits


🧠 Why MarketMind?

Traditional market research is:

Slow

Manual

Expensive

MarketMind turns it into a repeatable, automated AI workflow that produces strategy-grade insights in minutes.


📌 Roadmap (Planned)

Async/background execution for long analyses

PDF / PPT export

Persistent project history

Frontend + API split for scale

n8n / workflow automation integration
