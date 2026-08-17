"""Per-document NLP pipeline: normalize -> language ID -> classify.

One raw document produces:
- a ``normalized_docs`` row (clean_text, lang, dialect)
- a ``classifications`` row (sentiment + signal taxonomy)
- an updated ``raw_docs.lang``

Two-stage classification (Amendment A7): the zero-cost lexicon fast path
handles the clear-cut majority; everything ambiguous (sarcasm, conflicting
signals, weak evidence) falls back to the Groq LLM. The heavy Groq call is
synchronous, so batches run through a small thread pool with the classifier's
own pacing - the pool size is deliberately modest (free tier rate limits are
the bottleneck, not CPU).
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .classifier import ClassifyResult, GroqClassifier
from .entities import EntityExtractor
from .langid import detect_language, get_langid
from .lexicon import LexiconClassifier, ROUTE_CONFIDENCE
from .normalizer import arabizi_to_arabic, clean_text
from .topics import TopicAssigner

# Local fast-path confidence bar (Phase 6, A17): when the local n-gram model
# is confident on both tasks, it wins without an LLM call. Calibrated on the
# v2 measurement; can be tuned per the eval.
LOCAL_CONFIDENCE = 0.70


def classify_with_fallback(
    lexicon: LexiconClassifier,
    classifier: GroqClassifier,
    text: str,
    title: str | None,
    lang: str,
    local: object | None = None,
) -> tuple[ClassifyResult, str]:
    """Lexicon first, then the local model (if given), then the LLM.
    Returns (result, path) where path is 'lexicon' | 'local' | 'llm'.
    """
    lex_result = lexicon.classify(text, title=title, lang=lang)
    if lex_result.confidence >= ROUTE_CONFIDENCE:
        return lex_result, "lexicon"
    if local is not None:
        local_result = local.classify(text, title=title, lang=lang)
        if local_result.confidence >= LOCAL_CONFIDENCE:
            return local_result, "local"
    llm_result = classifier.classify(text, title=title)
    return llm_result, "llm"


class HybridClassifier:
    """Production routing as a single object, for the eval harness: lexicon
    fast path, then the local model, then the LLM. Mirrors
    classify_with_fallback exactly."""

    def __init__(
        self,
        lexicon: LexiconClassifier | None = None,
        classifier: GroqClassifier | None = None,
        local=None,
    ) -> None:
        self._lexicon = lexicon or LexiconClassifier()
        self._classifier = classifier or GroqClassifier()
        if local is None:
            from .local_model import LocalModelClassifier
            local = LocalModelClassifier()
        self._local = local

    def classify(
        self, text: str, *, title: str | None = None, lang: str | None = None
    ) -> ClassifyResult:
        result, _ = classify_with_fallback(
            self._lexicon, self._classifier, text, title, lang or "mixed",
            local=self._local,
        )
        return result


def process_doc(
    doc_id: int,
    text: str,
    title: str | None,
    lexicon: LexiconClassifier,
    classifier: GroqClassifier,
    topics: TopicAssigner | None = None,
    entities: EntityExtractor | None = None,
    local=None,
) -> tuple[dict[str, Any], dict[str, Any] | None, str, str,
           list[dict[str, Any]], list[dict[str, Any]]]:
    """Normalize + detect language + classify + enrich one raw doc.

    Returns (normalized_row, classification_row | None, lang, path, topics,
    entities). A hard model failure (confidence 0, error raw) returns ``None``
    for the classification row - the doc stays unclassified so the next run
    retries it. Topics + entities are zero-token and never fail. Never raises.
    """
    clean = clean_text(text)
    # fasttext (if present on Linux) else the heuristic.
    fasttext = get_langid()
    lang = fasttext.detect(clean) if fasttext is not None else detect_language(clean)

    # Give the LLM the Arabizi hint alongside the cleaned original - it reads
    # Arabizi natively, but the transliteration disambiguates digit-letters.
    # The lexicon benefits from both surfaces too.
    hint = arabizi_to_arabic(clean) if lang == "arz" else ""
    classify_text = f"{hint}\n---\n{clean}" if hint and hint != clean else clean

    result, path = classify_with_fallback(lexicon, classifier, classify_text,
                                          title, lang, local=local)

    # The model's own language read is usually right; trust it over the
    # heuristic for mixed texts (schema keeps raw output for audit either way).
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

    if topics is None:
        topics = TopicAssigner()
    if entities is None:
        entities = EntityExtractor()
    topic_list = topics.assign(clean)
    entity_list = entities.extract(clean)
    return (normalized_row, classification_row, lang, path,
            topic_list, entity_list)


def _dialect_from(lang: str) -> str | None:
    if lang == "arz":
        return "gulf"  # v1: Gulf-primary; finer dialect tags are a later pass
    if lang == "ar":
        return "msa"
    return None


async def classify_docs(
    docs: list[dict[str, Any]],
    classifier: GroqClassifier,
    lexicon: LexiconClassifier | None = None,
    *,
    # Serialized: the free tier's token-per-minute window is the binding
    # constraint, not request rate - 2 workers just bursts into 429s.
    workers: int = 1,
    local=None,
) -> list[tuple[dict[str, Any], dict[str, Any] | None, str, str,
               list[dict[str, Any]], list[dict[str, Any]]]]:
    """Classify + enrich a list of raw-doc dicts ({id, text, title}).

    Each result is (normalized_row, classification_row | None, lang, path,
    topics, entities). The lexicon fast path is used when provided (A7) and
    topic/entity enrichment is always zero-token (A8).
    """
    if not docs:
        return []
    if lexicon is None:
        lexicon = LexiconClassifier()
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            loop.run_in_executor(
                pool,
                process_doc,
                d["id"],
                d.get("text") or "",
                d.get("title"),
                lexicon,
                classifier,
                None,
                None,
                local,
            )
            for d in docs
        ]
        return await asyncio.gather(*futures)


async def enrich_docs(
    docs: list[dict[str, Any]],
    *,
    workers: int = 4,
) -> list[tuple[int, list[dict[str, Any]], list[dict[str, Any]]]]:
    """Zero-token enrichment pass over docs that already have classification
    (or never will): returns (doc_id, topics, entities) per doc."""
    if not docs:
        return []
    assigner = TopicAssigner()
    extractor = EntityExtractor()
    loop = asyncio.get_running_loop()

    def _one(d: dict) -> tuple[int, list[dict[str, Any]], list[dict[str, Any]]]:
        clean = clean_text(d.get("text") or "")
        return d["id"], assigner.assign(clean), extractor.extract(clean)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [loop.run_in_executor(pool, _one, d) for d in docs]
        return await asyncio.gather(*futures)
