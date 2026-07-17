# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Run the app


**CRITICAL**: Flask must be started from **Bash** (not PowerShell) to inherit the Claude Code OAuth session env vars (`CLAUDECODE`, `CLAUDE_CODE_SESSION_ID`, etc.). Starting from PowerShell breaks the `claude` CLI subprocess auth.

```bash
# From Bash terminal — uses the Python 3.11 venv (required for Coqui TTS):
/c/Claude-agents/hello-world-agent/.venv311/Scripts/python.exe web/app.py
```

App runs at `http://localhost:5000`. No build step — Flask serves directly.

### Install dependencies

```bash
# Use the Python 3.11 venv (Coqui TTS requires Python 3.9–3.11)
/c/Claude-agents/hello-world-agent/.venv311/Scripts/pip.exe install -r requirements.txt
playwright install chromium   # one-time, required for E2E tests
```

### Run tests (Playwright E2E)

```bash
# All tests — spins up Flask automatically via conftest.py fixture
pytest tests/

# Single test file
pytest tests/test_hello_world.py

# Single test by name
pytest tests/test_hello_world.py::test_page_title

# Headed mode (watch the browser)
pytest tests/ --headed
```

Tests do **not** call Claude — the `/hello` route is mocked via `page.route()` in every test that exercises it. The `conftest.py` fixture starts Flask on a random free port and tears it down after the session.

### Lint

No linter is configured. If adding one, prefer `ruff` (`pip install ruff && ruff check .`).

## Architecture

**Two-layer design** — `agent.py` is a stable engine; `app.py` is where all features live.

```
agent/agent.py   ← Never changes per feature. Calls `claude` CLI subprocess.
web/app.py       ← All Flask routes live here. Each feature = one route.
web/templates/index.html  ← All UI cards. Feature cards talk to routes via fetch().
web/static/style.css      ← CSS variable system; dark mode via [data-theme="dark"].
generated-prompts/        ← Separate git repo → github.com/badugusekhar/claude-code-prompts
```

### How Claude is called

`ask_agent()` in `agent/agent.py` runs `claude -p "<prompt>" --output-format text` as a subprocess. It **strips `ANTHROPIC_API_KEY` from the env** before spawning — the `.env` placeholder value `ANTHROPIC_API_KEY_HERE` causes the CLI to switch from OAuth to API-key mode and fail. The subprocess has `encoding="utf-8", errors="replace"` and `timeout=120`.

### How to add a new feature

1. Add a card `<div class="card">` to `web/templates/index.html` with a `fetch()` call to the new route
2. Add a `@app.route("/your-route", methods=["POST"])` to `web/app.py`
3. Build a prompt from user input, call `ask_agent(prompt)`, return `jsonify({...})`
4. Never modify `agent/agent.py`

### Dark mode

CSS custom properties (`--bg`, `--text`, `--card-bg`, etc.) defined in `:root` with overrides in `[data-theme="dark"]`. The `<html>` element's `data-theme` attribute is toggled by JS. A `<head>` script reads `localStorage` before paint to avoid FOUC. All new UI components must use CSS variables — no hardcoded colours.

### Generated prompts repo

`generated-prompts/` is an independent git repo tracking `https://github.com/badugusekhar/claude-code-prompts.git` (branch: `main`). After each prompt is generated, `git_push_prompt()` in `app.py` commits and pushes the new `.md` file. Push failures are silently swallowed — the prompt is always saved locally regardless.
