# agents.py
from crewai import Agent
from tools.scrape_pipeline import WebSearchTool, WebScrapeTool, FallbackSearchTool, FileReadTool
from tools.review_scraper import ReviewScraperTool

class MarketResearchAgents:
    def __init__(self):
        # Initialize tools
        self.search_tool = WebSearchTool()
        self.scrape_tool = WebScrapeTool()
        self.fallback_tool = FallbackSearchTool()
        self.file_tool = FileReadTool()
        self.review_tool = ReviewScraperTool()

    # --------------------------------------------------
    # 1️⃣ Market Strategy Consultant
    # --------------------------------------------------
    def strategy_consultant(self):
        return Agent(
            role="Market Strategy Consultant",
            goal="Develop a comprehensive research plan for understanding the market landscape.",
            backstory="An expert strategist who frames market research questions and guides market exploration.",
            tools=[self.search_tool, self.scrape_tool, self.fallback_tool],
            verbose=False
        )

    # --------------------------------------------------
    # 2️⃣ Competitor Analyst (Real competitor extraction)
    # --------------------------------------------------
    def competitor_analyst(self):
        return Agent(
            role="Competitor Analyst",
            goal="Find REAL competitors, REAL prices, and REAL product differentiators.",
            backstory=(
                "Expert in competitive intelligence. Always extract real competitor products "
                "and pricing from search results or industry data. "
                "Never invent fake competitors unless absolutely necessary."
            ),
            tools=[self.search_tool, self.scrape_tool, self.fallback_tool],
            allow_delegation=False,
            verbose=False
        )

    # --------------------------------------------------
    # 3️⃣ Customer Persona Analyst
    # --------------------------------------------------
    def customer_persona_analyst(self):
        return Agent(
            role="Customer Persona Analyst",
            goal="Create data-backed customer personas for the target market.",
            backstory="A behavioral marketing expert skilled in demographics, psychographics, and buyer motivations.",
            tools=[self.search_tool, self.scrape_tool],
            verbose=False
        )

    # --------------------------------------------------
    # 4️⃣ Review / Sentiment Analyst
    # --------------------------------------------------
    def review_analyst(self):
        return Agent(
            role="Sentiment and Review Analyst",
            goal="Analyze real customer reviews to extract sentiment, themes, praises, and complaints.",
            backstory="Expert in NLP, sentiment extraction, and opinion mining.",
            tools=[self.review_tool, self.search_tool, self.scrape_tool],
            allow_delegation=False,
            verbose=False
        )

    # --------------------------------------------------
    # 5️⃣ Lead Strategy Synthesizer
    # --------------------------------------------------
    def lead_strategy_synthesizer(self):
        return Agent(
            role="Lead Strategy Synthesizer",
            goal="Combine all research outputs into a unified strategic market report.",
            backstory="A senior strategist who synthesizes multiple research streams into actionable recommendations.",
            tools=[self.file_tool],
            verbose=False
        )
