"""
Evaluation runner.

Runs both the baseline (single prompt) and the full agent (multi-persona
debate graph) on every scenario in eval_data/scenarios.json, and saves
raw outputs + basic run metadata (timing, retry counts) to a results
file. This does NOT auto-score quality -- per the hackathon brief, a
"good final result" is user-defined, and forcing an LLM to grade its own
sibling's outputs would be circular evidence. Instead this script produces
the paired baseline/agent transcripts that a human (you) scores against
the rubric in eval_data/rubric.md, and that go into the submission as
raw evidence.

Usage:
    python evaluate.py                  # run all scenarios
    python evaluate.py --limit 2        # quick smoke test on first 2
"""

import json
import time
import shutil
import argparse
import tempfile
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from baseline import run_baseline
from graph import run_debate
from memory.vector_store import DecisionMemory

SCENARIOS_PATH = Path("eval_data/scenarios.json")
RESULTS_PATH = Path("eval_data/results.json")


def load_scenarios():
    with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run_one_scenario(scenario: dict) -> dict:
    """Each scenario gets a FRESH, isolated memory store.

    Discovered issue: running all benchmark scenarios against one shared
    persistent memory (as this originally did) caused cross-scenario
    contamination -- e.g. the 'used_vs_new_car' scenario's agent output
    referenced "your upcoming housing goal", which the user never
    mentioned in that query. It leaked in because the unrelated
    'rent_vs_buy' scenario, run earlier in the same batch, had been
    stored in memory and got retrieved as a "similar past decision" by
    TF-IDF's loose similarity matching.

    This is a real failure mode, not just a benchmark artifact: in
    production, an unrelated prior decision (even the user's own) being
    injected as unstated context could distort advice on a fresh
    question. The fix here is narrow and honest about its limits: for
    evaluation, we isolate memory per scenario so the debate quality is
    judged on its own merits, uncontaminated. Memory's actual value
    (recalling a user's own genuinely related past decisions) would need
    a separate, deliberately-related test case to demonstrate -- it is
    not validated by this benchmark run.
    """
    query = scenario["query"]
    print(f"\n=== Scenario: {scenario['id']} ===")
    print(f"Query: {query}")

    temp_dir = tempfile.mkdtemp(prefix="eval_memory_")
    memory = DecisionMemory(persist_dir=temp_dir)

    try:
        print("Running baseline...")
        t0 = time.time()
        baseline_output = run_baseline(query)
        baseline_time = time.time() - t0
        print(f"  baseline done in {baseline_time:.1f}s")

        print("Running agent (multi-persona debate)...")
        t0 = time.time()
        agent_result = run_debate(query, memory)
        agent_time = time.time() - t0
        print(f"  agent done in {agent_time:.1f}s (verification retries: {agent_result.get('retry_count', 0) - 1})")

        return {
            "id": scenario["id"],
            "category": scenario.get("category"),
            "query": query,
            "note": scenario.get("note", ""),
            "baseline": {
                "output": baseline_output,
                "time_seconds": round(baseline_time, 2),
            },
            "agent": {
                "optimist_view": agent_result["optimist_view"],
                "skeptic_view": agent_result["skeptic_view"],
                "analyst_view": agent_result["analyst_view"],
                "moderator_output": agent_result["moderator_output"],
                "verification_retries": agent_result.get("retry_count", 1) - 1,
                "time_seconds": round(agent_time, 2),
            },
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Only run the first N scenarios")
    args = parser.parse_args()

    scenarios = load_scenarios()
    if args.limit:
        scenarios = scenarios[: args.limit]

    results = []
    for scenario in scenarios:
        try:
            result = run_one_scenario(scenario)
        except RuntimeError as e:
            if "DAILY quota exhausted" in str(e):
                print(f"\n  STOPPING: {e}")
                print(f"  Saving {len(results)} completed results so far before exiting.")
                break
            print(f"  ERROR on {scenario['id']}: {e}")
            result = {"id": scenario["id"], "query": scenario["query"], "error": str(e)}
            results.append(result)
            continue
        except Exception as e:
            print(f"  ERROR on {scenario['id']}: {e}")
            result = {"id": scenario["id"], "query": scenario["query"], "error": str(e)}
        results.append(result)

    RESULTS_PATH.parent.mkdir(exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(results)} results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()