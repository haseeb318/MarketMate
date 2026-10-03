"""
MarketMate – crew.py
CrewAI pipeline entry point.

Phase 8 additions
─────────────────
- Retry-once logic: if crew.kickoff() fails, wait 5 s then retry once.
- Fallback save   : every successful run saves the result to
                    data/fallback_result.json via tools.safety.save_fallback.
- Fallback load   : if both attempts fail, try loading the cached result;
                    raises LLMFailedError if no cache is available.
- main() returns a typed dict so app.py can distinguish live vs cached output
  and display language-quality issues inline.
- Existing pending/scheduled posts are never touched on failure.
"""
from __future__ import annotations

import os
import time

# Disable CrewAI telemetry prompt and OpenTelemetry network export
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

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
from tools.safety import load_fallback, review_campaign_content, save_fallback


# ─── Custom exception ─────────────────────────────────────────────────────────

class LLMFailedError(RuntimeError):
    """
    Raised when the LLM pipeline fails after one retry AND no cached result
    is available.  Caught in app.py and shown as a user-friendly message.
    """


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _build_crew(llm: LLM) -> Crew:
    """Assign *llm* to every agent and return a freshly constructed Crew."""
    sales_analyst.llm = llm
    campaign_strategist.llm = llm
    copywriter.llm = llm
    scheduler.llm = llm

    return Crew(
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


# ─── Public entry point ───────────────────────────────────────────────────────

def main() -> dict:
    """
    Run the MarketMate CrewAI pipeline with automatic retry and cached fallback.

    Return value
    ~~~~~~~~~~~~
    A dict with the following keys:

    ``result``        (str)  – campaign plan text
    ``from_cache``    (bool) – True when loaded from fallback JSON
    ``cached_at``     (str|None) – date the fallback was saved, or None
    ``quality_issues`` (dict) – {section: [issue, …]} from review_campaign_content

    Raises
    ~~~~~~
    LLMFailedError   – both LLM attempts failed AND no cached result exists.
                       Caught in app.py; existing posts are untouched.
    """
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise LLMFailedError(
            "No API key found.  Set GEMINI_API_KEY or GOOGLE_API_KEY in your .env file."
        )

    llm = LLM(
        model=os.getenv("MODEL", "gemini/gemini-3.5-flash"),
        api_key=api_key,
    )
    last_exc: Exception | None = None

    for attempt in range(1, 3):   # up to 2 attempts
        try:
            # Build a fresh Crew each attempt so no task state leaks between runs
            crew = _build_crew(llm)
            result = crew.kickoff()
            result_text = str(result)

            # Persist a known-good result for offline/demo use
            save_fallback(result_text)

            quality_issues = review_campaign_content(result_text)

            return {
                "result": result_text,
                "from_cache": False,
                "cached_at": None,
                "quality_issues": quality_issues,
            }

        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt == 1:
                print(
                    f"[MarketMate] LLM attempt {attempt} failed: {exc}\n"
                    "Retrying in 5 seconds…"
                )
                time.sleep(5)
            else:
                print(f"[MarketMate] LLM attempt {attempt} also failed: {exc}")

    # Both attempts failed — try loading the cached fallback
    cached = load_fallback()
    if cached:
        quality_issues = review_campaign_content(cached["result"])
        return {
            "result": cached["result"],
            "from_cache": True,
            "cached_at": cached.get("saved_at"),
            "quality_issues": quality_issues,
        }

    # No cache available — surface a friendly error
    raise LLMFailedError(
        f"The AI pipeline failed after 2 attempts and no cached result is available.\n"
        f"Last error: {last_exc}\n\n"
        "Your existing scheduled/pending posts are safe and have not been changed."
    )


if __name__ == "__main__":
    data = main()
    print("\n" + "=" * 60)
    print("MARKETMATE CAMPAIGN RESULT")
    if data["from_cache"]:
        print(f"(loaded from cache saved on {data['cached_at']})")    
    print("=" * 60)
    print(data["result"])