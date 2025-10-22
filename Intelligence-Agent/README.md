# 🤖 Madison Framework Intelligence Agent

**Open-Source AI Marketing Intelligence System**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Production-Ready](https://img.shields.io/badge/Status-Production--Ready-brightgreen.svg)]()
[![Built with: n8n, OpenAI, Python](https://img.shields.io/badge/Built%20with-n8n%2C%20OpenAI%2C%20Python-blueviolet.svg)]()
[![Nonprofit: Humanitarians AI](https://img.shields.io/badge/Organization-Humanitarians%20AI-red.svg)](https://humanitarians.ai)

---

## 💡 Overview

The **Madison Framework Intelligence Agent** is the foundational layer of the Madison five-layer agent architecture, an ambitious open-source initiative by **Humanitarians AI** to democratize AI-powered marketing intelligence.

This system is a production-ready infrastructure that processes **870+ articles daily** across multiple brands, providing real-time sentiment analysis, competitive benchmarking, and actionable marketing insights. It achieves high efficiency with a **90% deduplication rate** and sub-3-minute processing latency.

### Key Capabilities

* **Multi-Source Data Gathering:** Aggregates market data from RSS feeds, Google News API, and social media (e.g., Reddit).
* **AI-Powered Analysis:** Utilizes OpenAI's language models (e.g., GPT-4o-mini) for real-time sentiment analysis and trend detection.
* **Competitive Benchmarking:** Enables comprehensive multi-brand analysis, tracking **Share of Voice** and **Sentiment Drift**.
* **Risk Monitoring:** Specialised feeds for detecting regulatory compliance risks (GDPR, DMA, FTC, etc.).
* **Open-Source & Accessible:** Built on a transparent, reproducible, and accessible stack to empower organizations of all sizes.

---

## ⚙️ System Architecture

The Intelligence Agent operates as a resilient, modular pipeline orchestrated primarily by **n8n**.

### Core Technical Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Orchestration** | **n8n** (40+ nodes) | Workflow automation and scheduling. |
| **AI Processing** | **OpenAI GPT-4o-mini** | Core sentiment analysis and content scoring. |
| **Data Sources** | RSS, Google News API, Reddit API | Content aggregation and market data ingestion. |
| **Storage** | Google Sheets | Structured, low-latency data storage and historical logging. |
| **Visualization** | Python, Plotly, Pandas | Interactive dashboards and analytical reporting. |
| **Deduplication** | MD5 Hashing, Levenshtein | Efficient content filtering to remove duplicates (90% reduction). |

### Data Pipeline Visualization

The system flows data through four main stages:

1.  **Ingestion:** Data is pulled from various sources (RSS/API/Web).
2.  **Orchestration:** n8n manages rate limiting, error handling, and data transformation.
3.  **Analysis:** The data is sent to OpenAI for sentiment scoring and tagging.
4.  **Storage & Visualization:** Results are stored in Google Sheets, then fed into Plotly for real-time dashboards.

---

## 🚀 Getting Started

To replicate and run the Madison Intelligence Agent, you will need the following prerequisites and follow the setup steps.

### Prerequisites

1.  **n8n Instance:** A self-hosted or cloud n8n instance (ideally with persistent storage).
2.  **OpenAI API Key:** For sentiment and AI-driven analysis.
3.  **Google Account:** Access to Google Sheets for data storage.
4.  **Python Environment:** For running the visualization scripts.

### Setup and Deployment

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/humanitariansai/madison](https://github.com/humanitariansai/madison)
    cd madison-intelligence-agent
    ```

2.  **Import the n8n Workflow**
    * Navigate to your n8n instance.
    * Go to **Workflows** and select **Import from JSON**.
    * Upload the primary workflow file: `workflows/n8n-export.json`.

3.  **Configure Credentials**
    * In the imported n8n workflow, update the credentials for the following nodes:
        * `OpenAI` (API Key)
        * `Google Sheets` (Authentication)
    * Update the `Multi-Brand Config` code node with the specific brands, RSS feeds, and keywords you wish to track.

4.  **Run the Workflow**
    * Execute the n8n workflow. It is designed to run on a scheduled trigger (e.g., every 30 minutes) to ensure continuous monitoring.

### Data Storage Structure

The system uses a Google Sheet with five tabs for structured data storage:

* `RawLinks`: All collected articles before analysis.
* `ProcessedLinks`: Articles with sentiment scores and brand analysis.
* `Alerts`: High-priority anomaly detection triggers.
* `Config`: Multi-brand configuration and keywords.
* `Metrics`: Historical performance data and operational metrics.

---

## 📊 Analytics and Reporting

The agent is designed to feed into advanced visualization tools for data interpretation.

### Key Metrics Tracked

| Metric | Value (Sample) | Description |
| :--- | :--- | :--- |
| **Daily Volume** | 870+ Articles | Total content processed per 24 hours. |
| **Latency** | < 3 minutes | Time from article detection to final score in the dashboard. |
| **Deduplication** | 90% | Efficiency of the filtering algorithm. |
| **Sentiment Score** | Weighted average sentiment from 0 (Negative) to 1 (Positive). |
| **Z-Score Anomaly** | $Z_{score} = \frac{X - \mu}{\sigma}$ | Standardized score for detecting significant shifts in sentiment. |

### Advanced Features

* **Knowledge Graph Construction:** Tracks entity relationships, brand co-mentions, and competitive positioning.
* **Regulatory Monitoring:** Dedicated feeds and AI parsing to flag content related to GDPR, DMA, FTC, and other compliance risks.
* **Cross-Agent Integration:** Provides data directly to the Madison **Content Agents** for sentiment-driven content generation and the **Performance Agents** for KPI tracking.

---

## 🤝 Contribution

The Madison Framework is an open-source project driven by a community-focused 501(c)(3) nonprofit, **Humanitarians AI**. Your contributions are vital to advancing our mission of accessible AI for social good.

---

### How to Contribute

1.  **Fork** the repository on GitHub.
2.  **Create** your feature branch (`git checkout -b feature/AmazingFeature`).
3.  **Open** a Pull Request.

We are looking for contributions in:

* Improving the Python visualization dashboards.
* Implementing semantic deduplication.
* Expanding data source integrations.

---

## ⚖️ License

This project is licensed under the **MIT License**. See the project's [LICENSE file](LICENSE) for details.

---

## ✉️ Contact

For questions, support, or partnership inquiries:

* **Organization:** Humanitarians AI Incorporated
* **Website:** [https://humanitarians.ai](https://humanitarians.ai)
* **GitHub:** [https://github.com/humanitariansai/madison](https://github.com/humanitariansai/madison)

***AI for Good™***