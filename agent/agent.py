"""
agent.py — Core Agent Engine
==============================
This file is the reusable engine for ALL features.
You rarely need to change this file.

What it does:
- Accepts a prompt string from app.py
- Sends it to Claude via the `claude` CLI (uses the active Claude Code session)
- Returns Claude's response as a string
"""

import os
import subprocess


def ask_agent(prompt: str) -> str:
    """
    Send a prompt to Claude and return the response.

    Uses the `claude` CLI so no API key is needed — it piggybacks on
    the already-authenticated Claude Code session.

    Args:
        prompt (str): The natural language instruction for Claude.
                      Built by app.py based on user browser input.

    Returns:
        str: Claude's final text response.
    """
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "text"],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            env={k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"},
        )
        if result.returncode != 0:
            return f"Error from claude CLI: {result.stderr.strip()}"
        return result.stdout.strip()
    except FileNotFoundError:
        return "Error: `claude` CLI not found. Make sure Claude Code is installed and on PATH."
    except subprocess.TimeoutExpired:
        return "Error: Claude CLI timed out."
    except Exception as e:
        return f"Error calling Claude: {str(e)}"
