"""Per-document NLP pipeline: normalize → language ID → classify.

One raw document produces:
- a ``normalized_docs`` row (clean_text, lang, dialect)
- a ``classifications`` row (sentiment + signal taxonomy)
- an updated ``raw_docs.lang``

The heavy Groq call is synchronous, so batches run through a small thread pool
with the classifier's own pacing — the pool size is deliberately modest (free
tier rate limits are the bottleneck, not CPU).
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .classifier import ClassifyResult, GroqClassifier
from .langid import detect_language, get_langid
from .normalizer import arabizi_to_arabic, clean_text


def process_doc(
    doc_id: int,
    text: str,
    title: str | None,
    classifier: GroqClassifier,
) -> tuple[dict[str, Any], dict[str, Any] | None, str]:
    """Normalize + detect language + classify one raw doc.

    Returns (normalized_row, classification_row | None, lang). A hard model
    failure (confidence 0, error raw) returns ``None`` for the classification
    row — the doc stays unclassified so the next run retries it. Never raises.
    """
    clean = clean_text(text)
    # fasttext (if present on Linux) else the heuristic.
    fasttext = get_langid()
    lang = fasttext.detect(clean) if fasttext is not None else detect_language(clean)

    # Give the LLM the Arabizi hint alongside the cleaned original — it reads
    # Arabizi natively, but the transliteration disambiguates digit-letters.
    hint = arabizi_to_arabic(clean) if lang == "arz" else ""
    llm_text = f"{hint}\n---\n{clean}" if hint and hint != clean else clean

    result: ClassifyResult = classifier.classify(llm_text, title=title)

    # The LLM's own language read is usually right; trust it over the heuristic
    # for mixed texts (schema keeps raw output for audit either way).
    if result.confidence > 0.0 and result.detected_language != "mixed":
        lang = result.detected_language

    normalized_row = {
        "raw_doc_id": doc_id,
        "clean_text": clean[:20000],
        "lang": lang,
        "dialect": _dialect_from(lang),
    }
    hard_failure = result.confidence == 0.0 and "error" in result.raw
    classification_row = None if hard_failure else result.to_row(doc_id)
    return normalized_row, classification_row, lang


def _dialect_from(lang: str) -> str | None:
    if lang == "arz":
        return "gulf"  # v1: Gulf-primary; finer dialect tags are a later pass
    if lang == "ar":
        return "msa"
    return None


async def classify_docs(
    docs: list[dict[str, Any]],
    classifier: GroqClassifier,
    *,
    # Serialized: the free tier's token-per-minute window is the binding
    # constraint, not request rate — 2 workers just bursts into 429s.
    workers: int = 1,
) -> list[tuple[dict[str, Any], dict[str, Any] | None, str]]:
    """Classify a list of raw-doc dicts ({id, text, title}) concurrently."""
    if not docs:
        return []
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            loop.run_in_executor(
                pool,
                process_doc,
                d["id"],
                d.get("text") or "",
                d.get("title"),
                classifier,
            )
            for d in docs
        ]
        return await asyncio.gather(*futures)
