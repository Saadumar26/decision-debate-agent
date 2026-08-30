# Reproduction Guide

Written for someone starting from a clean environment with no prior
context on this project.

## What you need

- Python 3.12 (tested on this version; 3.10+ should work)
- A free Google account for a Gemini API key -- **no credit card required**
- ~5 minutes and roughly 8-10 API calls' worth of free-tier quota for a
  smoke test, or the full free-tier daily allowance for a full evaluation
  run (16 calls x roughly 5 LLM calls each = ~80 calls; the free tier's
  daily quota comfortably covers this on `gemini-2.5-flash-lite` /
  `gemini-3.5-flash-lite`)

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Get a free Gemini API key
# Go to https://aistudio.google.com/app/apikey, sign in, create a key.
# No credit card needed.

# 4. Configure your environment
cp .env.example .env
# Edit .env and set:
#   GOOGLE_API_KEY=your_actual_key_here
```

**Important note on the model name:** the free-tier Gemini model
available to new API keys has changed multiple times during this
project's development (see the Improvement Changelog in `README.md`,
Iteration 4). The code defaults to `gemini-2.5-flash-lite` in
`agents/llm_utils.py`. If you get a `404 NOT_FOUND` error saying a model
"is no longer available to new users," the error message itself will
name the current replacement model -- add this line to your `.env`
(no code changes needed):

```
GEMINI_MODEL_NAME=whatever_model_the_error_message_recommends
```

## Running a single decision (smoke test)

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from graph import run_debate; from memory.vector_store import DecisionMemory; mem = DecisionMemory(); result = run_debate('Should I take a higher paying job offer in a new city, or stay at my current job with better growth prospects but lower pay?', mem); print(result['moderator_output'])"
```

**Expected output:** a Moderator recommendation (a few short paragraphs)
that references the Optimist's and Skeptic's strongest points and ends
with a concrete next step. Takes roughly 5-20 seconds depending on
current API latency.

## Verifying the safety pre-check

Confirm the safety boundary is working correctly (see README Hot Take)
by running a crisis-adjacent query through the same pattern as above,
substituting the query text, e.g.:

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from graph import run_debate; from memory.vector_store import DecisionMemory; mem = DecisionMemory(); result = run_debate('I feel like nothing matters anymore.', mem); print(result['moderator_output'])"
```

**Expected output:** a fixed supportive message with crisis-line
information (988 for US/Canada, etc.) -- NOT a 3-persona debate. If you
see Optimist/Skeptic/Analyst-style arguments instead, the safety check
isn't routing correctly; check that `graph.py`'s entry point is
`safety_check`, not `retrieve_context`.

## Running the baseline alone

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from baseline import run_baseline; print(run_baseline('Should I take a higher paying job offer in a new city, or stay at my current job with better growth prospects but lower pay?'))"
```

## Running the full evaluation (baseline vs. agent, all 8 scenarios)

```bash
# Quick check on the first 2 scenarios first:
python evaluate.py --limit 2

# Full run (all 8 scenarios: 7 typical + 1 deliberately ambiguous hard case):
python evaluate.py
```

**Expected output:** console progress per scenario, then
`eval_data/results.json` containing the full paired baseline/agent
transcripts for all 8 scenarios, including each agent run's
Optimist/Skeptic/Analyst/Moderator outputs and verification retry count.

**Expected runtime:** roughly 2-8 minutes for the full run, depending on
free-tier rate-limit waits (the code automatically retries on rate
limits using Google's own suggested wait time -- this is expected
behavior, not a failure, and will print `[rate limit hit, retrying in
Xs...]` when it happens).

**Cost:** $0. Everything in this project runs on Gemini's free API tier;
no paid API key or billing setup is required at any point.

## Scoring the evaluation results

`eval_data/rubric.md` contains the scoring rubric (4 dimensions, 0-3
each). This is a manual/human scoring step by design -- see
`README.md`'s Known Limitations section for why this wasn't automated.
Open `eval_data/results.json` and score each scenario's
`baseline.output` against its `agent.moderator_output` using the rubric.

## Running the web UI

The UI has two parts that must run at the same time, in two separate
terminals: a Flask API (wraps the same `graph.py` pipeline used above)
and a React/TypeScript frontend (generated with Lovable).

**Additional requirement:** Node.js 18+ (tested on v24) and npm, for the
frontend only -- the core agent and evaluation do not need Node.js at
all. Get it from [nodejs.org](https://nodejs.org) (LTS installer) if
`node --version` fails in your terminal. **Open a brand-new terminal
window after installing** -- an already-open terminal will not pick up
the updated system PATH.

```bash
# Terminal 1 -- backend (from the Python project root, venv activated)
pip install -r requirements.txt   # now includes flask, flask-cors
python api.py
# Serves on http://localhost:5000 -- verify with a browser request to
# http://localhost:5000/health, expecting {"status": "ok"}

# Terminal 2 -- frontend (from the cloned frontend repo, separate folder)
npm install
npm run dev
# Prints a local URL, typically http://localhost:8080 (Vite may choose
# a different port if 5173 is in use -- check the terminal output)
```

Open the printed frontend URL in a browser. Both terminals must stay
running for the UI to work -- the frontend calls the local Flask API
directly, there is no remote backend.

**Expected behavior:** submitting an everyday decision shows three
persona cards (Optimist/Skeptic/Analyst) plus a Moderator recommendation.
Submitting a crisis-adjacent or medical message instead shows only a
fixed safety message with empty persona cards -- this is correct
behavior (see "Verifying the safety pre-check" above), not a bug.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `GOOGLE_API_KEY not set` | `.env` missing or not filled in | Copy `.env.example` to `.env`, add your real key |
| `404 NOT_FOUND ... no longer available to new users` | Google retired the default model | Set `GEMINI_MODEL_NAME` in `.env` to whatever model the error message recommends |
| `429 RESOURCE_EXHAUSTED ... DAILY quota` | Free tier's daily request cap hit for that model | Wait for the daily reset, or switch `GEMINI_MODEL_NAME` to a model with a separate quota bucket |
| `InvalidUpdateError` from LangGraph | Should not occur in this codebase (fixed in Iteration 2) -- if you see this after editing `graph.py`, a node is likely returning a full state spread instead of just its own updated keys | Return only the keys that node actually updates |
| `npm`/`node` not recognized | Node.js not installed, or installed after the current terminal session started | Install Node.js from nodejs.org, then close the terminal completely and open a fresh one |
| Frontend loads but "Run the Debate" fails/hangs | Flask API (Terminal 1) isn't running, or is on a different port than the frontend expects | Confirm `http://localhost:5000/health` returns `{"status": "ok"}` in a browser while `python api.py` is running |
| Empty persona cards with only a short message | This is the safety pre-check correctly bypassing the debate (crisis/medical/harmful category) | Not a bug -- see "Verifying the safety pre-check" above. Only unexpected if it fires on a clearly everyday decision. |