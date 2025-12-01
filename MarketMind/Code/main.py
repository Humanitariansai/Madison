%%writefile main.py
import os
from crewai import Crew
from agents import MarketResearchAgents
from tasks import MarketResearchTasks
from tools.feature_comparison import FeatureComparisonTool


def run():
    # 1️⃣ Configuration
    product_name = os.getenv("PRODUCT_NAME", "EcoWave Smart Bottle")
    industry = os.getenv("INDUSTRY", "Consumer Goods")

    print(f"\n🚀 Running MarketMind Full Analysis for {product_name} ({industry})\n")

    # 2️⃣ Initialize agents and tasks manager
    agents = MarketResearchAgents()
    tasks = MarketResearchTasks()

    # --- Initialize AI agents ---
    consultant = agents.strategy_consultant()
    competitor_analyst = agents.review_analyst()
    customer_analyst = agents.customer_persona_analyst()
    sentiment_analyst = agents.review_analyst()
    summarizer = agents.lead_strategy_synthesizer()

    # --- Define core analysis tasks ---
    planning_task = tasks.research_planning_task(consultant, product_name, industry)
    competitor_task = tasks.competitor_analysis_task(competitor_analyst, product_name, industry)
    customer_task = tasks.customer_persona_task(customer_analyst, product_name, industry)
    review_task = tasks.review_analysis_task(sentiment_analyst, product_name)
    summary_task = tasks.executive_summary_task(summarizer, product_name, industry)

    # --- Run feature comparison (external analysis)
    print("🔍 Running feature comparison tool...")
    feature_tool = FeatureComparisonTool()
    feature_output = feature_tool._run(product_name, industry)
    print("✅ Feature comparison complete.\n")

    # --- Combine all prior insights into a synthesis task
    synthesis_task = tasks.synthesis_task(
        summarizer,
        product_name,
        industry,
        [planning_task, competitor_task, customer_task, review_task, summary_task]
    )

    # --- Create Crew and execute tasks collaboratively ---
    print("🤖 Launching multi-agent collaboration...\n")
    crew = Crew(
        agents=[consultant, competitor_analyst, customer_analyst, sentiment_analyst, summarizer],
        tasks=[
            planning_task,
            competitor_task,
            customer_task,
            review_task,
            summary_task,
            synthesis_task,
        ],
        verbose=True,
    )

    results = crew.kickoff()
    print("\n✅ Crew Execution Completed Successfully!\n")

    # --- Save results ---
    os.makedirs("outputs", exist_ok=True)
    output_files = {
        "research_plan.md": getattr(planning_task, "output", ""),
        "competitor_analysis.md": getattr(competitor_task, "output", ""),
        "customer_analysis.md": getattr(customer_task, "output", ""),
        "review_sentiment.md": getattr(review_task, "output", ""),
        "executive_summary.md": getattr(summary_task, "output", ""),
        "feature_comparison.md": feature_output or "",
        "final_market_strategy_report.md": getattr(synthesis_task, "output", ""),
    }

    for filename, content in output_files.items():
        file_path = os.path.join("outputs", filename)
        if content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(content))
        else:
            print(f"⚠️ No content generated for {filename}")

    print("\n🎯 All tasks completed successfully. Reports saved to /outputs directory.\n")
    os.system("ls -lh outputs || echo '⚠️ No output files found.'")
    os.system("head -n 40 outputs/final_market_strategy_report.md || echo '⚠️ No final report generated.'")


if __name__ == "__main__":
    run()
