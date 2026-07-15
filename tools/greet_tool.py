"""
greet_tool.py — Custom Tool Example
======================================
This is a placeholder for future custom tools.

Currently, Claude handles greetings on its own (no tool needed).
As your app grows, you would register tools like this
as MCP (Model Context Protocol) servers so Claude can CALL them.

Example future tools for Future Finance Kids:
  - generate_quiz_question(grade: int, topic: str) -> str
  - calculate_savings(amount: float, months: int) -> float
  - fetch_stock_price(symbol: str) -> dict
"""


def greet(name: str) -> str:
    """
    Returns a personalized greeting.
    (Currently used directly in app.py prompt, not as an MCP tool yet.)

    Args:
        name (str): The name to greet.

    Returns:
        str: A greeting message.
    """
    return f"Hello, {name}! Welcome to Future Finance Kids — Planting The Wealth Seed 🌱"
