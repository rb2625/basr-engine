"""LLM classification: sentiment + emotion + BASR v1-lineage signal taxonomy.

The system prompt is the **v1 lineage** - ``processor.py``'s prompt is kept
nearly verbatim (it is good, per PLAN.md sec 6.4) and extended with the
sentiment/emotion fields the schema demands. Output is a single JSON object
that maps 1:1 onto the ``classifications`` table.

Model: ``openai/gpt-oss-120b`` on Groq's free tier (Amendment A10 - Groq
retired llama-3.3-70b-versatile, so the classifier was re-benchmarked against
the models still available: gpt-oss-120b won (qwen/qwen3.6-27b fails Groq's
json_object mode entirely, allam-2-7b is weak, gpt-oss-20b trails). Note that
Groq's json_object response mode rejects gpt-oss output, so it is NOT used -
the prompt's strong JSON instruction plus the tolerant _extract_json parser
carry the load. Rate limits on the free tier are real, so every request is
paced (default 6s minimum gap) and retried with backoff on 429/5xx.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any

MODEL = "openai/gpt-oss-120b"
MODEL_VERSION = "groq-gpt-oss-120b-v1"

# ---------------------------------------------------------------------------
# Taxonomies (validated outputs)
# ---------------------------------------------------------------------------

SENTIMENT_LABELS = ("positive", "negative", "neutral", "mixed")
EMOTIONS = (
    "anger", "fear", "joy", "sadness", "disgust", "surprise", "trust",
    "anticipation", "neutral",
)
SIGNAL_TYPES = ("stress", "closure", "opportunity", "neutral")
SECTORS = (
    "F&B", "Real Estate", "Tech", "Retail", "Logistics", "Finance",
    "Government Services", "Education", "Healthcare", "Transport", "General",
)

# ---------------------------------------------------------------------------
# Prompt - v1 lineage + sentiment/emotion extension
# ---------------------------------------------------------------------------

_SENTIMENT_BLOCK = """
SENTIMENT CLASSIFICATION RULES (in addition to the above):
- sentiment_score: float -1.0 (very negative) .. 1.0 (very positive). 0 = neutral.
- sentiment_label: "positive" | "negative" | "neutral" | "mixed"
- emotion: one of "anger" | "fear" | "joy" | "sadness" | "disgust" |
  "surprise" | "trust" | "anticipation" | "neutral" - the dominant emotion
  of the speaker/writer, not the topic's general mood.
- sarcasm: boolean - true only when the text is clearly ironic/sarcastic
  (e.g. "great, another rent increase"). Sarcastic negative statements still
  get a negative sentiment_score.
