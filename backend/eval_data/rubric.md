# Evaluation Rubric — Decision Debate Agent

This is the scoring rubric proposed for this project, per the hackathon
instruction to design a custom rubric when the standard metric/baseline
format doesn't fit the task well. A single "accuracy" number doesn't apply
to open-ended decision advice, so quality is broken into scorable
dimensions instead.

Score each of the baseline output and the agent's final `moderator_output`
on the same scenario, using the same rubric, so the comparison is fair.

## Primary metric: Decision Quality Score (0–12 per scenario)

| Dimension | Points | What to check |
|---|---|---|
| **Perspective coverage** | 0–3 | Does the output substantively address both upside AND downside/risk? (0 = one-sided, 3 = both covered with real specifics) |
| **Actionability** | 0–3 | Does it end with a clear recommendation or concrete next step, not just a list of considerations? (0 = no recommendation, 3 = clear recommendation or well-justified conditional) |
| **Specificity to the query** | 0–3 | Does it engage with the actual details the user gave, or is it generic advice that could apply to any decision? (0 = generic, 3 = clearly grounded in the specific scenario) |
| **Missing-information awareness** | 0–3 | Does it flag when the decision genuinely can't be resolved without information the user didn't provide, rather than fabricating assumptions? (0 = confidently answers despite missing info, 3 = explicitly names what's missing) |

## Secondary metrics (tracked, not scored 0-N, just reported)

| Metric | How it's captured |
|---|---|
| Time per scenario | `evaluate.py` logs wall-clock seconds for baseline vs agent |
| Verification retries | How often the moderator's first draft failed the verification check (from `graph.py`'s `retry_count`) |

## How to score

1. Run `python evaluate.py` to generate `eval_data/results.json`.
2. For each scenario, read `baseline.output` and `agent.moderator_output`
   side by side.
3. Score both on the 0–12 rubric above. Use a spreadsheet or a simple
   table in the changelog.
4. The `ambiguous_hard_case` scenario is the one challenging case per the
   hackathon brief -- write up what it revealed (this is changelog
   material, not just a score).

## Why this rubric, not a single pass/fail metric

The hackathon brief allows a custom rubric "if the standard format fits
your task poorly." A binary "is this good advice" judgment is exactly the
kind of soft, multi-dimensional output where implicit judgment calls hide
what actually improved. Breaking it into 4 named dimensions makes it
possible to say specifically *where* the agent's structure earns its
score over the baseline (e.g. "the agent scored 3/3 on missing-information
awareness on 6 of 8 scenarios; baseline scored 3/3 on 0 of 8") instead of
a vague "the agent felt better."
