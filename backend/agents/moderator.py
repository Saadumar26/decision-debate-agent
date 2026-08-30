"""
Moderator agent: synthesizes the Optimist, Skeptic, and Analyst arguments
into one balanced recommendation.

Design intent: the moderator does not just concatenate the three views --
it must explicitly weigh them against each other and produce a single
actionable recommendation with visible reasoning. This is the node the
verification loop (graph.py) checks: if the moderator's synthesis skips
a perspective or contradicts itself, verification sends it back.
"""

from agents.llm_utils import call_llm

SYSTEM_PROMPT = """You are the Moderator in a structured decision debate.

You have three perspectives on a decision: an Optimist case, a Skeptic case,
and an Analyst's trade-off breakdown. Your job is to weigh them and produce
ONE clear, actionable recommendation -- not a summary that lists all three
and shrugs.

Rules:
- Briefly acknowledge the strongest point from each perspective (1 line each).
- State a clear recommendation or a clear "it depends on X" if the decision
  genuinely hinges on missing information the Analyst flagged.
- Justify the recommendation by explicitly weighing the Optimist vs Skeptic
  tension -- do not just average them or restate both sides.
- End with one concrete next step the user could take.
- Keep it under 200 words. No preamble, no "as an AI" disclaimers.
"""


def run_moderator(
    decision_query: str,
    optimist_view: str,
    skeptic_view: str,
    analyst_view: str,
) -> str:
    user_prompt = f"""Decision under consideration:
{decision_query}

Optimist's case:
{optimist_view}

Skeptic's case:
{skeptic_view}

Analyst's trade-off breakdown:
{analyst_view}

Synthesize these into one clear recommendation."""

    return call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.5)
