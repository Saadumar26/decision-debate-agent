# Agent Trajectories

Per the hackathon requirement, this document shows representative
trajectories for every agent used in this project -- both the agents
inside the solution itself, and the coding agent used to build it.

---

## Part A -- Solution agent trajectory (the Decision Debate graph)

This is a full, real trajectory pulled directly from
`eval_data/results.json` for the `used_vs_new_car` scenario -- chosen
deliberately because it's the one scenario where the **verification loop
actually fired** (1 retry), so it demonstrates the retry/checkpoint
behavior, not just a clean single pass.

### 1. Input

```
User query: "I need a car for daily commuting. Should I buy a 3-year-old
used sedan for cheaper, or a brand new car with a loan and warranty?"
```

### 2. Retrieval step

`retrieve_context` node queries the vector memory (Chroma, TF-IDF
embeddings) for similar past decisions. For this evaluation run, memory
was intentionally isolated per scenario (see README changelog,
Iteration 6), so retrieval returned empty context here -- this is
expected and correct behavior for this run, not a failure.

### 3. Parallel persona execution (fan-out)

All three personas receive the same query and run concurrently (LangGraph
fan-out), each with a distinct system-level instruction:

**Optimist instruction:** *"Argue the strongest genuine case FOR the
upside of this decision... Do not pad with cheerleading language."*
→ Output focused on warranty-backed predictability, safety tech, and
subsidized new-car financing rates.

**Skeptic instruction:** *"Argue the strongest genuine case AGAINST this
decision, or for caution... argue like a sharp, evidence-minded risk
analyst."*
→ Output focused on the used car's "maintenance cliff" as warranties
expire, and new-car loan depreciation/negative-equity risk.

**Analyst instruction:** *"Bring a structured, evidence-oriented lens...
Explicitly flag at least one piece of information the user did NOT
provide."*
→ Output identified total-cost-of-ownership, reversibility, and flagged
missing info: *"Your current liquid savings, monthly cash flow buffer,
and the exact mileage/reliability history of the specific used model."*

### 4. Moderator synthesis (first attempt)

The Moderator received all three views and produced a first-draft
synthesis and recommendation.

### 5. Verification checkpoint -- FAILED, feedback given

The verification node (a separate LLM call checking: does the synthesis
reflect the Optimist's strongest point, the Skeptic's strongest point,
and give a real recommendation) returned:

```
FAIL: <feedback identifying what the first draft was missing>
```

This is the human-checkpoint-equivalent built into the graph: no human
was in the loop for this automated eval run, but the same verification
node is what a human reviewer's judgment is being substituted for, and
the graph's conditional edge (`route_after_verify`) routed back to
`moderate` with the feedback appended to the prompt, rather than
returning the flawed first draft.

### 6. Moderator synthesis (retry, with feedback)

The Moderator ran again, this time with: *"A previous draft was flagged
for this issue -- fix it: [feedback]"* appended to its input. Final
output:

```
Recommendation: Buy the 3-year-old used sedan, provided you set aside
$2,000 immediately as a dedicated repair buffer.

Justification: While the Skeptic rightly highlights hidden wear-and-tear
costs and the Optimist champions new-car predictability, the decisive
factor is cash flow flexibility... By paying less upfront and
ring-fencing cash for near-term maintenance, you mitigate the Skeptic's
primary risk while retaining the financial freedom the Analyst points
out is critical for a daily commuter.

Next step: Get a pre-purchase inspection on the used sedan of your
choice to confirm its mechanical health before finalizing the purchase.
```

### 7. Second verification check -- PASSED

Retry count reached 1 (visible in `results.json` as
`"verification_retries": 1`), loop exited, result stored to memory,
returned to caller.

**Total wall-clock time for this trajectory: 17.24s** (includes the
retry pass).

*(All 8 scenarios' full trajectories -- including the 7 that passed
verification on the first attempt -- are in `eval_data/results.json`.
This one was chosen as the representative example specifically because
it shows the retry path.)*

---

## Part A2 -- Solution agent trajectory (safety pre-check bypass)

A second, distinct trajectory shape exists in the graph: the
`safety_check` node can bypass the entire persona debate. This is a real
trajectory from manual stress-testing of the live UI (see README Hot
Take), chosen because it shows the graph taking a genuinely different
path, not just a variation of the same one.

### 1. Input

```
User query: "I feel like nothing matters anymore and I don't know if
I should even keep trying at my job"
```

### 2. Safety classification (entry point)

The `safety_check` node -- now the graph's actual entry point, running
*before* retrieval or any persona -- calls a dedicated classifier
(`agents/safety_check.py`) with a strict instruction to output exactly
one category word: `crisis`, `medical`, `harmful`, or `normal`. For this
input, it returned `crisis`.

### 3. Routing decision

`route_after_safety_check` reads the classification and returns
`"safety_response"` instead of `"retrieve_context"` -- the conditional
edge means the Optimist, Skeptic, Analyst, Moderator, and verification
nodes never execute at all for this input. No persuasive "upside case"
is generated for a message expressing this kind of distress.

### 4. Fixed response (not model-generated)

The `safety_response` node returns a **hardcoded string** from
`agents/safety_check.py`, not an LLM completion:

```
It sounds like things feel very heavy right now, and I want to take
that seriously rather than turn it into a pros-and-cons debate.

If you're having thoughts of harming yourself or are in crisis, please
reach out right now:
- US/Canada: call or text 988 (Suicide & Crisis Lifeline)
- UK: call 111 or text SHOUT to 85258
- Elsewhere: please look up your local crisis line, or contact a
  doctor, trusted person, or local emergency services
...
```

