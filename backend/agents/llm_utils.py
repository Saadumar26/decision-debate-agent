"""
Shared LLM utility for the Decision Debate Agent.

Uses Google's Gemini API (free tier: gemini-2.5-flash) via the current
`google-genai` SDK (the older `google-generativeai` package is deprecated
as of early 2026 and prints a FutureWarning / will stop receiving fixes).
Centralized here so every agent (optimist, skeptic, analyst, moderator)
calls the model the same way, with the same retry/backoff behavior for
free-tier rate limits.

Design note for the changelog: the free tier has a low requests-per-minute
ceiling. A multi-persona debate makes several calls per single user query
(3 personas + moderator + optional verification), and the evaluation script
multiplies that across baseline + agent runs. Without backoff, batch
evaluation runs would fail midway on 429 errors. This wrapper exists
specifically to make evaluation runs reliable end to end.
"""

import os
import re
import time
import random
from typing import Optional

from google import genai
from google.genai import types

# Model name is configurable via env var since Google has retired/renamed
# free-tier models mid-project before, and free-tier daily quotas vary
# sharply by model (as of testing: gemini-3.6-flash's free daily quota
# was only 20 requests/day, which a multi-persona pipeline making 5-6
# calls per scenario exhausts almost immediately -- gemini-2.5-flash-lite
# has a much higher free daily quota and is used as the default instead.
# A grader hitting a different quota situation only needs to set
# GEMINI_MODEL_NAME in .env, not edit code.
_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-flash-lite")
_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY not set. Copy .env.example to .env and add your key "
            "from https://aistudio.google.com/app/apikey"
        )
    _client = genai.Client(api_key=api_key)
    return _client


def _extract_retry_delay_seconds(error_str: str) -> Optional[float]:
    """Google's 429 responses include an exact suggested wait time (e.g.
    'retryDelay': '48s' or 'Please retry in 48.8s'). Parsing this and
    waiting the exact amount is more reliable than blind exponential
    backoff -- our earlier fixed backoff (capping around ~16s) was not
    long enough for observed per-minute-limit waits of 30-48s, causing
    evaluation runs to fail partway through even with retries enabled."""
    match = re.search(r"retryDelay['\"]?\s*:\s*['\"]?(\d+(?:\.\d+)?)s", error_str)
    if match:
        return float(match.group(1))
    match = re.search(r"retry in (\d+(?:\.\d+)?)s", error_str, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def call_llm(
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 6,
    temperature: float = 0.7,
) -> str:
    """Call Gemini with a system + user prompt. Retries on short-lived
    per-minute rate limits, preferring the exact wait time Google's API
    reports (retryDelay) over a blind exponential guess. Fails fast (no
    retry loop) on a per-DAY quota exhaustion, since no amount of waiting
    within a single script run will fix that -- it surfaces a clear
    message instead of burning through more retries uselessly."""
    client = _get_client()

    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=_MODEL_NAME,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                ),
            )
            return response.text.strip()
        except Exception as e:
            last_error = e
            error_str = str(e).lower()

            is_daily_quota = "perday" in error_str.replace(" ", "") or "requestsperday" in error_str.replace(" ", "")
            if is_daily_quota:
                raise RuntimeError(
                    "Gemini free-tier DAILY quota exhausted for model "
                    f"'{_MODEL_NAME}'. This will not be fixed by retrying within "
                    "this run -- it resets on a rolling basis (Google does not "
                    "publish an exact reset time for all models). Options: "
                    "(1) wait and re-run later, (2) set GEMINI_MODEL_NAME in .env "
                    "to a model with a higher free daily quota, or (3) use a "
                    "different API key. Original error: " + str(e)
                ) from e

            is_rate_limit = "429" in error_str or "quota" in error_str or "resource_exhausted" in error_str
            if is_rate_limit and attempt < max_retries - 1:
                suggested_wait = _extract_retry_delay_seconds(str(e))
                if suggested_wait is not None:
                    wait = suggested_wait + random.uniform(0.5, 2.0)  # small buffer past the exact boundary
                else:
                    wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"  [rate limit hit, retrying in {wait:.1f}s...]")
                time.sleep(wait)
                continue
            raise

    raise RuntimeError(f"LLM call failed after {max_retries} retries: {last_error}")