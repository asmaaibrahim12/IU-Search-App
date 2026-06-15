# IU Course Search — an AI semantic search demo

A small, hackable web app that searches a university course catalog using
**natural language**, powered by Claude. Type *"ethics courses for non-CS majors"*
or *"learn about the brain"* and you get the courses that actually fit your
**intent** — something keyword search can't do.

Built as a workshop demo: the whole thing is ~200 lines and every part is meant
to be read and tweaked live.

![flow](https://img.shields.io/badge/stack-Python%20%C2%B7%20Flask%20%C2%B7%20Claude-990000)

---

## What's inside

| File | What it does |
|------|--------------|
| `data/courses.json` | The sample dataset — 36 made-up IU courses across many departments. |
| `app.py` | A tiny Flask server. One endpoint, `/api/search`, asks Claude to rank courses. |
| `static/index.html` | A self-contained search page (HTML + CSS + vanilla JS). |
| `requirements.txt` | Three dependencies: `anthropic`, `flask`, `pydantic`. |

---

## Run it in 3 steps

```bash
# 1. Install dependencies (a virtual environment is recommended)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Add your Anthropic API key
#    Get one at https://console.anthropic.com/settings/keys
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Start the app
python app.py
```

Then open **http://127.0.0.1:5000** and start searching.

> On Windows (PowerShell) use `setx ANTHROPIC_API_KEY "sk-ant-..."` then reopen
> the terminal, or `$env:ANTHROPIC_API_KEY="sk-ant-..."` for the current session.

---

## How it works (the 60-second version)

1. The full course catalog is dropped into a **system prompt** and sent to Claude.
2. When you search, the app asks Claude to return the courses that match your
   request, each with a **relevance score** and a **one-line reason**.
3. Claude replies in a **structured format** (validated with Pydantic), so the
   server can render clean result cards.

```
your query ──▶ Flask /api/search ──▶ Claude (catalog in system prompt)
                                          │
   result cards ◀── structured JSON ◀─────┘
```

---

## Three ideas worth pointing out in the session

- **Semantic vs. keyword search.** Search *"analyze data without heavy math"* —
  you'll get applied stats and data-science courses even though none of them
  contain the phrase. The model matches *meaning*.
- **Prompt caching.** The catalog is sent with `cache_control`, so after the
  first search the catalog tokens are served from cache — cheaper and faster.
  The UI shows the cached-token count under each result.
- **Structured outputs.** `client.messages.parse(..., output_format=SearchResults)`
  guarantees Claude's answer fits a schema, so there's no fragile string parsing.

---

## Make it your own

- **Swap the data.** Replace `data/courses.json` with your own records (events,
  library items, staff directory…) and update the labels in `app.py` /
  `index.html`. The search logic doesn't change.
- **Go faster/cheaper.** For a live demo, try Haiku: `export MODEL=claude-haiku-4-5`.
- **Tune the behavior.** Edit `SYSTEM_PROMPT` in `app.py` to change how strict or
  generous the matching is.

---

## Deploy a live demo (Render)

GitHub Pages can't host this app (it has a Python backend and a secret key), but
the included `render.yaml` makes deploying to [Render](https://render.com) one click:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/asmaaibrahim12/IU-Search-App)

1. Click the button (or: Render dashboard → **New** → **Blueprint** → pick this repo).
2. When prompted, paste your `ANTHROPIC_API_KEY` (it's never stored in the repo).
3. Render builds and gives you a public URL — perfect for sharing in the session.

> The free plan sleeps after inactivity, so the first request after a pause takes
> a few extra seconds to wake up. Hit it once before your demo starts.

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request. It installs the
dependencies, validates the course dataset, and confirms the app imports cleanly —
a quick safety net so a broken change is caught before the workshop.

---

*This is a teaching demo with a fictional catalog — not an official IU service.*