- Sentiment tracks the writer's view of ECONOMIC topics (prices, jobs,
  housing, companies, services, policies) and their experiences with
  services and products. Everything else is "neutral": weather, movies and
  entertainment, food, personal plans, personal purchases of consumer
  products (phone, laptop, TV, games console), general observations,
  questions, and vague statements without a concrete subject (e.g. "the
  economy is good" with no sector or measurement). Enjoying a movie is NOT
  positive sentiment - it is neutral.
- Factual announcements of economic EVENTS keep the event's sentiment:
  a price/fee increase, closure, layoff, or service cut is negative;
  new investments, openings, launches, expansions, tax exemptions, fee cuts,
  price drops, hiring surges, and record profits are positive - the event
  direction decides, not the tone of the announcement.
- Ironic praise of something genuinely bad ("Great, another rent increase.
  Just what we needed." / "Salik charges are the best thing ever") is
  NEGATIVE sentiment with sarcasm=true. Never take ironic praise at face
  value - judge the underlying situation (genuine praise wrapped in
  sarcastic surprise stays positive).
- A complaint about a service/business = negative sentiment even when it is
  not a systemic economic signal (signal_type stays "neutral" unless the
  economic rules above say otherwise).
"""

SYSTEM_PROMPT = f"""
You are an elite macroeconomic data analyst specializing in the UAE market.
You extract ONLY genuine economic intelligence signals from text. You fluently
understand formal Arabic, Gulf/Egyptian/Levantine dialects, English, and
Arabizi (3ashan, wallah, khara, yalla, 7aram, inshallah).

STRICT FILTERING - classify as "neutral" (intensity 1) if the text is:
- International news with no direct UAE market connection
- Personal complaints about individual situations unless they reveal a
  systemic pattern affecting a named company or sector
- Personal social posts, dating/relationships, personal opinions
- Generic product recommendations, consumer preference questions
- Entertainment or weather news unrelated to the UAE economy
- Student questions about education programs
- EXCEPTION: complaints about universal personal-cost items that affect
  everyone (Salik tolls, fees, rent, prices, utility bills) ARE stress
  signals even without a named company - they reveal a sector-wide pattern

Only classify stress/closure/opportunity if the text contains:
- Named companies/banks/developers/sectors with measurable change
- Labor signals (layoffs, hiring surges, salary trends)
- Real estate movements (rent changes, closures, demand shifts)
- Financial stress (loan issues, payment failures, bank problems)
- Business closures/openings with named entities (bankruptcy/insolvency/
  shutdown of a NAMED business = "closure")
- Supply-chain or pricing disruptions, regulatory changes, or macro
  indicators (GDP, PMI, trade, inflation)

CLASSIFICATION RULES:
- signal_type: "stress" | "closure" | "opportunity" | "neutral"
- sector: F&B | Real Estate | Tech | Retail | Logistics | Finance | Government
  Services | Education | Healthcare | Transport | General (General only for
  cross-sector macro signals, not personal posts)
- confidence_score: 0.0 to 1.0
- intensity_score 1-5: 1 vague individual complaint, no named entity; 2 named
  company/location, moderate signal; 3 multiple reports or clear business
  impact; 4 significant named-company/sector-wide impact; 5 systemic risk,
  mass layoffs, major market disruption, macro indicator
- extracted_entities: {{"companies": ["names"], "locations": ["places"]}}
  Only include real company names and real UAE locations
- summary_en: ONE sentence naming the specific economic implication and the
  companies/locations involved. Never vague ("there is demand for X").
{_SENTIMENT_BLOCK}

OUTPUT: ONLY a valid JSON object with exactly these keys:
{{
  "sentiment_score": <float -1.0..1.0>,
  "sentiment_label": "<positive|negative|neutral|mixed>",
  "emotion": "<anger|fear|joy|sadness|disgust|surprise|trust|anticipation|neutral>",
  "sarcasm": <true|false>,
  "signal_type": "<stress|closure|opportunity|neutral>",
  "sector": "<one of the sector list>",
  "intensity_score": <1..5>,
  "confidence": <float 0.0..1.0>,
  "detected_language": "<ar|arz|en|mixed>",
  "extracted_entities": {{"companies": ["..."], "locations": ["..."]}},
  "summary_en": "<one sentence>"
}}
No markdown. No backticks. If the text has no genuine economic signal,
return signal_type "neutral" and intensity 1 - but ALWAYS still score
sentiment, emotion and sarcasm.
"""

# ---------------------------------------------------------------------------
# Result + validation
# ---------------------------------------------------------------------------


@dataclass
class ClassifyResult:
    sentiment_score: float = 0.0
    sentiment_label: str = "neutral"
    emotion: str = "neutral"
    sarcasm: bool = False
    signal_type: str = "neutral"
    sector: str = "General"
    intensity_score: int = 1
    confidence: float = 0.0
    detected_language: str = "mixed"
    extracted_entities: dict = field(default_factory=lambda: {"companies": [], "locations": []})
    summary_en: str = "No summary available."
    raw: dict = field(default_factory=dict)
    model_version: str = MODEL_VERSION

    def to_row(self, raw_doc_id: int) -> dict[str, Any]:
        """Map onto the classifications table columns (schema.sql sec 2)."""
        return {
            "raw_doc_id": raw_doc_id,
            "sentiment_score": round(max(-1.0, min(1.0, self.sentiment_score)), 3),
            "sentiment_label": self.sentiment_label,
            "emotion": self.emotion,
            "sarcasm": self.sarcasm,
            "signal_type": self.signal_type,
            "sector": self.sector,
            "intensity_score": self.intensity_score,
            "confidence": round(max(0.0, min(1.0, self.confidence)), 3),
            "model_version": self.model_version,
            "raw": self.raw,
        }


def _clamp_int(v: Any, lo: int, hi: int, default: int) -> int:
    try:
        return max(lo, min(hi, int(float(v))))
    except (TypeError, ValueError):
        return default


def _clamp_float(v: Any, lo: float, hi: float, default: float) -> float:
    try:
        return max(lo, min(hi, float(v)))
    except (TypeError, ValueError):
        return default


def _pick(v: Any, allowed: tuple[str, ...], default: str) -> str:
    if isinstance(v, str) and v in allowed:
        return v
    return default


def _validate(data: dict) -> ClassifyResult:
    """Coerce an LLM JSON object into a ClassifyResult, tolerating drift."""
    entities = data.get("extracted_entities")
    if isinstance(entities, list):
        entities = {"companies": [], "locations": [e for e in entities if isinstance(e, str)]}
    if not isinstance(entities, dict):
        entities = {"companies": [], "locations": []}
    companies = [e for e in entities.get("companies", []) if isinstance(e, str)][:20]
    locations = [e for e in entities.get("locations", []) if isinstance(e, str)][:20]

    return ClassifyResult(
        sentiment_score=_clamp_float(data.get("sentiment_score"), -1.0, 1.0, 0.0),
        sentiment_label=_pick(data.get("sentiment_label"), SENTIMENT_LABELS, "neutral"),
        emotion=_pick(data.get("emotion"), EMOTIONS, "neutral"),
        sarcasm=bool(data.get("sarcasm", False)),
        signal_type=_pick(data.get("signal_type"), SIGNAL_TYPES, "neutral"),
        sector=_pick(data.get("sector"), SECTORS, "General"),
        intensity_score=_clamp_int(data.get("intensity_score"), 1, 5, 1),
        # The model sometimes echoes the v1 key "confidence_score" - accept both.
        confidence=_clamp_float(
            data.get("confidence", data.get("confidence_score")), 0.0, 1.0, 0.0
        ),
        detected_language=_pick(
            data.get("detected_language"),
            ("ar", "arz", "en", "mixed"),
            "mixed",
        ),
        extracted_entities={"companies": companies, "locations": locations},
        summary_en=str(data.get("summary_en") or "No summary available.").strip()[:500],
        raw=data,
    )


def _extract_json(text: str) -> dict:
    """Parse a model response that may carry markdown fences or stray text."""
    t = text.strip().strip("`")
    if t.startswith("json"):
        t = t[4:].strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    # Last resort: find the first balanced {...} block.
    start = t.find("{")
    if start == -1:
        raise ValueError("no JSON object in model output")
    depth = 0
    for i in range(start, len(t)):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(t[start : i + 1])
    raise ValueError("unbalanced JSON in model output")


# ---------------------------------------------------------------------------
# Groq client
# ---------------------------------------------------------------------------

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class GroqClassifier:
    """Paced, retrying classifier over the Groq free tier."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        # Free-tier RPM is model-specific; gpt-oss-120b answered ~1s/call in
        # benchmarking with no 429 at a 1.5s gap, but a 6s gap (10 RPM) keeps
        # a safe margin for the daily-token wall and burst behavior.
        min_gap_s: float = 6.0,
        max_attempts: int = 3,
    ) -> None:
        from groq import Groq  # local import: heavy, only needed at runtime

        self._client = Groq(api_key=api_key or os.environ.get("GROQ_API_KEY"))
        self._min_gap_s = min_gap_s
        self._max_attempts = max_attempts
        self._last_ts = 0.0
        # Daily token budget (Amendment A5): the free tier caps llama-3.3-70b-v
        # at 100k tokens/day. We self-calibrate from the API's own counter on
        # the first 429, so a cron run stops classifying honestly instead of
        # hammering retries - the remaining docs stay unclassified for the
        # next run (or the fine-tuned model, which is the real unlock).
        self._daily_exhausted = False

    # ------------------------------------------------------------------

    @staticmethod
    def _parse_daily_usage(message: str) -> tuple[int, int] | None:
        """Extract (used, limit) from a 'tokens per day' 429 message."""
        if "tokens per day" not in message:
            return None
        m_used = re.search(r"Used (\d+)", message)
        m_lim = re.search(r"Limit (\d+)", message)
        if m_used and m_lim:
            return int(m_used.group(1)), int(m_lim.group(1))
        return None

    def _budget_exhausted(self, detail: str) -> ClassifyResult:
        return ClassifyResult(
            confidence=0.0,
            raw={"error": f"daily_budget_exhausted: {detail}"},
        )

    def _pace(self) -> None:
        """Enforce a minimum gap between request starts (free-tier RPM)."""
        now = time.monotonic()
        wait = self._last_ts + self._min_gap_s - now
        if wait > 0:
            time.sleep(wait)
        self._last_ts = time.monotonic()

    def classify(self, text: str, *, title: str | None = None) -> ClassifyResult:
        """Classify one document. Returns a validated result (never raises for
        model errors - the pipeline needs graceful degradation, working rule 3)."""
        user_content = (
            f"Analyze this text from the UAE digital ecosystem:\n\n{text}"
            if not title
            else f"Title: {title}\n\nAnalyze this text from the UAE digital ecosystem:\n\n{text}"
        )
        if self._daily_exhausted:
            return self._budget_exhausted("known from earlier 429 in this run")

        attempt = 0
        while True:
            self._pace()
            try:
                response = self._client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.1,
                    # NOTE (A10): Groq's json_object response mode rejects
                    # gpt-oss output (json_validate_failed with an empty
                    # failed_generation), so it is deliberately NOT used here -
                    # the prompt's strict JSON instruction plus _extract_json
                    # (which tolerates fences and stray text) handle it.
                    max_tokens=600,
                )
                content = (response.choices[0].message.content or "").strip()
                if not content:
                    raise ValueError("empty model response")
                data = _extract_json(_JSON_FENCE_RE.sub("", content))
                return _validate(data)
            except Exception as exc:
                attempt += 1
                status = getattr(exc, "status_code", None)
                if status == 429:
                    message = str(exc)
                    # Daily token budget gone (Amendment A5): stop immediately
                    # and honestly, instead of burning retries on a wall.
                    parsed = self._parse_daily_usage(message)
                    if parsed:
                        used, limit = parsed
                        self._daily_exhausted = True
                        print(
                            f"    [-] Groq daily token budget exhausted "
                            f"({used}/{limit}) - docs stay unclassified for next run"
                        )
                        return self._budget_exhausted(f"{used}/{limit} used")
                    if attempt < self._max_attempts:
                        retry_after = None
                        if hasattr(exc, "headers") and exc.headers:
                            retry_after = exc.headers.get("retry-after")
                        wait = 15 * attempt
                        try:
                            wait = max(wait, int(retry_after))
                        except (TypeError, ValueError):
                            pass
                        print(f"    [retry] groq 429: waiting {wait}s "
                              f"(attempt {attempt}/{self._max_attempts})")
                        time.sleep(wait)
                        continue
                if attempt >= self._max_attempts:
                    print(f"    [-] classify failed after {attempt} attempts: {str(exc)[:120]}")
                    return ClassifyResult(confidence=0.0, raw={"error": str(exc)[:300]})
                print(f"    [retry] groq {exc.__class__.__name__}: attempt {attempt}")
                time.sleep(3 * attempt)
