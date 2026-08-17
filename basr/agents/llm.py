"""Shared LLM helper for the Phase 5 agent layer (A12).

One thin wrapper over the Groq free tier used by briefs, reports, and agent
eval. Reuses the classifier's model + tolerant JSON parsing so the whole
platform speaks one model dialect. Never raises for model errors: on budget
exhaustion or empty output it returns None and the caller falls back to its
deterministic path (working rule 3 - graceful degradation).

gpt-oss-120b spends tokens on reasoning before emitting content, so calls
here use a generous max_tokens and treat empty content as a retryable error.
"""

from __future__ import annotations

import os
import re
import time

from ..nlp.classifier import MODEL, MODEL_VERSION, _extract_json, _JSON_FENCE_RE


class AgentLLM:
    """Paced single-shot JSON call. Returns the parsed dict or None."""

    def __init__(self, *, min_gap_s: float = 4.0, max_attempts: int = 3) -> None:
        from groq import Groq  # local import: heavy, only needed at runtime

        self._client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self._min_gap_s = min_gap_s
        self._max_attempts = max_attempts
        self._last_ts = 0.0
        self._daily_exhausted = False

    # ------------------------------------------------------------------

    def _pace(self) -> None:
        now = time.monotonic()
        wait = self._last_ts + self._min_gap_s - now
        if wait > 0:
            time.sleep(wait)
        self._last_ts = time.monotonic()

    def ask(self, system: str, user: str, *, max_tokens: int = 1600) -> dict | None:
        """One JSON-answer call. Returns a dict, or None on any failure."""
        if self._daily_exhausted:
            return None
        attempt = 0
        while attempt < self._max_attempts:
            attempt += 1
            self._pace()
            try:
                response = self._client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens,
                )
                content = (response.choices[0].message.content or "").strip()
                if not content:
                    raise ValueError("empty model response (reasoning-only output)")
                data = _extract_json(_JSON_FENCE_RE.sub("", content))
                if not isinstance(data, dict):
                    raise ValueError("model output is not a JSON object")
                return data
            except Exception as exc:
                status = getattr(exc, "status_code", None)
                if status == 429:
                    message = str(exc)
                    if "tokens per day" in message:
                        self._daily_exhausted = True
                        print("    [-] agent LLM: daily token budget exhausted, "
                              "degrading to deterministic output")
                        return None
                if attempt >= self._max_attempts:
                    print(f"    [-] agent LLM failed after {attempt} attempts: "
                          f"{str(exc)[:120]}")
                    return None
                time.sleep(1.0 * attempt)
        return None


def model_version() -> str:
    return MODEL_VERSION
