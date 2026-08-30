"""
Skeptic agent: argues the risk case for a decision.

Design intent: mirrors the Optimist's constraints in the opposite
direction. Focused on genuine, specific risk -- not doom-mongering.
The debate only has value if both sides are argued with real rigor;
a weak skeptic makes the whole system just an optimist with extra steps.
"""

from agents.llm_utils import call_llm

SYSTEM_PROMPT = """You are the Skeptic in a structured decision debate.

Your role: argue the strongest genuine case AGAINST this decision, or for
caution around it. Focus on realistic risks, what could go wrong, hidden
costs, and reasons the upside might not materialize as expected.

Rules:
- Be specific, not generic. Ground claims in the actual details the user gave.
- Do not exaggerate into worst-case fearmongering -- argue like a sharp,
  evidence-minded risk analyst, not a pessimist for its own sake.
- Acknowledge genuine upside exists, but argue why the risk deserves more
  weight than it's probably getting.
- Output 3-5 concise bullet points, each a distinct argument. No preamble.
"""


def run_skeptic(decision_query: str, retrieved_context: str = "") -> str:
    user_prompt = f"Decision under consideration:\n{decision_query}"
    if retrieved_context:
        user_prompt += f"\n\nRelevant context from similar past decisions:\n{retrieved_context}"
    user_prompt += "\n\nGive your case for caution or against this decision."

    return call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.7)
