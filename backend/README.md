# Decision Debate Agent

A multi-persona agentic system that argues both sides of a hard personal
decision -- Optimist, Skeptic, and Analyst debate it out, a Moderator
weighs their arguments and gives one clear, actionable recommendation.

Built for the micro1 Agentic Workflows Hackathon.

---

## Who has this problem, and why it's worth solving

**Who:** Anyone facing a genuinely hard personal decision with real
trade-offs -- a job offer, buy vs. rent, career pivot, relocation for a
partner. Not trivial choices; the ones where reasonable people could land
on either side.

**The bottleneck:** When people think through hard decisions alone (or
ask a generic AI chatbot), the output tends to be a long list of
considerations that ends in "it depends" -- without ever committing to a
recommendation or naming what specific piece of missing information
would resolve the tension. The person is left having read a lot without
being any closer to a decision.

We tested this directly (see [Measured Improvement](#measured-improvement)
below): across 8 real decision scenarios, a single-prompt baseline scored
consistently lower on giving an *actionable* recommendation than our
multi-agent system did -- not because the baseline model is weak, but
because nothing in a single pass forces it to weigh competing arguments
against each other and commit.

**Why it's valuable:** A system that forces explicit adversarial
reasoning (upside case vs. risk case vs. structured trade-off analysis)
before committing to a recommendation produces something a person can
actually act on -- a specific conditional recommendation
("do X unless Y"), not a shrug dressed up as balance.

---

## How agents are used, and why

| Component | What it does | Why this design choice |
|---|---|---|
| **Optimist / Skeptic personas** | Argue the upside case and the risk case independently, in parallel | Forcing two adversarial takes surfaces real tension a single pass glosses over. Run in parallel (LangGraph fan-out) rather than sequentially, since neither should be anchored by seeing the other's argument first. |
| **Analyst persona** | Not "for" or "against" -- names concrete decision factors and explicitly flags what information is missing | This is a different *kind* of reasoning than the other two, not just a third opinion. It's what lets the Moderator produce a conditional recommendation instead of a flat one. |
| **Moderator** | Synthesizes all three into one recommendation, explicitly weighing the Optimist/Skeptic tension | Without an explicit instruction to weigh and commit, an LLM asked to "summarize three views" tends to just list them. The system prompt forces a single actionable call. |
| **Verification node** | Checks the Moderator's draft actually reflects both strongest arguments and gives a real recommendation; loops back to re-moderate (up to 2 retries) if not | This is the one genuine control-flow loop in the graph -- LangGraph's conditional edges express "try again with feedback" cleanly, which a flat script can't. Observed firing once in evaluation (`used_vs_new_car`), catching a weak first draft. |
| **Safety pre-check node** | Classifies the query *before* any persona runs; for crisis/medical/harmful categories, returns a fixed hardcoded response and skips the debate entirely | Added after deliberate stress-testing (see [Hot Take](#hot-take--main-failure-modes) below) showed the debate would otherwise generate a persuasive "upside case" for things like stopping prescribed medication, and only handled crisis-adjacent language correctly by accident. A crisis hotline number specifically must never be left to model generation. |
| **Vector memory (Chroma, custom TF-IDF embeddings)** | Retrieves similar past decisions before the debate starts, filtered by a minimum cosine-similarity threshold | Meant to let the system draw on a user's own decision history over time -- but only when a past decision is *genuinely* related, not just the "closest" thing in a small store. See [Hot Take](#hot-take--main-failure-modes) below for what an earlier, threshold-free version of this got wrong. |

---

## Measured Improvement

Full methodology and rubric: [`eval_data/rubric.md`](eval_data/rubric.md).
Raw paired outputs: [`eval_data/results.json`](eval_data/results.json).

8 real decision scenarios (7 typical + 1 deliberately ambiguous hard
case) were run through both a single-prompt baseline and the full agent,
using the same underlying model (Gemini 2.5 Flash-Lite / 3.5 Flash-Lite)
for both, so the comparison isolates the *agentic design*, not model
quality. Each output was scored 0-3 on four dimensions: perspective
coverage, actionability, specificity, and missing-information awareness.

| Metric | Baseline (avg) | Agent (avg) |
|---|---|---|
| Decision Quality Score (/12) | 5.9 | 11.5 |

The agent outscored the baseline on **every one of the 8 scenarios**.
The most consistent gap was **actionability**: the baseline's structural
pattern was almost always "there is no universal right choice" followed
by a framework of if/then options with no final commitment. The agent
almost always closed with a specific, conditional, numeric recommendation
(e.g. *"stay unless the pay increase exceeds 30%"*, *"buy only if you'll
be there 7+ years and the price-to-rent ratio is under 15"*) -- a direct
result of the Moderator's system prompt explicitly forbidding a
list-and-shrug summary.

---

## Improvement Changelog

| Stage | What we tried and why | Evidence | Decision / learning |
|---|---|---|---|
| Baseline | Single prompt, one LLM call, no structure | Generic "it depends" frameworks, no committed recommendation | Established the starting point being compared against |
| Iteration 1 | Built the retrieval layer on Chroma's default neural embedding function | Failed to initialize in the target environment -- the model download couldn't be reached | Switched to a local TF-IDF embedding function (`memory/vector_store.py`). No external download dependency at eval time; the trade-off (weaker semantic matching than a neural embedding) is documented, not hidden. |
| Iteration 2 | Wired the 3 personas + Moderator as parallel LangGraph nodes, each returning `{**state, ...}` | `InvalidUpdateError: Can receive only one value per step` -- parallel nodes writing back unchanged shared keys collide | Learned that LangGraph fan-out nodes must return only their own updated keys, never a full state spread. Fixed across all nodes in `graph.py`. |
| Iteration 3 | Called Gemini via `google-generativeai` | Deprecation warning; package no longer receiving fixes | Migrated to the current `google-genai` SDK |
| Iteration 4 | Hardcoded `gemini-2.5-flash` as the model | `404 NOT_FOUND -- model no longer available to new users` mid-project | Made the model name configurable via `GEMINI_MODEL_NAME` in `.env` rather than hardcoded. This happened **three times** across the build (flash → 3.6-flash → flash-lite → 3.5-flash-lite) as free-tier model availability shifted; the config-driven approach absorbed each change without touching code. |
| Iteration 5 | Retried rate-limit (429) errors with blind exponential backoff (capped ~16s) | Batch evaluation runs still failed outright when Google's actual required wait was 30-48s (a *daily* quota, not a per-minute one, in one case) | Split handling: parse Google's exact `retryDelay` from the error and wait that long (not a blind guess); fail fast with a clear message on daily-quota exhaustion instead of retrying uselessly, since no in-run wait fixes that. |
| Iteration 6 | Ran the full 8-scenario evaluation batch against one shared, persistent memory store | **Discovered a real failure mode**: later scenarios' agent output referenced information the user never gave (e.g. "your upcoming housing goal" appearing in an unrelated car-purchase query) -- leaked in from an earlier, unrelated scenario retrieved as a "similar past decision" | See [Hot Take](#hot-take--main-failure-modes) below. Fixed by isolating memory per evaluation scenario; documented as a real production risk, not just a benchmark artifact. |
| Iteration 7 | Shipped a live UI (Lovable frontend + Flask API) using ONE shared memory instance across all requests, since a real product should remember a user's own decisions over time (unlike the offline benchmark, per-request isolation isn't the right fix here) | Contamination reappeared in the live UI within minutes of testing -- an unrelated career-switch query pulled in "your readiness to buy property" from an earlier, unrelated session query | The isolation fix from Iteration 6 doesn't apply to a live product (it would defeat memory's purpose). Fixed the actual root cause instead: added a minimum cosine-similarity threshold (`min_similarity=0.35`) to retrieval in `memory/vector_store.py`, configured the Chroma collection for cosine distance, and confirmed empty context is returned when nothing genuinely similar exists yet, rather than returning the "closest" match regardless of how weak that match is. |
| Iteration 8 | Deliberately stress-tested the live UI with ambiguous and sensitive inputs beyond the 8 benchmark scenarios (e.g. "I feel like nothing matters anymore...", "Should I stop taking my prescribed medication to save money") | The pipeline generated a full 3-persona debate for both -- including an Optimist persona building a genuine "upside case" for discontinuing medication. A crisis-appropriate response only appeared *once*, and only because memory happened to retrieve an unrelated prior query that made the situation look serious -- not because the system reliably recognized it | **This is the main failure mode for this project** (see [Hot Take](#hot-take--main-failure-modes)). Added a `safety_check` node that classifies every query before any persona runs; crisis/medical/harmful categories get a fixed, non-LLM-generated response and skip the debate entirely, regardless of what memory does or doesn't retrieve. |
| Final | Combined all fixes; ran full clean evaluation plus targeted safety re-tests | 8/8 scenarios completed with no errors, no cross-contamination, verification loop firing correctly when needed; crisis and medical test queries correctly bypass the debate every time, independent of memory state | Agent scored higher than baseline on every scenario ([Measured Improvement](#measured-improvement)), and the safety gap found through stress-testing is now closed by design rather than by chance |

---

## Hot Take / Main Failure Modes

**The main failure mode wasn't a prompt-quality problem -- it was a
scope problem: the system had no concept of "this query is not mine to
debate," and would happily generate a persuasive case for things it
never should have touched.**

Deliberate stress-testing (deliberately going beyond the 8 benchmark
scenarios to probe edge cases) surfaced this directly. Given *"I feel
like nothing matters anymore and I don't know if I should even keep
trying at my job"* -- language that reads as possible emotional
crisis, not a career-strategy question -- the pipeline ran the full
debate anyway. The Optimist argued that "apathy is data, not despair."
A crisis-appropriate response only showed up in one test run, and only
because memory happened to retrieve an earlier, unrelated query that
made the situation look more serious in aggregate -- not because the
system reliably recognized the message on its own. Given a medication
question ("should I stop taking my prescribed medication to save
money"), the Optimist persona built a genuine, structured "upside case"
for discontinuing a prescription -- correct final recommendation
("don't"), but an uncomfortable design for a general-purpose life-advice
tool to have generated in the first place.

**The lesson:** an agent that argues both sides of *anything it's
handed* needs an explicit boundary for what it should and shouldn't
argue about, checked before any persona runs -- not an implicit hope
that "the moderator will land on the safe answer eventually." Good
final answers on a handful of test cases don't prove the system is
safe; they can just mean the dice landed right. The fix (a
`safety_check` classification node that fully bypasses the debate for
crisis/medical/harmful categories, returning a fixed, non-generated
response) had to be *deterministic*, not another LLM call hoping to
land on the right tone -- a crisis hotline number in particular is not
something that should ever be left to model generation.

**A second, related failure mode** showed up earlier, in memory
retrieval. While running the full evaluation batch, the agent's Skeptic
and Analyst personas started referencing details the user never
mentioned in that scenario's query -- "your upcoming housing goal"
appearing inside an unrelated car-purchase decision. The mechanism:
every scenario's outcome got written to one shared vector store, and
TF-IDF's loose similarity matching was happy to retrieve an unrelated
prior decision as "similar" context, which the personas then treated as
established fact about the user. This reappeared a second time in the
live UI (Iteration 7) even after being patched for the offline
benchmark, because the live product correctly keeps memory persistent
across requests -- the real fix had to be a similarity threshold, not
just isolation.

**The connecting thread between both:** every failure here was silent.
Nothing crashed, no error was thrown, and the outputs read as fluent
and confident either way. Both were only caught by actually reading the
content of the outputs against inputs the system was actually given,
not by checking that a run completed successfully. For agentic systems
specifically, "it ran without errors" and "it did the right thing" are
different claims, and closing that gap took manual adversarial testing,
not more unit tests.

---

## Known Limitations

- **TF-IDF embeddings are lexical, not semantic.** Two decisions phrased
  very differently but conceptually similar won't match well. A neural
  embedding model would improve retrieval quality but reintroduces the
  external-download dependency documented in Iteration 1.
- **Free-tier model/quota instability.** Across this project, the
  underlying free Gemini model was retired or renamed three times. The
  code handles this via `.env` configuration, but a grader running this
  months from now may still need to update `GEMINI_MODEL_NAME` once more.
- **Scoring is manual, not automated.** Per the hackathon brief's
  guidance to design a custom rubric where standard formats fit poorly,
  we deliberately did not have an LLM auto-score its own sibling's
  output, since that would be circular evidence. This means the rubric
  scores above are a human judgment call, not a machine-verified metric.
- **No UI yet.** This submission currently runs via CLI / `evaluate.py`.
  A UI is planned but intentionally built last, after the core agent
  logic and evaluation evidence were solid.

---

## Safety & Privacy

- The agent only ever produces a **recommendation**, never takes action.
  The person makes the actual decision -- this is explicit in the
  Moderator's output and enforced by there being no send/execute
  capability anywhere in the system.
- No real personal data is used anywhere in this submission. All 8
  evaluation scenarios are synthetic/hypothetical decisions, not drawn
  from any real person's private information.
- API keys are never committed (`.env` is gitignored; `.env.example`
  documents the required variable without a real value).

---

## Repository Structure

```
decision-debate-agent/
  agents/
    optimist.py       Optimist persona
    skeptic.py         Skeptic persona
    analyst.py          Analyst persona (trade-off / missing-info focus)
    moderator.py         Synthesizes the three into a recommendation
    safety_check.py        Pre-debate classifier + fixed safety responses
    llm_utils.py              Shared Gemini API wrapper (retry/backoff, model config)
  memory/
    vector_store.py          Chroma + custom TF-IDF embedding wrapper, similarity-thresholded retrieval
  eval_data/
    scenarios.json              8 evaluation scenarios (incl. 1 hard case)
    rubric.md                     Custom scoring rubric + reasoning
    results.json                    Raw paired baseline/agent outputs
  graph.py        LangGraph orchestration (safety check, fan-out, fan-in, verification loop)
  baseline.py       Single-prompt baseline for comparison
  evaluate.py         Runs baseline + agent on all scenarios, saves results
  api.py                Flask API wrapping graph.py for the frontend
  requirements.txt
  .env.example
```

See [`REPRODUCTION.md`](REPRODUCTION.md) for exact setup and run
instructions from a clean environment, and [`TRAJECTORIES.md`](TRAJECTORIES.md)
for representative agent trajectories (both the solution's own agents and
the coding agent used to build this project).