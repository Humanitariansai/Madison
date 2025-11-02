from crewai import Task

class MarketResearchTasks:
    def research_planning_task(self, agent, product_name, industry):
        return Task(
            description=(
                f"Develop a detailed research plan for understanding the {industry} market "
                f"with specific focus on the product '{product_name}'. "
                "Include objectives, key questions, data sources, and methodologies."
            ),
            expected_output=(
                "A well-structured research plan in Markdown format that outlines "
                "objectives, data sources, analysis methods, and expected insights."
            ),
            agent=agent,
            output_file="outputs/research_plan.md"
        )

    def competitor_analysis_task(self, agent, product_name, industry):
        return Task(
            description=(
                f"Conduct a competitor analysis for the product '{product_name}' "
                f"within the {industry} industry. Identify at least 5 competitors "
                "and compare their strengths, weaknesses, and market strategies."
            ),
            expected_output=(
                "A competitor analysis report in Markdown format including a table "
                "comparing each competitor’s key differentiators."
            ),
            agent=agent,
            output_file="outputs/competitor_analysis.md"
        )

    def customer_analysis_task(self, agent, product_name, industry):
        return Task(
            description=(
                f"Develop detailed customer personas for '{product_name}' within the {industry} industry. "
                "Include demographic, psychographic, and behavioral data. Create 3–4 distinct personas."
            ),
            expected_output=(
                "A detailed Markdown report containing customer personas with narratives, "
                "motivations, and buying behaviors."
            ),
            agent=agent,
            output_file="outputs/customer_analysis.md"
        )

    def synthesis_task(self, agent, product_name, industry, dependencies):
        return Task(
            description=(
                f"Synthesize insights from competitor, customer, and research reports "
                f"to generate a single cohesive market strategy report for '{product_name}' in the {industry} industry. "
                "Include strategic recommendations, trends, and opportunities."
            ),
            expected_output=(
                "A comprehensive market strategy report in Markdown format, integrating insights "
                "from all previous tasks and structured for presentation to executives."
            ),
            agent=agent,
            context=dependencies,
            output_file="outputs/final_market_strategy_report.md"
        )

