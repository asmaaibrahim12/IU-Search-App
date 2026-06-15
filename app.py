"""IU Course Search — an AI semantic search demo powered by Claude.

The whole course catalog is placed in a cached system prompt. For each query,
Claude reads the catalog and returns the genuinely relevant courses, ranked,
each with a one-line reason. This is what lets natural-language searches like
"ethics courses for non-CS majors" work — something keyword search can't do.
"""

import json
import os
from pathlib import Path

import anthropic
from flask import Flask, jsonify, request, send_from_directory
from pydantic import BaseModel

BASE_DIR = Path(__file__).parent

# Default to Opus 4.8. For a snappier live demo you can switch to
# "claude-haiku-4-5" (faster, cheaper) via the MODEL env var.
MODEL = os.environ.get("MODEL", "claude-opus-4-8")
MAX_RESULTS = 8

# --- Load the sample dataset --------------------------------------------------

COURSES = json.loads((BASE_DIR / "data" / "courses.json").read_text())
COURSES_BY_CODE = {c["code"]: c for c in COURSES}


def format_catalog(courses: list[dict]) -> str:
    """Render the catalog as stable text so it caches as a fixed prompt prefix."""
    blocks = []
    for c in courses:
        blocks.append(
            f"[{c['code']}] {c['title']} — {c['credits']} credits, {c['level']}\n"
            f"  Department: {c['department']}\n"
            f"  Instructor: {c['instructor']}\n"
            f"  Description: {c['description']}"
        )
    return "\n\n".join(blocks)


SYSTEM_PROMPT = f"""You are the semantic search engine for the Indiana University \
course catalog. A student describes what they are looking for in plain language, \
and you return the courses that genuinely fit their intent.

Rank by how well each course matches the *meaning* of the request, not just shared \
keywords. Understand goals ("I want to learn about the brain"), constraints \
("for non-majors", "without heavy math"), and themes ("startups", "sustainability"). \
If few courses truly fit, return only those — do not pad the list with weak matches. \
Only ever return courses that appear in the catalog below, using their exact course codes.

=== COURSE CATALOG ===
{format_catalog(COURSES)}
=== END CATALOG ==="""


# --- Structured output schema -------------------------------------------------


class Match(BaseModel):
    code: str  # exact course code from the catalog
    relevance: int  # 0-100, how well it matches the search intent
    reason: str  # one short sentence on why it fits this search


class SearchResults(BaseModel):
    matches: list[Match]


# --- App ----------------------------------------------------------------------

client = anthropic.Anthropic()
app = Flask(__name__, static_folder="static")


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.post("/api/search")
def search():
    query = (request.get_json(silent=True) or {}).get("query", "").strip()
    if not query:
        return jsonify({"error": "Please enter something to search for."}), 400

    try:
        response = client.messages.parse(
            model=MODEL,
            max_tokens=4000,
            # Caching the catalog makes every repeat search cheaper and faster.
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": (
                        f'Find the courses most relevant to this search: "{query}".\n'
                        f"Return up to {MAX_RESULTS} matches, most relevant first. "
                        "Only include courses that genuinely fit the request."
                    ),
                }
            ],
            output_format=SearchResults,
        )
    except anthropic.AuthenticationError:
        return jsonify({"error": "Invalid or missing ANTHROPIC_API_KEY."}), 500
    except anthropic.APIError as e:
        return jsonify({"error": f"Claude API error: {e.message}"}), 502

    parsed = response.parsed_output
    results = []
    if parsed:
        for m in parsed.matches:
            course = COURSES_BY_CODE.get(m.code)
            if course:
                results.append({**course, "relevance": m.relevance, "reason": m.reason})

    return jsonify(
        {
            "query": query,
            "results": results,
            # Surface caching in the UI — a nice thing to show in the workshop.
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cache_read_tokens": response.usage.cache_read_input_tokens,
                "cache_write_tokens": response.usage.cache_creation_input_tokens,
            },
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
