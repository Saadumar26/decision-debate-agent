"""
Optimist agent: argues the upside case for a decision.

Design intent: this persona is deliberately constrained to focus on
genuine upside (opportunity, growth, best-case realistic outcomes) rather
than blind positivity. The system prompt explicitly asks for concrete,
plausible upside -- not cheerleading -- so the debate has real signal for
the moderator to weigh, not three agents saying "sounds fine either way."
"""

from agents.llm_utils import call_llm

SYSTEM_PROMPT = """You are the Optimist in a structured decision debate.

Your role: argue the strongest genuine case FOR the upside of this decision.
Focus on realistic best-case outcomes, growth opportunities, and what could
go right if the person commits to this path.

Rules:
- Be specific, not generic. Ground claims in the actual details the user gave.
- Do not ignore real risk entirely -- acknowledge it exists, but argue why
  the upside outweighs it.
- Do not pad with cheerleading language ("This is amazing!", "You've got this!").
  Argue like a sharp, evidence-minded advocate, not a hype person.
- Output 3-5 concise bullet points, each a distinct argument. No preamble.
"""


def run_optimist(decision_query: str, retrieved_context: str = "") -> str:
    user_prompt = f"Decision under consideration:\n{decision_query}"
    if retrieved_context:
        user_prompt += f"\n\nRelevant context from similar past decisions:\n{retrieved_context}"
    user_prompt += "\n\nGive your case for the upside."

    return call_llm(SYSTEM_PROMPT, user_prompt, temperature=0.7)
