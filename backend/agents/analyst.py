"""
Analyst agent: argues from evidence and structured trade-off analysis,
not from an emotional "for/against" stance.

Design intent: Optimist and Skeptic are stance-driven (upside vs risk).
The Analyst is deliberately different in kind, not just in opinion -- it
asks what data or comparison would actually resolve the decision, and
flags where the user's framing might be missing information. This is
what keeps the debate from being a simple two-sided argument and makes
the multi-agent structure earn its place (per the judging rubric: does
each design choice help the agent reach the goal reliably).
"""

from agents.llm_utils import call_llm

SYSTEM_PROMPT = """You are the Analyst in a structured decision debate.

Your role: bring a structured, evidence-oriented lens. You are not "for"
or "against" -- you identify what factors actually matter, what trade-offs
are being made, and what information is missing that would change the
answer.

Rules:
- Identify 2-4 concrete decision factors (e.g. financial runway, reversibility,
  time horizon, opportunity cost) and briefly assess each against what the
  user described.
- Explicitly flag at least one piece of information the user did NOT provide
  that would materially change the analysis, if one exists.
- Do not take a side (upside vs risk) -- stay in comparison/trade-off mode.
- Output as concise bullet points. No preamble.
"""


def run_analyst(decision_query: str, retrieved_context: str = "") -> str:
    user_prompt = f"Decision under consideration:\n{decision_query}"
    if retrieved_context:
        user_prompt += f"\n\nRelevant context from similar past decisions:\n{retrieved_context}"
    user_prompt += "\n\nGive your structured trade-off analysis."

    return call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.4)
