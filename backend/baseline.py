"""
Baseline: the "reasonable basic way to handle the task before using the
agent solution" (per the hackathon brief).

This is a single direct prompt with basic instructions -- no personas, no
retrieval/memory, no verification loop, no orchestration. It represents
what a person would get from pasting their decision into a generic chat
prompt. This is intentionally NOT a strawman: it uses the same underlying
model (Gemini 3.6 Flash) and a reasonable, clearly-written instruction --
the difference being tested is the *agentic design*, not model quality.
"""

from agents.llm_utils import call_llm

BASELINE_SYSTEM_PROMPT = """You are a helpful assistant. The user will describe
a decision they are trying to make. Give them clear, useful advice to help
them decide."""


def run_baseline(decision_query: str) -> str:
    return call_llm(BASELINE_SYSTEM_PROMPT, decision_query, temperature=0.7)
