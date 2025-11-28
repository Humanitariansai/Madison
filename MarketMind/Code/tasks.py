%%writefile tasks.py
from crewai import Task

class MarketResearchTasks:
    # --------------------------------------------
    # 1️⃣ Research Planning
    # --------------------------------------------
    def research_planning_task(self, agent, product_name, industry):
        return Task(
            description=(
                f"Develop a structured research plan for {product_name} in the {industry} industry. "
                "Identify data sources, key market questions, and methods for gathering insights."
            ),
            expected_output=(
                "A detailed research plan covering objectives, data sources, target audiences, "
                "and approaches for market data collection."
            ),
            agent=agent,
        )

    # --------------------------------------------
    # 2️⃣ Competitor Analysis
    # --------------------------------------------
    def competitor_analysis_task(self, agent, product_name, industry):
        return Task(
            description=(
                f"Identify and analyze at least 5 DIRECT real-world competitors for {product_name} "
                f"in the {industry} industry. "
                "Return ONLY real companies and products.\n\n"
                "For each competitor, include:\n"
                "- Product name\n"
                "- Company name\n"
                "- Price in USD\n"
                "- Key strengths\n"
                "- Weaknesses\n\n"
                "The output MUST follow this exact markdown template for each competitor:\n\n"
                "### Competitor: **<Product Name>**\n"
                "- Company: <company name>\n"
                "- Price: $<price>\n"
                "- Strengths: <comma-separated list>\n"
                "- Weaknesses: <comma-separated list>\n\n"
                "Only output the competitors in this structure. Do NOT add extra narrative paragraphs "
                "before or after the list."
            ),
            expected_output=(
                "A structured list of 5 real-world competitors with pricing and strengths/weaknesses, "
                "strictly following the markdown template."
            ),
            agent=agent,
        )

    # --------------------------------------------
    # 3️⃣ Customer Personas & Insights
    # --------------------------------------------
    def customer_persona_task(self, agent, product_name, industry):
        return Task(
            description=(
                f"Develop 3–4 detailed customer personas for {product_name} in the {industry} market. "
                "Include demographics, psychographics, goals, pain points, and buying motivations."
            ),
            expected_output=(
                "A markdown document with detailed persona cards summarizing customer types, "
                "purchase motivations, and behavioral insights."
            ),
            agent=agent,
        )

    # --------------------------------------------
    # 4️⃣ Review Scraping & Sentiment Analysis
    # --------------------------------------------
    def review_analysis_task(self, agent, product_name):
        return Task(
            description=(
                f"Collect and analyze customer reviews for {product_name}. "
                "Perform sentiment analysis and summarize overall satisfaction and pain points. "
                "Clearly state the percentage of positive, negative, and neutral reviews in the form: "
                "'Positive: X%, Negative: Y%, Neutral: Z%'."
            ),
            expected_output=(
                "A sentiment report in markdown format with percentages of positive, negative, and neutral feedback, "
                "plus key customer quotes and insights."
            ),
            agent=agent,
        )

    # --------------------------------------------
    # 5️⃣ Executive Summary Generation
    # --------------------------------------------
    def executive_summary_task(self, agent, product_name, industry):
        return Task(
            description=(
                f"Summarize all research findings for {product_name} in the {industry} market. "
                "Condense key insights from competitor, customer, and sentiment analyses "
                "into an executive summary that can guide strategy."
            ),
            expected_output=(
                "A concise markdown executive summary (2–3 paragraphs) covering the market outlook, "
                "key risks, and high-level recommendations."
            ),
            agent=agent,
        )

    # --------------------------------------------
    # 6️⃣ Visualization / Dashboard Data Prep (optional)
    # --------------------------------------------
    def visualization_task(self, agent, product_name):
        return Task(
            description=(
                f"Generate structured summary data for {product_name}, ready for visualization. "
                "Output should include key metrics from competitor analysis, sentiment, and customer segmentation."
            ),
            expected_output=(
                "A markdown table or JSON-like summary suitable for rendering in visual charts."
            ),
            agent=agent,
        )

    # --------------------------------------------
    # 7️⃣ Final Strategic Synthesis
    # --------------------------------------------
    def synthesis_task(self, agent, product_name, industry, dependencies):
        return Task(
            description=(
                f"Synthesize insights from all prior analyses — research plan, competitor study, customer personas, "
                f"sentiment analysis, and executive summary — to generate a comprehensive market strategy report "
                f"for {product_name} in the {industry} industry."
            ),
            expected_output=(
                "A comprehensive markdown report titled 'Final Market Strategy Report' with sections: "
                "Executive Summary, Market Overview, Competitor Insights, Customer Insights, "
                "Sentiment Analysis, Key Recommendations, and Visual Summary."
            ),
            agent=agent,
            context=dependencies,
        )
