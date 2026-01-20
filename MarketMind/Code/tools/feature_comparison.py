import json
from crewai.tools import BaseTool

class FeatureComparisonTool(BaseTool):
    name: str = "feature_comparison"
    description: str = (
        "Compares the product's features with its top competitors to identify unique strengths, "
        "weaknesses, and opportunities for differentiation."
    )

    def _run(self, product_name: str, industry: str) -> str:
        """
        Default run method required by CrewAI BaseTool.
        """
        return self.run_comparison(product_name, industry)

    def run_comparison(self, product_name: str, industry: str) -> str:
        """
        Generates a mock feature comparison table for the given product and competitors.
        Returns JSON and saves a Markdown report.
        """

        # Mocked dataset (you can later replace with scraped or real data)
        comparisons = [
            {
                "feature": "Design & Build Quality",
                product_name: "Premium aluminum body, ergonomic design",
                "Competitor A": "Plastic frame, lightweight",
                "Competitor B": "Glass exterior, heavier feel",
            },
            {
                "feature": "Performance",
                product_name: "High-speed processing with A17 Pro chip equivalent",
                "Competitor A": "Standard mid-tier CPU",
                "Competitor B": "Optimized GPU for multitasking",
            },
            {
                "feature": "Battery Life",
                product_name: "Up to 18 hours with heavy usage",
                "Competitor A": "12 hours typical",
                "Competitor B": "14 hours with power optimization mode",
            },
            {
                "feature": "Software Ecosystem",
                product_name: "Seamless integration with Apple devices",
                "Competitor A": "Android-based open ecosystem",
                "Competitor B": "Cross-platform support with limited optimization",
            },
            {
                "feature": "Price",
                product_name: "$999",
                "Competitor A": "$699",
                "Competitor B": "$849",
            },
        ]

        # Build report content
        report = {
            "title": f"Feature Comparison Report for {product_name}",
            "industry": industry,
            "summary": (
                f"{product_name} shows superior build quality and ecosystem integration "
                f"but may face competition on pricing within the {industry} sector."
            ),
            "comparison_table": comparisons,
        }

        # Save to Markdown
        with open("outputs/feature_comparison.md", "w", encoding="utf-8") as f:
            f.write(f"# Feature Comparison Report for {product_name}\n\n")
            f.write(f"### Industry: {industry}\n\n")
            f.write(f"## Summary\n{report['summary']}\n\n")
            f.write("## Feature Comparison Table\n\n")
            for row in comparisons:
                f.write(f"**{row['feature']}**:\n")
                for key, val in row.items():
                    if key != "feature":
                        f.write(f"- {key}: {val}\n")
                f.write("\n")

        print(f"✅ Feature comparison saved to outputs/feature_comparison.md")
        return json.dumps(report, indent=2)
