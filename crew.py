"""Minimal CrewAI smoke test for the configured Gemini API."""

import os

from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit(
            "Set GEMINI_API_KEY or GOOGLE_API_KEY in your .env file before running."
        )

    llm = LLM(
        model=os.getenv("MODEL", "gemini/gemini-2.5-flash"),
        api_key=api_key,
    )
    greeter = Agent(
        role="Greeting assistant",
        goal="Respond to simple greetings clearly and briefly.",
        backstory="You are a concise assistant used to verify the LLM connection.",
        llm=llm,
        verbose=False,
    )
    hello_task = Task(
        description="Say hello in one short sentence.",
        expected_output="A brief greeting.",
        agent=greeter,
    )
    crew = Crew(
        agents=[greeter],
        tasks=[hello_task],
        process=Process.sequential,
        verbose=False,
    )

    print(crew.kickoff())


if __name__ == "__main__":
    main()