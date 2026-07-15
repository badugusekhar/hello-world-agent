"""
agent.py — Core Agent Engine
==============================
This file is the reusable engine for ALL features.
You rarely need to change this file.

What it does:
- Accepts a prompt string from app.py
- Sends it to Claude via Anthropic API
- Returns Claude's response as a string
"""

import os
from anthropic import Anthropic


def ask_agent(prompt: str) -> str:
    """
    Send a prompt to Claude and return the response.

    Args:
        prompt (str): The natural language instruction for Claude.
                      Built by app.py based on user browser input.

    Returns:
        str: Claude's final text response.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "Error: ANTHROPIC_API_KEY not set in .env file"

    client = Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except Exception as e:
        return f"Error calling Claude: {str(e)}"
