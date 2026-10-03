from crewai import Task

from agents import (
    sales_analyst,
    campaign_strategist,
    copywriter,
    scheduler,
)


sales_analysis_task = Task(
    description="""
    Analyze the recent sales performance of the products.

    Use the available sales, inventory, margin, and upcoming-event tools.
    Identify products with strong demand, weak demand, and useful marketing
    opportunities.

    Provide concise findings supported by the available data.
    """,
    expected_output="""
    A clear summary containing:
    - Top-performing products
    - Weak-performing products
    - Important sales trends
    - Relevant inventory or margin observations
    - Recommended products for marketing
    """,
    agent=sales_analyst,
)


campaign_strategy_task = Task(
    description="""
    Based on the sales analysis, decide which products should be promoted
    and what marketing angle should be used.

    Consider sales performance, inventory, profit margins, and upcoming events.
    Do not recommend products that have critically low stock.
    """,
    expected_output="""
    A campaign strategy containing:
    - Selected products
    - Reason for selecting each product
    - Marketing angle
    - Relevant event or timing
    """,
    agent=campaign_strategist,
)


copywriting_task = Task(
    description="""
    Create marketing copy for the selected campaign products.

    Produce:
    1. English social media copy
    2. Roman Urdu copy
    3. WhatsApp promotional copy

    Keep the copy realistic and do not invent discounts, prices, stock levels,
    or product claims that were not provided by the data.
    """,
    expected_output="""
    Marketing copy for the selected products in:
    - English
    - Roman Urdu
    - WhatsApp format
    """,
    agent=copywriter,
)


scheduling_task = Task(
    description="""
    Create a simple marketing posting schedule based on the campaign strategy
    and generated copy.

    Recommend suitable days and times for the campaign.
    Do not publish anything automatically.
    """,
    expected_output="""
    A simple posting schedule containing:
    - Product
    - Platform
    - Suggested date
    - Suggested time
    - Content type
    - Post content (the actual marketing copy to be saved)
    """,
    agent=scheduler,
)