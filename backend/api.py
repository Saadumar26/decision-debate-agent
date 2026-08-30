"""
Lightweight Flask API wrapping the Decision Debate Agent's LangGraph
pipeline, for a Lovable (React/TypeScript) frontend to call.

This file intentionally contains no agent logic of its own -- it is a
thin adapter. All actual reasoning happens in graph.py / baseline.py,
unchanged. This keeps the CLI (evaluate.py) and the API using the exact
same underlying pipeline, so the UI never behaves differently from what
was evaluated.

Run with: python api.py
Serves on http://localhost:5000 by default.
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from graph import run_debate
from baseline import run_baseline
from memory.vector_store import DecisionMemory

app = Flask(__name__)
# CORS is required because the Lovable dev server runs on a different
# port (typically 5173/8080) than this API (5000) -- without this,
# browser requests from the frontend would be blocked.
CORS(app)

_memory = DecisionMemory()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/debate", methods=["POST"])
def debate():
    """
    Request body:  {"query": "Should I take the higher paying job..."}
    Response body: {
        "optimist_view": str,
        "skeptic_view": str,
        "analyst_view": str,
        "moderator_output": str,
        "verification_retries": int,
        "retrieved_context": str
    }
    """
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    try:
        result = run_debate(query, _memory)
    except RuntimeError as e:
        if "DAILY quota exhausted" in str(e):
            return jsonify({"error": "Gemini free-tier daily quota exhausted. Try again later or change GEMINI_MODEL_NAME in .env."}), 503
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "optimist_view": result["optimist_view"],
        "skeptic_view": result["skeptic_view"],
        "analyst_view": result["analyst_view"],
        "moderator_output": result["moderator_output"],
        "verification_retries": result.get("retry_count", 1) - 1,
        "retrieved_context": result.get("retrieved_context", ""),
        "safety_category": result.get("safety_category", "normal"),
    })


@app.route("/baseline", methods=["POST"])
def baseline():
    """
    Request body:  {"query": "..."}
    Response body: {"output": str}

    Exposed separately so the frontend can optionally show the baseline
    side-by-side with the agent's result, making the improvement visible
    directly in the UI rather than only in eval_data/results.json.
    """
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    try:
        output = run_baseline(query)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"output": output})


if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)