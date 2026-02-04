# agents.py
from crewai import Agent

# Safe imports: your app should not crash if a tool import fails.
try:
    from tools.scrape_pipeline import WebSearchTool, WebScrapeTool, FallbackSearchTool, FileReadTool
except Exception:
    WebSearchTool = WebScrapeTool = FallbackSearchTool = FileReadTool = None


class MarketResearchAgents:
    def __init__(self):
        # Tools are optional. If imports fail, we fallback to no-tool agents (still runs).
        self.search_tool = WebSearchTool() if WebSearchTool else None
        self.scrape_tool = WebScrapeTool() if WebScrapeTool else None
        self.fallback_tool = FallbackSearchTool() if FallbackSearchTool else None
        self.file_tool = FileReadTool() if FileReadTool else None

    def _tools(self, names):
        tool_map = {
            "search": self.search_tool,
            "scrape": self.scrape_tool,
            "fallback": self.fallback_tool,
            "file": self.file_tool,
        }
        return [tool_map[n] for n in names if tool_map.get(n) is not None]

    def strategy_consultant(self):
        return Agent(
            role="Market Strategy Consultant",
            goal="Build structured research plans and market framing without hallucinating facts.",
            backstory="Expert strategist who frames the right market questions and research plan.",
            tools=self._tools(["search", "scrape", "fallback"]),
            allow_delegation=False,
            verbose=False,
        )

    def competitor_analyst(self):
        return Agent(
            role="Competitive Intelligence Analyst",
            goal=(
                "Find and summarize competitor info cautiously. Return structured JSON. "
                "If you cannot verify a data point, set it null and explain limitations."
            ),
            backstory="Expert in competitive intelligence. Prefers evidence and transparency over guessing.",
            tools=self._tools(["search", "scrape", "fallback"]),
            allow_delegation=False,
            verbose=False,
        )

    def customer_persona_analyst(self):
        return Agent(
            role="Customer Persona Analyst",
            goal=(
                "Create realistic personas and buyer insights. "
                "Explain how personas were derived and how users can customize."
            ),
            backstory="Behavioral marketing expert skilled in segmentation and customer motivations.",
            tools=self._tools(["search", "scrape"]),
            allow_delegation=False,
            verbose=False,
        )

    def review_analyst(self):
        # IMPORTANT: No ReviewScraperTool. This fixes your ImportError.
        return Agent(
            role="Sentiment and Review Analyst",
            goal=(
                "Summarize sentiment ONLY from provided sources. "
                "Never fabricate quotes. If sources are missing, set quotes empty and mark unverified."
            ),
            backstory="Trust-first analyst. Returns 'insufficient data' rather than hallucinating.",
            tools=self._tools(["search", "scrape", "fallback"]),
            allow_delegation=False,
            verbose=False,
        )

    def lead_strategy_synthesizer(self):
        return Agent(
            role="Lead Strategy Synthesizer",
            goal=(
                "Turn all analysis into a clean, actionable strategy report. "
                "Do not invent budgets or implementation timelines unless requested."
            ),
            backstory="Senior strategist who synthesizes research into executive-ready recommendations.",
            tools=self._tools(["file"]),
            allow_delegation=False,
            verbose=False,
        )



