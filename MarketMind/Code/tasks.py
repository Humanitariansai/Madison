from crewai import Task

class MarketResearchTasks:
    def research_planning_task(self, agent):
        return Task(
            description=(
                "Based on the provided product and market context, develop a detailed and expansive research plan. "
                "This plan should be a set of 8-10 clarifying, strategic questions that probe deep into the market dynamics, "
                "competitive landscape, and customer psychology."
            ),
            expected_output=(
                "A comprehensive research plan in Markdown format. The plan must be presented as a numbered list of at least 8 strategic questions, "
                "each with a brief explanation of why it is critical to the research."
            ),
            agent=agent,
            output_file='research_plan.md'
        )

    def competitor_analysis_task(self, agent):
        return Task(
            description=(
                "Conduct an exhaustive analysis of the competitive landscape for {product_name} in the {industry} sector. "
                "CRITICAL: You MUST search for and identify REAL, ACTUAL competitors by their actual company names. "
                "Do NOT use generic names like 'Competitor 1' or 'Competitor 2'. "
                "Search for companies like Tableau, Power BI, Looker, Qlik, Sisense, Domo, etc. for BI tools, "
                "or search for actual companies in the {industry} space. "
                "Define a detailed scoring rubric with 5-6 key criteria. Identify and analyze at least 4-6 real competitors. "
                "For each, provide a lengthy, narrative-driven profile, covering their history, strategy, strengths, and weaknesses. "
                "IMPORTANT: Create a transparent scoring system where market share scores add up to 100% across all competitors, "
                "and provide detailed rationale for each score based on specific data points and evidence. "
                "If a specific competitor is provided in {competitor_focus}, conduct an especially detailed analysis of that competitor. "
                "Be opinionated and bold in your assessments - don't be afraid to call out overhyped products or highlight underappreciated strengths. "
                "Use your search tools to find actual competitor information, pricing, reviews, and market data. "
                "Search for specific queries like: 'top competitors in {industry}', '{industry} companies list', "
                "'{industry} market leaders', 'best {industry} tools', '{industry} software comparison'. "
                "Make sure to identify real company names and gather actual data about their products, pricing, and market position. "
                "CRITICAL: Document the ACTUAL URLs you find during your searches. "
                "Record every website URL you visit and every source you discover. "
                "These real URLs will be used in the appendix - do NOT use placeholder URLs. "
                "Evidence column must contain SPECIFIC data points like: '4.5/5 rating on G2 with 2,500+ reviews', "
                "'$70/month starting price according to official website', '35% market share based on Gartner 2024 report'. "
                "Do NOT use vague descriptions like 'various reports' or 'industry sources'."
            ),
            expected_output=(
                "A detailed competitor analysis report in Markdown format. The report must include:\n"
                "1. A 'Detailed Scoring Rubric' section with comprehensive tables showing:\n"
                "   - Features scoring criteria (1-5 scale with detailed descriptions)\n"
                "   - Pricing scoring criteria (1-5 scale with detailed descriptions)\n"
                "   - User Sentiment scoring criteria (1-5 scale with detailed descriptions)\n"
                "   - Innovation scoring criteria (1-5 scale with detailed descriptions)\n"
                "   - Support & Training scoring criteria (1-5 scale with detailed descriptions)\n"
                "2. A 'Competitor Scorecard' table with columns: Competitor, Market Share (%), Features (Score/5), Pricing (Score/5), User Sentiment (Score/5), Innovation (Score/5), Support & Training (Score/5), Total Score (out of 25), Evidence.\n"
                "3. A 'Market Share Distribution' section showing how market share percentages add up to 100% across competitors.\n"
                "4. A 'Detailed Evidence Section' with specific data points, sources, and rationale for each competitor's scores.\n"
                "5. A lengthy, multi-paragraph profile for each competitor with detailed analysis.\n"
                "\n"
                "SCORING GUIDELINES:\n"
                "- Market Share: Must add up to 100% across all competitors (e.g., Tableau 35%, Power BI 30%, Looker 20%, Qlik 15%)\n"
                "\n"
                "- Features (1-5 scale):\n"
                "  * 1/5: Basic functionality only, limited integrations, poor user experience, minimal features\n"
                "  * 2/5: Standard features, some integrations, acceptable usability, basic functionality\n"
                "  * 3/5: Good feature set, decent integrations, solid user experience, moderate capabilities\n"
                "  * 4/5: Rich feature set, good integrations, strong user experience, comprehensive capabilities\n"
                "  * 5/5: Comprehensive features, extensive integrations, excellent UX, industry-leading capabilities\n"
                "  * Score based on: Number of data connectors, visualization types, collaboration tools, mobile capabilities, API access, customization options, advanced features\n"
                "\n"
                "- Pricing (1-5 scale):\n"
                "  * 1/5: Expensive with poor value, limited tiers, hidden costs, overpriced\n"
                "  * 2/5: Moderate pricing, basic tiers, some value concerns, fair pricing\n"
                "  * 3/5: Competitive pricing, good value, multiple tiers, reasonable cost\n"
                "  * 4/5: Excellent value, transparent pricing, flexible tiers, great cost-benefit\n"
                "  * 5/5: Outstanding value, highly transparent pricing, extensive tiers, best-in-class pricing\n"
                "  * Score based on: Starting price, enterprise pricing, feature-to-cost ratio, free tier availability, scalability costs, hidden fees\n"
                "\n"
                "- User Sentiment (1-5 scale):\n"
                "  * 1/5: Poor reviews (<2.5/5), many complaints, low satisfaction, negative feedback\n"
                "  * 2/5: Mixed reviews (2.5-3.2/5), some concerns, moderate satisfaction, mixed feedback\n"
                "  * 3/5: Good reviews (3.2-3.8/5), few complaints, high satisfaction, positive feedback\n"
                "  * 4/5: Very good reviews (3.8-4.3/5), minimal complaints, very high satisfaction, excellent feedback\n"
                "  * 5/5: Excellent reviews (>4.3/5), almost no complaints, outstanding satisfaction, exceptional feedback\n"
                "  * Score based on: G2, Capterra, Trustpilot ratings, customer testimonials, support quality feedback, user reviews\n"
                "\n"
                "- Innovation (1-5 scale):\n"
                "  * 1/5: Rare updates, outdated technology, slow to market trends, minimal innovation\n"
                "  * 2/5: Occasional updates, standard technology, moderate innovation, basic advancement\n"
                "  * 3/5: Regular updates, modern technology, good innovation pace, solid advancement\n"
                "  * 4/5: Frequent updates, cutting-edge technology, strong innovation, advanced features\n"
                "  * 5/5: Constant updates, industry-leading technology, exceptional innovation, breakthrough features\n"
                "  * Score based on: Update frequency, AI/ML integration, new feature releases, technology stack, R&D investment, patent activity\n"
                "\n"
                "- Support & Training (1-5 scale):\n"
                "  * 1/5: Poor support, limited training, no community resources, inadequate help\n"
                "  * 2/5: Basic support, some training, minimal community, basic assistance\n"
                "  * 3/5: Good support, comprehensive training, active community, solid assistance\n"
                "  * 4/5: Excellent support, extensive training, vibrant community, outstanding assistance\n"
                "  * 5/5: Outstanding support, comprehensive training programs, thriving community, exceptional assistance\n"
                "  * Score based on: Response times, documentation quality, training programs, community forums, certification options, support channels\n"
                "\n"
                "For each score, provide specific evidence and data points that justify the rating."
            ),
            agent=agent,
            output_file='competitor_analysis.md'
        )

    def customer_analysis_task(self, agent):
        return Task(
            description=(
                "Develop highly detailed customer personas. Create 3-4 distinct personas. For each, write a 'day in the life' narrative, "
                "detail their professional goals, personal motivations, key pain points, and the 'job-to-be-done' they would hire {product_name} for. "
                "Provide a deep and verbose analysis for each. "
                "Be bold and opinionated about customer behavior - challenge conventional wisdom and highlight overlooked opportunities. "
                "Consider any additional context provided in {additional_context}."
            ),
            expected_output=(
                "A verbose customer analysis report in Markdown format. The report must contain 3-4 detailed sections, "
                "one for each persona, including a multi-paragraph narrative and extensive lists for their goals, pain points, and motivations."
            ),
            agent=agent,
            output_file='customer_analysis.md'
        )

    def risk_critique_task(self, agent, context_tasks):
        return Task(
            description=(
                "Act as a devil's advocate. Meticulously review all prior reports and provide a lengthy, detailed critique. "
                "Identify 5-7 potential risks, blind spots, or weak points in the research. For each point, "
                "elaborate on the potential negative impact and suggest how the assumption could be further tested. "
                "Be brutally honest and opinionated - don't sugarcoat the risks or potential failures. "
                "Consider any additional context provided in {additional_context}. "
                "IMPORTANT: If you cannot access the previous reports, create your critique based on general market knowledge "
                "and common risks in the {industry} sector."
            ),
            expected_output=(
                "A detailed critical analysis report in Markdown format. Present your findings as a numbered list "
                "under the heading 'Devil's Advocate Critique & Strategic Risk Assessment', with detailed, multi-sentence explanations for each point."
            ),
            agent=agent,
            context=context_tasks,
            output_file='risk_analysis.md'
        )

    def synthesis_task(self, agent, context_tasks):
        return Task(
            description=(
                "Synthesize all findings into a single, verbose, and comprehensive market research document. "
                "Elaborate extensively on each section, providing rich narrative context and detailed explanations. "
                "The final report should be lengthy and suitable for a deep-read by executive leadership. "
                "Be bold and opinionated in your strategic recommendations - don't be afraid to challenge conventional wisdom. "
                "Consider any additional context provided in {additional_context}. "
                "IMPORTANT: If you cannot access the previous reports, create a comprehensive analysis based on your knowledge "
                "of the {industry} sector and general market research principles. "
                "If refocus_mode is true, create a focused analysis specifically addressing the additional context provided, "
                "while building upon the existing research findings."
            ),
            expected_output=(
                "A final, comprehensive, and extremely detailed market analysis report in Markdown format. The document must be wordy and thorough, with each section containing extensive explanations and evidence. The tone must be bold, opinionated, and decisive to help users make firm decisions. Include the following sections:\n"
                "\n"
                "1. **Executive Summary**: A comprehensive overview with bold, opinionated conclusions and clear strategic direction.\n"
                "2. **Strategic Research Framework**: Detailed explanation of the research methodology and why each question matters.\n"
                "3. **In-Depth Competitive Landscape**: \n"
                "   - Complete scoring rubric tables for each category (Features, Pricing, User Sentiment, Innovation, Support & Training)\n"
                "   - Detailed competitor scorecard with evidence column\n"
                "   - Market share distribution totaling 100%\n"
                "   - Extensive competitor profiles with deep analysis\n"
                "   - Evidence section with specific data points and sources\n"
                "4. **Detailed Customer & Persona Analysis**: Comprehensive user personas with extensive narratives and behavioral insights.\n"
                "5. **Strategic Risk Assessment & Devil's Advocate Critique**: Brutally honest analysis of risks, challenges, and potential failures.\n"
                "6. **Comprehensive SWOT Analysis**: \n"
                "   - **Strengths**: Internal positive attributes with detailed explanations, specific examples, and competitive advantages\n"
                "   - **Weaknesses**: Internal limitations with specific examples, areas for improvement, and competitive disadvantages\n"
                "   - **Opportunities**: External factors with detailed market analysis, growth potential, and strategic opportunities\n"
                "   - **Threats**: External risks with specific scenarios, impact assessment, and competitive threats\n"
                "   - For each SWOT element, provide 3-5 detailed points with extensive explanations and evidence\n"
                "   - CRITICAL: Include REAL NUMBERS, STATISTICS, and MARKET FIGURES in SWOT analysis\n"
                "   - Use specific data like: 'Market size of $25.6B in 2024', '35% annual growth rate', 'Competitor X has 45% market share'\n"
                "   - Do NOT use vague statements without supporting numbers"
                "7. **Bold Strategic Recommendations**: 5-7 high-level, actionable recommendations with extensive justification and reasoning.\n"
                "8. **Appendix A: Research Sources**: Complete list of all sources, links, and references used throughout the report. "
                "CRITICAL: Include only REAL, WORKING URLs that you actually found during your research. "
                "Do NOT include placeholder URLs like 'example.com'. "
                "Document the actual websites, articles, and sources you discovered.\n"
                "\n"
                "REPORT REQUIREMENTS:\n"
                "- Be extremely detailed and wordy - length is not a concern\n"
                "- Use bold, opinionated language throughout\n"
                "- Provide extensive evidence and reasoning for every claim\n"
                "- Include specific data points, statistics, and examples\n"
                "- Make decisive conclusions that help users take action\n"
                "- Challenge conventional wisdom with contrarian insights\n"
                "- Include detailed explanations for every SWOT element\n"
                "- Provide comprehensive source documentation in the appendix with actual URLs and links\n"
                "- Ensure every claim in the report has a corresponding source link in the appendix\n"
                "- CRITICAL: All URLs in the appendix must be REAL, WORKING links from your search results\n"
                "- DO NOT use placeholder URLs like 'example.com' or 'website.com'\n"
                "- Document the actual URLs you found during your research\n"
                "- MINIMUM REQUIREMENT: Include at least 10-15 real URLs in the appendix\n"
                "- Every claim in the report must have a corresponding real URL\n"
                "- Evidence column must contain specific data points, not vague descriptions\n"
                "- SWOT analysis must include real numbers, statistics, and market figures\n"
                "- If refocus_mode is true, create a focused analysis that specifically addresses the additional context while building upon existing research"
            ),
            agent=agent,
            context=context_tasks,
            output_file='refocused_market_analysis_report.md' if '{refocus_mode}' == 'true' else 'final_market_analysis_report.md'
        )
