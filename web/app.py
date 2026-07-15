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
import sys

# Make sure Python can find the agent/ folder from anywhere
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from agent.agent import ask_agent

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
