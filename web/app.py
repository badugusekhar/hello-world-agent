"""
app.py — Web Server & Feature Layer
=======================================
This is where ALL your features live.
agent.py stays the same — only this file changes per feature.

Current Routes:
  GET  /          → Renders the browser UI (index.html)
  POST /hello     → Hello World feature (greets the user)

How to add a new feature:
  1. Add a new HTML section in index.html
  2. Add a new @app.route() here
  3. Build a prompt string from the user's input
  4. Call ask_agent(prompt) and return the result

Flow:
  Browser → app.py (builds prompt) → agent.py (calls Claude) → Browser
"""

import os
import re
import subprocess
import sys

# Make sure Python can find the agent/ folder from anywhere
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from agent.agent import ask_agent

# Directory where generated prompts are saved as .md files
PROMPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generated-prompts"))


def git_push_prompt(filepath: str, filename: str) -> None:
    """Commit the newly saved prompt file and push to github.com/badugusekhar/claude-code-prompts."""
    try:
        subprocess.run(["git", "-C", PROMPTS_DIR, "add", filename], check=True, timeout=15)
        subprocess.run(
            ["git", "-C", PROMPTS_DIR, "commit", "-m", f"add: {filename}"],
            check=True, timeout=15,
        )
        subprocess.run(["git", "-C", PROMPTS_DIR, "push"], check=True, timeout=30)
    except Exception:
        pass  # push failure is non-fatal — prompt is still saved locally


def slugify(text: str) -> str:
    """Turn a task description into a kebab-case filename slug (max 50 chars)."""
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug[:50].rstrip("-")

# Load ANTHROPIC_API_KEY from .env file
load_dotenv()

# Resolve templates/static relative to this file so Flask works
# whether the script is run from the project root or the web folder.
_base_dir = os.path.dirname(__file__)
app = Flask(
    __name__,
    template_folder=os.path.join(_base_dir, "templates"),
    static_folder=os.path.join(_base_dir, "static"),
)


# ─────────────────────────────────────────────
# ROUTE 1: Home Page
# ─────────────────────────────────────────────
@app.route("/")
def index():
    """Serve the main browser UI."""
    return render_template("index.html")


# ─────────────────────────────────────────────
# ROUTE 2: Hello World Feature
# ─────────────────────────────────────────────
@app.route("/hello", methods=["POST"])
def hello():
    """
    Feature: Greet the user by name.

    Browser sends: { "name": "Sekhar" }
    We build:      "Say a friendly hello to Sekhar in one sentence."
    Claude returns: "Hello, Sekhar! ..."
    Browser shows:  the response
    """
    data = request.get_json()
    name = data.get("name", "World").strip()

    # Build a natural language prompt — this is the ONLY thing you change per feature
    prompt = (
        f"Say a warm and friendly hello to {name} in exactly one sentence. "
        f"Keep it simple and cheerful."
    )

    response = ask_agent(prompt)
    return jsonify({"message": response})


# ─────────────────────────────────────────────
# ROUTE 3: Generate Prompt Feature
# ─────────────────────────────────────────────
@app.route("/generate-prompt", methods=["POST"])
def generate_prompt():
    """
    Feature: Expand a short task description into a detailed Claude Code prompt.

    Browser sends: { "task": "add a dark mode toggle" }
    Returns:       { "prompt": "...", "filename": "add-dark-mode-toggle.md" }
    Also saves the prompt as generated-prompts/<slug>.md
    """
    data = request.get_json()
    task = data.get("task", "").strip()
    if not task:
        return jsonify({"error": "No task provided"}), 400

    meta_prompt = f"""You are an expert Claude Code prompt engineer. Your job is to take a short, informal task description and turn it into a precise, detailed prompt that a developer can paste directly into Claude Code to get excellent results.

Task description: "{task}"

Write a Claude Code prompt using EXACTLY this markdown structure — no extra commentary before or after:

## Context & Assumptions
State the tech stack, framework, or domain you are assuming based on the task description. If the task is ambiguous, pick the most common reasonable interpretation and say so. This lets the developer correct any wrong assumptions before running the prompt.

## Goal
One focused paragraph. What needs to be built, changed, or fixed — and why it matters. Be specific about the outcome, not just the action.

## Acceptance Criteria
A bullet list of concrete, testable conditions. Each criterion must be independently verifiable (e.g. "clicking X does Y", "the value persists after reload", "no console errors in both states"). Avoid vague criteria like "works correctly" or "looks good".

## Constraints & Things to Avoid
Bullets covering: what existing code must not break, which dependencies or patterns to avoid, scope boundaries, and any non-obvious guardrails. Include at least one constraint about not over-engineering.

## Files to Read First
List the specific files Claude should read before writing any code. This prevents unnecessary exploration. If the task is general, list likely candidates based on the assumed stack.

## Suggested Approach
Numbered steps. Each step should be a concrete action (read a file, add a function, edit a specific element). Steps should be ordered so each one builds on the last. Include a final verification step.

Output only the prompt markdown — no preamble, no explanation, no wrapping quotes."""

    response = ask_agent(meta_prompt)

    # Save to generated-prompts/<slug>.md
    slug = slugify(task)
    filename = f"{slug}.md"
    os.makedirs(PROMPTS_DIR, exist_ok=True)
    filepath = os.path.join(PROMPTS_DIR, filename)
    # Avoid clobbering — append a counter if the file already exists
    counter = 1
    while os.path.exists(filepath):
        filepath = os.path.join(PROMPTS_DIR, f"{slug}-{counter}.md")
        filename = f"{slug}-{counter}.md"
        counter += 1
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {task}\n\n")
        f.write(response)
        f.write("\n")

    git_push_prompt(filepath, filename)

    return jsonify({"prompt": response, "filename": filename})


# ─────────────────────────────────────────────
# FUTURE FEATURES — Add new routes below here
# ─────────────────────────────────────────────

# Example skeleton for next feature (Calculator):
#
# @app.route("/calculate", methods=["POST"])
# def calculate():
#     data = request.get_json()
#     num1 = data.get("num1")
#     num2 = data.get("num2")
#     operation = data.get("operation", "plus")
#     prompt = f"Calculate {num1} {operation} {num2}. Reply with just the number."
#     response = ask_agent(prompt)
#     return jsonify({"result": response})


if __name__ == "__main__":
    print("=" * 50)
    print("  Hello World Agent — Starting Server")
    print("  Open your browser at: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