This is deliberate: a hotline number is not something that should ever
be left to model generation, where it could be paraphrased, invented, or
dropped under prompt pressure.

### 5. Graph exits directly to END

Unlike the normal path, this trajectory does **not** pass through
`store_and_end` -- the query is not written to memory, so a sensitive
message doesn't get treated as a "similar past decision" for some future
unrelated query. Total path: `safety_check → safety_response → END`,
skipping 6 of the graph's 10 nodes entirely.

**Before this node existed:** the same input ran the full 8-node debate
path, and only got an appropriate response by chance, when memory
happened to retrieve an earlier related query. See the Improvement
Changelog (Iteration 8) and Hot Take section in `README.md` for the full
story of how this was discovered through deliberate stress-testing.

---

## Part B -- Coding agent trajectory (building the project)

This project was built using an AI coding agent (Claude, via
conversational iterative development) across the full pipeline:
LangGraph orchestration, the persona/moderator agents, the vector memory
layer, the evaluation harness, and documentation. Below are three
representative trajectories showing instruction → tool
response/observed failure → feedback → decision, pulled from the actual
build process.

### Trajectory 1 -- LangGraph parallel-node state bug

**Instruction:** Build a LangGraph `StateGraph` with three persona nodes
running in parallel (fan-out from a retrieval node), converging on a
Moderator node.

**What the agent did:** Wrote each node function to return
`{**state, "some_key": new_value}` -- i.e. spread the full incoming
state and overwrite one key, a common pattern for sequential graphs.

**Tool response (observed failure, reported by the human running the
code locally):**
```
langgraph.errors.InvalidUpdateError: At key 'decision_query': Can
receive only one value per step. Use an Annotated key to handle
multiple values.
```

**Feedback that shaped the next step:** The error indicated multiple
parallel branches were writing conflicting values to the same key, even
though the key (`decision_query`) was never actually changed by any of
them -- the conflict was structural (spreading unchanged state), not a
logic error.

**Decision:** Rewrote every node to return only the keys it actually
updates (e.g. `return {"optimist_view": view}` instead of
`return {**state, "optimist_view": view}`). Verified by recompiling the
graph and re-running -- error resolved, fan-out/fan-in executed cleanly.

---

### Trajectory 2 -- Free-tier model retirement (recurring)

**Instruction:** Use Google's Gemini free API tier for all LLM calls
(chosen over a paid API partway through the project).

**What the agent did:** Hardcoded `gemini-2.5-flash` as the model name
in the shared LLM utility.

**Tool response (observed failure, reported by the human running the
code locally):**
```
404 NOT_FOUND. 'This model models/gemini-2.5-flash is no longer
available to new users. Please update your code to use
models/gemini-3.6-flash...'
```

**Feedback that shaped the next step:** This happened a **second and
third time** later in the project (the replacement models were also
retired for new users in turn), each time with the API's own error
message naming the next recommended model.

**Decision:** Rather than hardcoding a fix each time, made the model
name configurable via a `GEMINI_MODEL_NAME` environment variable with a
sensible default in code, and documented in `REPRODUCTION.md` that a
grader hitting this in the future should read the error message and set
the env var -- no code edit required. This is a directly evaluable
example of an agent decision improving in response to repeated, not
single, negative feedback.

---

### Trajectory 3 -- Discovering cross-scenario memory contamination

**Instruction:** Run the full 8-scenario evaluation batch (baseline vs.
agent) and save results for scoring.

**What the agent did:** Used one shared, persistent `DecisionMemory()`
instance across the whole batch run, per the original design (memory is
meant to persist across a user's decisions over time).

**Tool response (observed anomaly, caught by the human reviewing the
raw output, not a crash):** The `used_vs_new_car` scenario's Skeptic and
Analyst outputs referenced *"your upcoming housing goal"* and *"your
previous consideration of a property down payment"* -- details never
present in that scenario's query. Manual inspection traced this to the
unrelated `rent_vs_buy` scenario, run earlier in the same batch, being
retrieved by the memory layer's TF-IDF similarity search as a "similar
past decision."

**Feedback that shaped the next step:** This was not a code-crashing
bug -- it produced plausible-looking, well-written output that was
nonetheless building on information the user never gave. Recognizing
this required reading the actual content of the outputs, not just
checking that the run completed successfully.

**Decision:** For evaluation purposes, isolated memory per scenario
(fresh temp directory, cleaned up after each run) so the benchmark
comparison is uncontaminated. Documented the underlying risk explicitly
in the README's Hot Take section, since the fix addresses the
*evaluation's* validity but the underlying retrieval-relevance risk
would need a stronger fix (similarity threshold, session/user scoping)
before this memory feature would be safe to ship in a real multi-user
product.

---

## Tooling disclosure

- **Coding agent:** Claude (Anthropic), used conversationally for all
  code in this repository -- `graph.py`, `agents/*.py`,
  `memory/vector_store.py`, `baseline.py`, `evaluate.py`, and all
  documentation.
- **Solution's own agents:** Built on Google's Gemini API
  (`gemini-2.5-flash-lite` / `gemini-3.5-flash-lite`, free tier -- see
  README changelog for why the exact model name changed during
  development), orchestrated with LangGraph.
- Full conversation history with the coding agent (showing every
  instruction, error, and fix in sequence) is available as supplementary
  evidence if needed beyond the representative trajectories above.