from crewai import Agent
from tools.scrape_pipeline import WebSearchTool, WebScrapeTool, FallbackSearchTool, FileReadTool
from tools.review_scraper import ReviewScraperTool


class MarketResearchAgents:
    def __init__(self):
        self.search_tool = WebSearchTool()
        self.scrape_tool = WebScrapeTool()
        self.fallback_tool = FallbackSearchTool()
        self.file_tool = FileReadTool()
        self.review_tool = ReviewScraperTool()

    def strategy_consultant(self):
        return Agent(
            role="Market Strategy Consultant",
            goal="Build structured research plans and market framing.",
            backstory="Expert strategist who frames the right market questions and research plan.",
            tools=[self.search_tool, self.scrape_tool, self.fallback_tool],
            verbose=False
        )

    def competitor_analyst(self):
        return Agent(
            role="Competitive Intelligence Analyst",
            goal="Fetch REAL competitor pricing and generate structured competitor comparisons.",
            backstory=(
                "Expert in competitive intelligence. "
                "Find real competitor info using web sources and return structured outputs."
            ),
            tools=[self.search_tool, self.scrape_tool, self.fallback_tool],
            allow_delegation=False,
            verbose=False
        )

    def customer_persona_analyst(self):
        return Agent(
            role="Customer Persona Analyst",
            goal="Create realistic personas and buyer insights.",
            backstory="Behavioral marketing expert skilled in segmentation and customer motivations.",
            tools=[self.search_tool, self.scrape_tool],
            verbose=False
        )

    def review_analyst(self):
        return Agent(
            role="Sentiment and Review Analyst",
            goal="Extract sentiment and themes from reviews reliably.",
            backstory="NLP-focused analyst who finds and summarizes review sentiment and themes.",
            tools=[self.review_tool, self.search_tool, self.scrape_tool],
            allow_delegation=False,
            verbose=False
        )

    def lead_strategy_synthesizer(self):
        return Agent(
            role="Lead Strategy Synthesizer",
            goal="Turn all analysis into a clean, actionable strategy report.",
            backstory="Senior strategist who synthesizes research into executive-ready recommendations.",
            tools=[self.file_tool],
            verbose=False
        )

