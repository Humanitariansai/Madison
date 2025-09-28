from crewai import Task

class MarketResearchTasks:
    def research_planning_task(self, agent):
        return Task(
            description=(
                "Based on the provided product and market context, develop a detailed and expansive research plan. "
                
            ),
            expected_output=(
                "A comprehensive research plan in Markdown format. "
            ),
            agent=agent,
            output_file='research_plan.md'
        )

    def competitor_analysis_task(self, agent):
        return Task(
            description=(
                "Conduct an exhaustive analysis of the competitive landscape for {product_name} in the {industry} sector. "
                
            ),
            expected_output=(
                "A detailed competitor analysis report in Markdown format. The report must include:\n"
               
            ),
            agent=agent,
            output_file='competitor_analysis.md'
        )

    def customer_analysis_task(self, agent):
        return Task(
            description=(
                "Develop highly detailed customer personas. Create 3-4 distinct personas. For each, write a 'day in the life' narrative, "
                
            ),
            expected_output=(
                "A verbose customer analysis report in Markdown format. The report must contain 3-4 detailed sections, "
                   ),
            agent=agent,
            output_file='customer_analysis.md'
        )

    def risk_critique_task(self, agent, context_tasks):
        return Task(
            description=(
                "Act as a devil's advocate. Meticulously review all prior reports and provide a lengthy, detailed critique. "
                ),
            expected_output=(
                "A detailed critical analysis report in Markdown format. Present your findings as a numbered list "
                ),
            agent=agent,
            context=context_tasks,
            output_file='risk_analysis.md'
        )

    def synthesis_task(self, agent, context_tasks):
        return Task(
            description=(
                "Synthesize all findings into a single, verbose, and comprehensive market research document. "
                
            ),
            expected_output=(
                "A final, comprehensive, and extremely detailed market analysis report in Markdown format." ),
            agent=agent,
            context=context_tasks,
            output_file='refocused_market_analysis_report.md' if '{refocus_mode}' == 'true' else 'final_market_analysis_report.md'
        )
