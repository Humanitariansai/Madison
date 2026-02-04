# tasks.py
from crewai import Task
from typing import List, Dict


class MarketResearchTasks:
    # ---------------------------
    # Markdown Tasks
    # ---------------------------
    def research_planning_task(self, agent, product_name: str, industry: str):
        return Task(
            description=(
                f"Create a structured market research plan for '{product_name}' in the '{industry}' industry.\n"
                "Output in markdown.\n\n"
                "Rules:\n"
                "- Do NOT invent numbers or citations.\n"
                "- If you make assumptions, label them as assumptions.\n"
            ),
            expected_output="Markdown research plan.",
            agent=agent,
        )

    def customer_persona_task(
        self,
        agent,
        product_name: str,
        industry: str,
        geography: str = "US",
        scale: str = "SME",
    ):
        return Task(
            description=(
                f"Create 3-5 customer personas for '{product_name}' in '{industry}'.\n"
                f"Geography: {geography}\n"
                f"Scale: {scale}\n\n"
                "IMPORTANT:\n"
                "- Personas must include a short 'How derived' explanation.\n"
                "- Include a 'Customization suggestions' section for how users can adjust personas.\n"
                "- Do NOT invent hard facts. Keep plausible and label hypotheses.\n"
                "Output in markdown."
            ),
            expected_output="Markdown personas with derivation + customization suggestions.",
            agent=agent,
        )

    # ---------------------------
    # JSON Tasks for Dashboard
    # ---------------------------
    def competitor_pricing_json_task(
        self, agent, product_name: str, industry: str, competitors: List[str]
    ):
        comps = competitors or []
        return Task(
            description=(
                f"Find pricing for '{product_name}' and ONLY these competitors: {comps}\n"
                f"Industry: {industry}\n\n"
                "Return STRICT JSON ONLY (no markdown):\n"
                "{\n"
                f'  \"product\": \"{product_name}\",\n'
                '  \"currency\": \"USD\",\n'
                '  \"prices\": [\n'
                '    {\"name\": \"<name>\", \"price\": <number|null>, \"source\": \"<url|empty>\"}\n'
                "  ],\n"
                '  \"notes\": \"short notes if approximate or unverified\"\n'
                "}\n\n"
                "Rules:\n"
                "- ONLY include the product + given competitors.\n"
                "- If you cannot verify price, set price=null and source=\"\".\n"
                "- Do NOT output placeholder random values.\n"
            ),
            expected_output="Strict JSON only.",
            agent=agent,
        )

    def feature_scores_json_task(
        self,
        agent,
        product_name: str,
        industry: str,
        competitors: List[str],
        features: List[str],
    ):
        comps = competitors or []
        feats = features or []
        return Task(
            description=(
                f"Generate numeric feature scores (0-10) for a radar chart.\n"
                f"Product: {product_name}\n"
                f"Industry: {industry}\n"
                f"Competitors: {comps}\n"
                f"Features (use ONLY these): {feats}\n\n"
                "Return STRICT JSON ONLY:\n"
                "{\n"
                f'  \"product\": \"{product_name}\",\n'
                f'  \"competitors\": {comps},\n'
                f'  \"features\": {feats},\n'
                '  \"scores\": [\n'
                '    {\"product\": \"<name>\", \"feature\": \"<feature>\", \"score\": 0, \"note\": \"\"}\n'
                "  ]\n"
                "}\n\n"
                "CRITICAL RULES:\n"
                "- You MUST output rows for product_name AND EACH competitor.\n"
                "- You MUST score EVERY feature for EVERY product.\n"
                "- Do NOT invent new features. Do NOT substitute generic tech features.\n"
                "- If not applicable, score 0 and write note='Not applicable'.\n"
            ),
            expected_output="Strict JSON only.",
            agent=agent,
        )

    def market_growth_json_task(
        self,
        agent,
        product_name: str,
        industry: str,
        geography: str,
        competitors: List[str],
    ):
        comps = ", ".join(competitors) if competitors else "None"
        return Task(
            description=(
                "Estimate a PRODUCT-level demand trend (not generic industry CAGR).\n\n"
                f"Product: {product_name}\n"
                f"Industry context: {industry}\n"
                f"Geography: {geography}\n"
                f"Competitor context: {comps}\n\n"
                "Return STRICT JSON ONLY:\n"
                "{\n"
                f'  \"product\": \"{product_name}\",\n'
                f'  \"geography\": \"{geography}\",\n'
                '  \"years\": [\"2023\",\"2024\",\"2025\",\"2026\"],\n'
                '  \"growth_percent\": [0,0,0,0],\n'
                '  \"rationale\": \"1–2 cautious lines; if unsure say low confidence\"\n'
                "}\n\n"
                "Rules:\n"
                "- growth_percent must be numeric.\n"
                "- Do NOT invent citations.\n"
                "- Be conservative.\n"
            ),
            expected_output="Strict JSON only.",
            agent=agent,
        )

    def review_analysis_task(self, agent, product_name: str, industry: str):
        """
        Trust-safe sentiment JSON.
        Quotes must be tied to URLs.
        If you do not have sources, quotes must be [] and no_verified_sources=true.
        """
        return Task(
            description=(
                f"Analyze brand sentiment for '{product_name}' in '{industry}'.\n\n"
                "Return STRICT JSON ONLY:\n"
                "{\n"
                f'  \"product\": \"{product_name}\",\n'
                '  \"no_verified_sources\": true,\n'
                '  \"sentiment\": {\"positive\": 0, \"negative\": 0, \"neutral\": 0},\n'
                '  \"themes\": {\"positive\": [], \"negative\": [], \"neutral\": []},\n'
                '  \"quotes\": [\n'
                '     {\"polarity\":\"positive|negative|neutral\",\"quote\":\"verbatim\",\"url\":\"source url\"}\n'
                "  ],\n"
                '  \"sources\": [\"url1\",\"url2\"]\n'
                "}\n\n"
                "CRITICAL TRUST RULES:\n"
                "- Do NOT create quotes unless you have verified sources.\n"
                "- If you do not have sources: no_verified_sources=true, quotes=[], sources=[]\n"
                "- Percentages should sum to ~100.\n"
                "- Themes must match the product category (no battery themes for food).\n"
            ),
            expected_output="Strict JSON only.",
            agent=agent,
        )

    # ✅ Alias to match your main.py call (fixes your AttributeError)
    def sentiment_verified_json_task(self, agent, product_name: str, industry: str, sources: List[Dict]):
        # For now we don’t pass sources into the prompt (you’re passing sources=[] anyway).
        # Later: we’ll wire real sources into the prompt when your scraper returns them.
        return self.review_analysis_task(agent, product_name, industry)

    # ---------------------------
    # Feature Comparison JSON Task
    # ---------------------------
    def feature_comparison_json_task(
        self,
        agent,
        product_name: str,
        industry: str,
        competitors: List[str],
        features: List[str],
        pricing_json: dict,
    ):
        comps = competitors or []
        feats = features or []

        return Task(
            description=(
                f"Build a feature comparison for '{product_name}' in '{industry}'.\n"
                f"Competitors: {comps}\n"
                f"Features: {feats}\n\n"
                "CRITICAL RULES:\n"
                "- Use ONLY the provided features. Do NOT add/substitute features.\n"
                "- If a feature doesn't apply, output 'N/A'.\n"
                "- Keep language consistent with the category (food must not mention battery).\n"
                "- If feature is Price/Pricing, use pricing_json values.\n\n"
                f"pricing_json:\n{pricing_json}\n\n"
                "Return STRICT JSON ONLY:\n"
                "{\n"
                f'  \"title\": \"Feature Comparison Report for {product_name}\",\n'
                f'  \"industry\": \"{industry}\",\n'
                '  \"summary\": \"1-2 cautious lines\",\n'
                '  \"comparison_table\": [\n'
                '    {\n'
                '      \"feature\": \"Feature name\",\n'
                f'      \"{product_name}\": \"value or N/A\",\n'
                + "".join([f'      \"{c}\": \"value or N/A\",\n' for c in comps[:3]])
                + "      \"_note\": \"(optional)\"\n"
                "    }\n"
                "  ]\n"
                "}\n"
            ),
            expected_output="Strict JSON only.",
            agent=agent,
        )

    # ---------------------------
    # Final Synthesis (Markdown)
    # ---------------------------
    def synthesis_task(self, agent, product_name: str, industry: str, context_tasks: List[Task]):
        return Task(
            description=(
                f"Synthesize prior outputs into a final strategy report for '{product_name}' in '{industry}'.\n\n"
                "Rules:\n"
                "- Do NOT include an implementation timeline unless user explicitly requested it.\n"
                "- Do NOT include budgets unless user explicitly provided a budget range.\n"
                "- Any claims about sentiment must match the sentiment JSON.\n"
                "- If no_verified_sources=true, explicitly state sentiment is not source-verified.\n"
                "Output in markdown."
            ),
            expected_output="Final markdown strategy report.",
            agent=agent,
            context=context_tasks,
        )

