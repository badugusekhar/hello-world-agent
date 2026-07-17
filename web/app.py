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

import base64
import os
import re
import subprocess
import sys
import tempfile

# Make sure Python can find the agent/ folder from anywhere
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from agent.agent import ask_agent

# Directory where generated prompts are saved as .md files
PROMPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generated-prompts"))

# Voice reference samples for Chatterbox TTS cloning
_VOICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VOICE_SAMPLES = {
    "sekhar":  os.path.join(_VOICE_DIR, "sekhar_voice.wav"),
    "abhinav": os.path.join(_VOICE_DIR, "abhinav_voice.wav"),
    "akshay":  os.path.join(_VOICE_DIR, "akshay_voice.wav"),
}

# Chatterbox model — loaded once on first request
_chatterbox = None

def get_chatterbox():
    global _chatterbox
    if _chatterbox is None:
        from chatterbox.tts import ChatterboxTTS
        _chatterbox = ChatterboxTTS.from_pretrained(device="cpu")
    return _chatterbox


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

    meta_prompt = f"""You are a Claude Code prompt engineer. Convert the task below into a concise, high-signal prompt — 150 to 250 words maximum. Claude Code is already skilled at exploring codebases; it does not need hand-holding. Give it intent and boundaries, not a tutorial.

Task: "{task}"

Output ONLY the prompt, using this exact structure. Keep each section tight:

**Task**
One or two sentences. What to build or fix and the expected outcome. Be specific, not generic.

**Constraints**
3 bullets max. Only include non-obvious guardrails — things Claude would not naturally assume. Skip obvious ones like "don't break tests".

**Done when**
3 bullets max. Each must be independently verifiable by running or clicking something. No vague conditions.

**Start here**
A short list of files most relevant to this task. Infer likely filenames from the task description and common project layouts.

Rules:
- Total output must be under 250 words
- No fluff, no re-stating the obvious, no step-by-step approach (Claude figures that out)
- No preamble or explanation outside the four sections above"""

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
# ROUTE 4: Scrum Status Voice
# ─────────────────────────────────────────────
@app.route("/scrum-voice", methods=["POST"])
def scrum_voice():
    """
    Feature: Generate a voice recording of a daily scrum status update.

    Browser sends: { "today": "...", "tomorrow": "...", "blockers": "..." }
    Returns:       { "script": "...", "audio": "data:audio/wav;base64,..." }

    Step 1 — Claude rewrites bullet points as natural spoken language.
    Step 2 — Coqui XTTS-v2 synthesises audio using sekhar_voice.m4a as the
              voice reference (runs fully locally, no API key needed).
    """
    data     = request.get_json()
    today    = data.get("today", "").strip()
    tomorrow = data.get("tomorrow", "").strip()
    blockers = data.get("blockers", "").strip() or "None"
    voice    = data.get("voice", "sekhar").strip().lower()

    if not today and not tomorrow:
        return jsonify({"error": "Please fill in at least Today or Tomorrow."}), 400

    voice_sample = VOICE_SAMPLES.get(voice, VOICE_SAMPLES["sekhar"])
    if not os.path.exists(voice_sample):
        return jsonify({"error": f"{voice.capitalize()}'s voice file not found. Please copy {voice}_voice.wav to the project root folder."}), 400

    rewrite_prompt = f"""Rewrite this daily scrum status as natural, conversational spoken English for a team standup — the kind you'd say out loud, not read from a list. Use contractions and smooth transitions. Keep it under 45 seconds when spoken aloud. Output ONLY the spoken script, no labels or preamble.

Today: {today}
Tomorrow: {tomorrow}
Blockers: {blockers}"""

    script = ask_agent(rewrite_prompt)

    try:
        import torchaudio
        import numpy as np
        import librosa
        model = get_chatterbox()
        wav = model.generate(script, audio_prompt_path=voice_sample, exaggeration=0.0, cfg_weight=0.95)
        # Slow down to 80% speed to match natural speaking pace (no pitch change)
        wav_np = wav.squeeze().cpu().numpy()
        wav_slow = librosa.effects.time_stretch(wav_np, rate=0.80)
        wav_out = np.expand_dims(wav_slow, axis=0)
        import torch
        wav_tensor = torch.from_numpy(wav_out)
        tmp_path = tempfile.mktemp(suffix=".wav")
        torchaudio.save(tmp_path, wav_tensor, model.sr)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        os.unlink(tmp_path)
    except Exception as e:
        return jsonify({"error": f"TTS generation failed: {str(e)}"}), 500

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return jsonify({"script": script, "audio": f"data:audio/wav;base64,{audio_b64}"})


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
    print("  Claude Agents Playground — Starting Server")
    print("  Open your browser at: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
