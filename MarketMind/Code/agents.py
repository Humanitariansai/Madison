from crewai import Agent


class MarketResearchAgents:
    def __init__(self):
        self.scrape_tool = FirecrawlScrapeWebsiteTool()
        self.read_file_tool = FileReadTool()
        self.fallback_search_tool = FallbackSearchTool()

    def strategy_consultant(self):
        return Agent(
            role='Strategy Consultant',
            goal=(
                "Analyze the initial product and market information to formulate a "
                
            ),
            backstory=(
                "A seasoned consultant from McKinsey, you excel at framing complex business problems. "
                
            ),
            tools=[], 
            verbose=True
        )

    def competitor_analyst(self):
        return Agent(
            role='Competitor Analyst',
            goal=(
                "Identify key competitors for {product_name} in the {industry} sector. "
                
            ),
            backstory=(
                "A meticulous analyst with a background in competitive intelligence and market research. You are an expert at "
                
            ),
            tools=[WebSearchTool(), self.scrape_tool, self.fallback_search_tool],
            verbose=True
        )

    def customer_persona_analyst(self):
        return Agent(
            role='Customer Persona Analyst',
            goal=(
                
                "Provide bold, opinionated insights about customer behavior and market opportunities."
            ),
            backstory=(
                "An empathetic market researcher with a knack for storytelling and strong opinions about customer behavior. "
                
            ),
            tools=[WebSearchTool(), self.scrape_tool, self.fallback_search_tool],
            verbose=True
        )

    

    def lead_strategy_synthesizer(self):
        return Agent(
            role='Lead Strategy Synthesizer',
            goal=(
                "Consolidate all research findings into an extremely detailed, comprehensive market research document. "
                
            ),
            backstory=(
                "A brilliant ex-CMO and management consultant known for bold, contrarian market insights. "
                
            ),
            allow_delegation=False, 
            tools=[self.read_file_tool],
            verbose=True
        )
