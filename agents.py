import os
from dotenv import load_dotenv
from crewai import Agent, LLM
from crewai.tools import tool
from tools.market_tools import save_post_to_queue
from tools.market_tools import (
    get_sales_trends,
    get_inventory,
    get_product_margins,
    get_upcoming_events,
)

load_dotenv()

llm = LLM(
    model=os.getenv("MODEL", "gemini/gemini-3.5-flash"),
    api_key=os.getenv("GEMINI_API_KEY"),
)

@tool("sales_trends")
def sales_trends_tool() -> str:
    """Get recent product sales trends from the MarketMate database."""
    return str(get_sales_trends())


@tool("inventory")
def inventory_tool() -> str:
    """Get current product inventory levels."""
    return str(get_inventory())


@tool("product_margins")
def product_margins_tool() -> str:
    """Get product prices, costs, profits, and margin percentages."""
    return str(get_product_margins())


@tool("upcoming_events")
def upcoming_events_tool() -> str:
    """Get upcoming marketing events from the MarketMate database."""
    return str(get_upcoming_events())

sales_analyst = Agent(
    role="Sales Analyst",
    max_iter=2,
    goal="Analyze recent product sales and identify products with strong or weak demand.",
    backstory=(
        "You are a careful e-commerce data analyst. "
        "You study sales trends, revenue, and product performance "
        "and provide concise, evidence-based findings."
    ),
    tools=[
        sales_trends_tool,
        inventory_tool,
        product_margins_tool,
        upcoming_events_tool,
    ],
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

campaign_strategist = Agent(
    role="Campaign Strategist",
    max_iter=2,
    goal="Choose suitable products and marketing angles based on sales, inventory, margins, and upcoming events.",
    backstory=(
        "You are an experienced Pakistani e-commerce marketing strategist. "
        "You turn business data into practical campaign ideas while considering "
        "inventory levels, profitability, and seasonal opportunities."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
)


copywriter = Agent(
    role="Marketing Copywriter",
    max_iter=2,
    goal="Create persuasive marketing copy in English, Roman Urdu, and WhatsApp-friendly formats.",
    backstory=(
        "You are a creative e-commerce copywriter familiar with Pakistani shoppers. "
        "You write clear, engaging copy without making unsupported product claims."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
)


scheduler = Agent(
    role="Marketing Scheduler",
    max_iter=2,
    goal="Prepare marketing posts for a practical weekly schedule while respecting inventory and campaign limits.",
    backstory=(
        "You are a marketing operations specialist. "
        "You organize approved campaign content into a sensible weekly schedule "
        "and avoid scheduling products that should not be promoted."
    ),
    tools=[save_post_to_queue],
    llm=llm,
    verbose=True,
    allow_delegation=False,
)


if __name__ == "__main__":
    print("MarketMate agents loaded successfully.")
    print("Agents:")
    print("-", sales_analyst.role)
    print("-", campaign_strategist.role)
    print("-", copywriter.role)
    print("-", scheduler.role)