"""
Safety pre-check for the Decision Debate Agent.

Discovered via stress-testing (see README Hot Take / changelog): the
debate pipeline would happily generate a persuasive "Optimist" case for
things it never should -- e.g. an "upside case" for stopping prescribed
medication, or running a full 3-persona debate on a message containing
crisis/self-harm-adjacent language, with any safety-appropriate response
happening only by accident (only when memory happened to retrieve
related past queries, which is not reliable).

This module classifies the query BEFORE any persona runs. If it falls
into a sensitive category, the debate is skipped entirely and a fixed,
hardcoded response is returned instead of an LLM-generated one. This is
deliberate: for a crisis-support message in particular, the exact
hotline number must never be left to model generation, where it could
be paraphrased or gotten wrong.

Categories:
- "crisis"  -- language suggesting acute emotional distress, hopelessness,
               or self-harm risk
- "medical" -- decisions about starting, stopping, or changing medical
               treatment/medication (out of scope for a general decision
               debate tool; needs a licensed professional, not personas
               arguing "for" and "against")
- "harmful" -- the decision itself is asking for a persuasive case to do
               something clearly illegal or seriously harmful to others
- "normal"  -- everything else; proceeds to the regular debate
"""

from agents.llm_utils import call_llm

CLASSIFY_SYSTEM_PROMPT = """You are a safety classifier for a decision-support tool.
Classify the user's message into exactly ONE category. Respond with
ONLY the single category word, nothing else.

Categories:
- crisis: the message expresses hopelessness, that nothing matters, acute
  emotional distress, self-harm ideation, or a request framed with severe
  psychological urgency. Err toward "crisis" when in doubt for messages
  expressing despair or hopelessness, even if a decision is also present.
- medical: the decision is about starting, stopping, changing, or
  affording prescribed medication or medical treatment.
- harmful: the decision is explicitly asking for help building a case to
  do something clearly illegal or seriously harmful to another person
  (not everyday ethical gray areas -- only clear-cut harm/illegality).
- normal: any other everyday decision (career, money, relationships,
  purchases, etc.), including ones with ethical nuance that don't meet
  the "harmful" bar.

Respond with only one word: crisis, medical, harmful, or normal."""


CRISIS_RESPONSE = """It sounds like things feel very heavy right now, and I want to take that seriously rather than turn it into a pros-and-cons debate.

If you're having thoughts of harming yourself or are in crisis, please reach out right now:
- **US/Canada:** call or text **988** (Suicide & Crisis Lifeline)
- **UK:** call **111** or text **SHOUT to 85258**
- **Elsewhere:** please look up your local crisis line, or contact a doctor, trusted person, or local emergency services

If you're not in immediate danger but this feeling has been sticking around, talking to a doctor, therapist, or someone you trust is a good next step. This tool is built for weighing everyday decisions -- it isn't the right tool for what you're describing right now, and you deserve real support, not an AI-generated debate."""

MEDICAL_RESPONSE = """This tool isn't the right place for decisions about starting, stopping, or changing medication or medical treatment -- that needs a licensed professional who knows your actual health history, not three AI personas debating pros and cons.

If cost is the concern: your prescribing doctor or pharmacist can often help directly -- through a generic alternative, a manufacturer patient assistance program, or adjusting the treatment plan. Please reach out to them before changing anything on your own.

Happy to help you think through other kinds of decisions -- career, money, relationships, and so on."""

HARMFUL_RESPONSE = """I can't build a persuasive case for that -- it crosses into something clearly illegal or seriously harmful to someone else, and giving that a structured "upside case" isn't something this tool should do.

If there's an underlying problem you're actually trying to solve, I'm glad to help you think through legitimate options for it instead."""


def classify_query(query: str) -> str:
    result = call_llm(CLASSIFY_SYSTEM_PROMPT, query, temperature=0.0)
    normalized = result.strip().lower()
    for category in ("crisis", "medical", "harmful", "normal"):
        if category in normalized:
            return category
    return "normal"  # fail open to normal debate rather than fail closed on a parsing miss


def get_safety_response(category: str) -> str:
    return {
        "crisis": CRISIS_RESPONSE,
        "medical": MEDICAL_RESPONSE,
        "harmful": HARMFUL_RESPONSE,
    }.get(category, "")