from crewai import Task
from typing import List


class MarketResearchTasks:
    def research_planning_task(self, agent, product_name, industry):
        return Task(
            description=(
                f"Create a structured market research plan for {product_name} "
                f"in the {industry} industry."
            ),
            expected_output="A clear research plan in markdown.",
            agent=agent,
        )

    def customer_persona_task(self, agent, product_name, industry):
        return Task(
            description=(
                f"Define customer personas for {product_name} "
                f"in the {industry} industry."
            ),
            expected_output="Customer personas in markdown.",
            agent=agent,
        )

    def competitor_pricing_json_task(self, agent, product_name, industry, competitors: List[str]):
        competitors_text = ", ".join(competitors) if competitors else ""
        return Task(
            description=(
                f"Estimate realistic pricing for {product_name} and the provided competitors "
                f"in the {industry} industry.\n\n"
                "Return STRICT JSON ONLY (no markdown) using EXACTLY this schema:\n"
                "{\n"
                f'  "product": "{product_name}",\n'
                '  "currency": "USD",\n'
                '  "prices": [\n'
                f'    {{"name": "{product_name}", "price": 0}},\n'
                '    {"name": "Competitor Name", "price": 0}\n'
                "  ]\n"
                "}\n\n"
                "Rules:\n"
                f"- Include the main product as the FIRST item with name EXACTLY '{product_name}'.\n"
                "- Include ONLY the competitors provided.\n"
                "- price must be a number (float or int), not a string.\n"
                f"Competitors: {competitors_text}"
            ),
            expected_output="Strict JSON only.",
            agent=agent,
        )

    def feature_scores_json_task(
        self,
        agent,
        product_name,
        industry,
        competitors: List[str],
        features: List[str],
    ):
        competitors_text = ", ".join(competitors) if competitors else ""
        features_text = ", ".join(features) if features else ""
        return Task(
            description=(
                f"Generate feature scores (0–10) for {product_name} and the provided competitors "
                f"in the {industry} industry.\n\n"
                "Return STRICT JSON ONLY (no markdown) using EXACTLY this schema:\n"
                "{\n"
                f'  "product": "{product_name}",\n'
                '  "scores": [\n'
                '    {"product": "<name>", "feature": "<feature>", "score": 0, "rationale": "<short reason>"},\n'
                '    {"product": "<name>", "feature": "<feature>", "score": 0, "rationale": "<short reason>"}\n'
                "  ]\n"
                "}\n\n"
                "Rules:\n"
                f"- Products must include '{product_name}' and ONLY these competitors: {competitors_text}\n"
                f"- Features must include ONLY these features: {features_text}\n"
                "- Include ALL combinations: every product × every feature.\n"
                "- score must be a NUMBER from 0 to 10.\n"
            ),
            expected_output="Strict JSON only.",
            agent=agent,
        )

    def market_growth_json_task(self, agent, product_name, industry, geography, scale, competitors: List[str]):
        competitors_text = ", ".join(competitors) if competitors else ""
        return Task(
            description=(
                f"Estimate market growth trend for the {industry} industry relevant to {product_name}.\n\n"
                "Return STRICT JSON ONLY (no markdown) using EXACTLY this schema:\n"
                "{\n"
                f'  "industry": "{industry}",\n'
                f'  "geography": "{geography}",\n'
                '  "years": ["2023","2024","2025","2026"],\n'
                '  "growth_percent": [12,18,24,33],\n'
                '  "rationale": "Short explanation"\n'
                "}\n\n"
                f"Scale: {scale}\n"
                f"Competitors considered: {competitors_text}\n"
                "Rules:\n"
                "- growth_percent must be 4 numeric values.\n"
            ),
            expected_output="Strict JSON only.",
            agent=agent,
        )

    def review_analysis_task(self, agent, product_name):
        return Task(
            description=(
                f"Analyze customer sentiment for {product_name}.\n\n"
                "Return STRICT JSON ONLY (no markdown):\n"
                "{\n"
                f'  "product": "{product_name}",\n'
                '  "sentiment": {"positive": 60, "negative": 30, "neutral": 10},\n'
                '  "top_positive_themes": ["..."],\n'
                '  "top_negative_themes": ["..."],\n'
                '  "sample_quotes": {\n'
                '    "positive": ["..."],\n'
                '    "negative": ["..."]\n'
                "  }\n"
                "}\n\n"
                "Rules:\n"
                "- positive+negative+neutral should sum to ~100.\n"
                "- Percentages must be integers.\n"
            ),
            expected_output="Strict JSON only.",
            agent=agent,
        )

    def synthesis_task(self, agent, product_name, industry, context_tasks):
        return Task(
            description=(
                f"Synthesize all prior tasks into a final executive market strategy report for "
                f"{product_name} in {industry}.\n\n"
                "Rules:\n"
                "- Use sentiment values EXACTLY from the provided sentiment JSON. Do not invent.\n"
                "- Keep it structured with headings and bullets.\n"
            ),
            expected_output="Final executive market strategy report in markdown.",
            agent=agent,
            context=context_tasks,
        )

