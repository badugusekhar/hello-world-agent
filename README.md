# Claude Agents Playground — Claude Agent SDK

A multi-agent demo and prompt-engineering playground built with Python (Flask) + Claude Agent SDK.

---

## Project Structure

```
hello-world-agent/
├── agent/
│   ├── __init__.py
│   └── agent.py          ← Core agent engine (reuse for all features)
├── web/
│   ├── static/
│   │   └── style.css
│   ├── templates/
│   │   └── index.html
│   └── app.py            ← Web server + all features live here
├── tools/
│   ├── __init__.py
│   └── greet_tool.py     ← Placeholder for future custom tools
├── .env                  ← Your API key goes here (never commit this!)
├── requirements.txt
└── README.md
```

---

## Setup in IntelliJ IDEA

### Step 1 — Open the Project
1. Open IntelliJ IDEA
2. Click **File → Open**
3. Select the `hello-world-agent` folder (the project root directory)
4. Click **OK**

### Step 2 — Set Up Python Interpreter
1. Go to **File → Project Structure → SDKs**
2. Click **+** → **Add Python SDK**
3. Choose **Virtualenv Environment → New environment**
4. Click **OK**

### Step 3 — Install Dependencies
Open the **Terminal** tab at the bottom of IntelliJ and run:
```bash
pip install -r requirements.txt
```

### Step 4 — Add Your API Key
1. Open the `.env` file in the project root
2. Replace `your_api_key_here` with your actual key:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
   Get your key from: https://console.anthropic.com/

### Step 5 — Run the App
In the Terminal tab, run:
```bash
cd web
python app.py
```

### Step 6 — Open in Browser
Visit: **http://localhost:5000**

---

## How to Add a New Feature

1. Add a new card in `web/templates/index.html`
2. Add a new route in `web/app.py`
3. Build a prompt string from user input
4. Call `ask_agent(prompt)` — done!

`agent/agent.py` stays the same for most features.

---

## Next Features to Add
- [ ] Calculator (enter two numbers, get result)
- [ ] Finance Quiz Generator
- [ ] Savings Calculator
- [ ] Web Search Agent

---

## Tech Stack
- **Python 3.10+**
- **Flask 3.1** — web server
- **Claude Agent SDK 0.1.48** — AI agent engine
- **python-dotenv** — loads .env file
