import os
import logging
import traceback
from typing import Optional, Dict, Any

from crewai import Crew
from agents import MarketResearchAgents
from tasks import MarketResearchTasks
from tools.feature_comparison import FeatureComparisonTool


# ---------------- Logging setup (Render-friendly) ----------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("MarketMind")


def _require_env(var_name: str) -> str:
    """Fail fast with clear error if a required env var is missing."""
    val = os.getenv(var_name)
    if not val:
        raise ValueError(
            f"Missing required environment variable: {var_name}. "
            f"Add it in Render/Vercel/Railway Environment Variables."
        )
    return val


def run_analysis(product_name: Optional[str] = None, industry: Optional[str] = None) -> Dict[str, Any]:
    """
    Runs the full MarketMind analysis and writes markdown reports into ./outputs.

    Returns a dict with:
      - success: bool
      - outputs_dir: str
      - files_written: list[str]
      - feature_comparison: str
      - error: str (only on failure)
    """

    # --- OPTIONAL: Fail fast on keys if your agents/tools need them ---
    # Uncomment these if your code requires them and you want early clear failures:
    # _require_env("OPENAI_API_KEY")
    # _require_env("SERPER_API_KEY")  # only if your tools really need it

    # Use passed args first; fallback to env vars; then defaults
    product_name = product_name or os.getenv("PRODUCT_NAME") or "EcoWave Smart Bottle"
    industry = industry or os.getenv("INDUSTRY") or "Consumer Goods"

    logger.info("🚀 Running MarketMind Full Analysis for %s (%s)", product_name, industry)

    try:
        # 1) Initialize agents and tasks manager
        agents = MarketResearchAgents()
        tasks = MarketResearchTasks()

        # 2) Initialize AI agents
        consultant = agents.strategy_consultant()
        competitor_analyst = agents.review_analyst()
        customer_analyst = agents.customer_persona_analyst()
        sentiment_analyst = agents.review_analyst()
        summarizer = agents.lead_strategy_synthesizer()

        # 3) Define core analysis tasks
        planning_task = tasks.research_planning_task(consultant, product_name, industry)
        competitor_task = tasks.competitor_analysis_task(competitor_analyst, product_name, industry)
        customer_task = tasks.customer_persona_task(customer_analyst, product_name, industry)
        review_task = tasks.review_analysis_task(sentiment_analyst, product_name)
        summary_task = tasks.executive_summary_task(summarizer, product_name, industry)

        # 4) Run feature comparison tool
        logger.info("🔍 Running feature comparison tool...")
        feature_tool = FeatureComparisonTool()

        # Prefer public run() if available, fallback to _run()
        if hasattr(feature_tool, "run") and callable(getattr(feature_tool, "run")):
            feature_output = feature_tool.run(product_name, industry)
        else:
            feature_output = feature_tool._run(product_name, industry)

        logger.info("✅ Feature comparison complete.")

        # 5) Synthesis task
        synthesis_task = tasks.synthesis_task(
            summarizer,
            product_name,
            industry,
            [planning_task, competitor_task, customer_task, review_task, summary_task],
        )

        # 6) Create Crew and execute tasks
        logger.info("🤖 Launching multi-agent collaboration...")
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
        logger.info("✅ Crew Execution Completed Successfully!")

        # 7) Save outputs
        outputs_dir = "outputs"
        os.makedirs(outputs_dir, exist_ok=True)

        output_files = {
            "research_plan.md": getattr(planning_task, "output", ""),
            "competitor_analysis.md": getattr(competitor_task, "output", ""),
            "customer_analysis.md": getattr(customer_task, "output", ""),
            "review_sentiment.md": getattr(review_task, "output", ""),
            "executive_summary.md": getattr(summary_task, "output", ""),
            "feature_comparison.md": feature_output or "",
            "final_market_strategy_report.md": getattr(synthesis_task, "output", ""),
        }

        files_written = []
        for filename, content in output_files.items():
            file_path = os.path.join(outputs_dir, filename)
            if content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(str(content))
                files_written.append(file_path)
            else:
                logger.warning("⚠️ No content generated for %s", filename)

        return {
            "success": True,
            "outputs_dir": outputs_dir,
            "files_written": files_written,
            "feature_comparison": str(feature_output or ""),
            "results": results,
        }

    except Exception as e:
        # ✅ This is the key improvement: we log the real traceback
        logger.error("❌ Error running analysis: %s", str(e))
        logger.error("TRACEBACK:\n%s", traceback.format_exc())

        # Re-raise if you want Streamlit to show the error too (recommended while debugging)
        raise
        # If you prefer not to raise, comment out raise and return:
        # return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


def run():
    """
    Backward-compatible CLI entrypoint.
    Uses env vars (PRODUCT_NAME, INDUSTRY) if set, else defaults.
    """
    _ = run_analysis()  # will raise with full traceback if something fails
    logger.info("🎯 All tasks completed successfully. Reports saved to /outputs.")


if __name__ == "__main__":
    run()



if __name__ == "__main__":
    run()
