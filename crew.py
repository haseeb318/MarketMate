import os

from crewai import Crew, LLM, Process
from dotenv import load_dotenv

from agents import (
    sales_analyst,
    campaign_strategist,
    copywriter,
    scheduler,
)

from tasks import (
    sales_analysis_task,
    campaign_strategy_task,
    copywriting_task,
    scheduling_task,
)


def main() -> None:
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise SystemExit(
            "Set GEMINI_API_KEY or GOOGLE_API_KEY in your .env file before running."
        )

    llm = LLM(
        model=os.getenv("MODEL", "gemini/gemini-3.8-flash"),
        api_key=api_key,
    )

    # Use the same LLM for all MarketMate agents
    sales_analyst.llm = llm
    campaign_strategist.llm = llm
    copywriter.llm = llm
    scheduler.llm = llm

    crew = Crew(
        agents=[
            sales_analyst,
            campaign_strategist,
            copywriter,
            scheduler,
        ],
        tasks=[
            sales_analysis_task,
            campaign_strategy_task,
            copywriting_task,
            scheduling_task,
        ],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    print("\n" + "=" * 60)
    print("MARKETMATE CAMPAIGN RESULT")
    print("=" * 60)
    print(result)
    return result

if __name__ == "__main__":
    main()