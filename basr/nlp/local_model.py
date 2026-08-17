"""Fine-tuned Gulf-Arabic model v1 (Phase 6, A16; the F1 unlock, Gate 2).

A local, zero-token sentiment classifier trained on the LABELED eval items
(500 sentiment texts: ar / arz / en). Pure stdlib (no sklearn, no GPU) so it
runs anywhere, including CI and the cron, with no API cost.

This is the honest v1 baseline of the plan's "fine-tuned Gulf Arabic model":
it measures what a local model can do before a real transformer fine-tune
(CAMeL/AraBERT on free Colab compute) becomes the upgrade. If it beats the
lexicon on the held-out set it becomes a second fast path before the LLM.

Features: character n-grams (2-4) + word tokens over the cleaned text.
Model: multinomial naive Bayes with additive smoothing. Confidence is the
posterior margin between the top two classes.

INTEGRITY CONSTRAINT: it is trained ON the eval items, so it must NOT be
wired into production routing until an eval v2 (fresh items, never seen in
training) exists - otherwise the hybrid eval would be train-on-test and its
scores meaningless (the trust layer dies). The plan's path: expand the
labeled set (eval v2, Gate 2), then this model becomes a second fast path
before the LLM.
"""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict

from .classifier import ClassifyResult
from .langid import detect_language
from .normalizer import clean_text

LOCAL_VERSION = "basr-local-ngram-v1"

# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------


def extract_features(text: str) -> Counter:
    """Character n-grams (2-4) + words, lowercased, counts as a multiset."""
    clean = clean_text(text or "").lower()
    feats: Counter = Counter()
    words = [w for w in clean.split() if w]
    for w in words:
        feats[w] += 1
        for n in (2, 3, 4):
            if len(w) >= n:
                for i in range(len(w) - n + 1):
                    feats[f"^{w[i:i+n]}$"] += 1
    return feats


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class CharNgramNB:
    """Multinomial naive Bayes over character n-grams + words."""

    def __init__(self, alpha: float = 0.3) -> None:
        self.alpha = alpha
        self.classes: list[str] = []
        self.priors: dict[str, float] = {}
        self.log_probs: dict[str, dict[str, float]] = {}
        self.vocab: set[str] = set()

    def fit(self, items: list[tuple[str, str]]) -> None:
        """items: [(text, label)]."""
        by_class: dict[str, list[Counter]] = defaultdict(list)
        for text, label in items:
            by_class[label].append(extract_features(text))
        self.classes = sorted(by_class)
        total = sum(len(v) for v in by_class.values())
        self.priors = {c: len(v) / total for c, v in by_class.items()}
        for c, feats_list in by_class.items():
            counts: Counter = Counter()
            for feats in feats_list:
                counts.update(feats)
            self.vocab |= set(counts)
        vocab_size = len(self.vocab)
        for c in self.classes:
            counts = Counter()
            for feats in by_class[c]:
                counts.update(feats)
            denom = sum(counts.values()) + self.alpha * vocab_size
            self.log_probs[c] = {
                f: math.log((counts[f] + self.alpha) / denom) for f in self.vocab
            }

    def predict(self, text: str) -> tuple[str, float]:
        """Return (label, confidence) where confidence is the posterior margin
        in [0, 1] between the top two classes."""
        feats = extract_features(text)
        scores = {c: math.log(self.priors[c]) for c in self.classes}
        for f, n in feats.items():
            if f not in self.vocab:
                continue
            for c in self.classes:
                scores[c] += n * self.log_probs[c][f]
        ranked = sorted(scores, key=lambda c: -scores[c])
        top, second = ranked[0], ranked[1]
        # Softmax-like margin over the top two log scores.
        d = scores[top] - scores[second]
        margin = 1.0 / (1.0 + math.exp(-d))
        return top, round(margin, 3)


# ---------------------------------------------------------------------------
# Eval
# ---------------------------------------------------------------------------


def _split(items: list[dict], seed: int = 7) -> tuple[list, list]:
    """Stratified-by-language 80/20 split (deterministic)."""
    rng = random.Random(seed)
    by_lang: dict[str, list] = defaultdict(list)
    for it in items:
        by_lang[detect_language(it["text"])].append(it)
    train, test = [], []
    for group in by_lang.values():
        rng.shuffle(group)
        cut = max(1, int(len(group) * 0.8))
        train.extend(group[:cut])
        test.extend(group[cut:])
    return train, test


def train_local() -> tuple[CharNgramNB, CharNgramNB]:
    """Train the sentiment + signal models on the FULL v1 eval items.

    This is the production model used by LocalModelClassifier. It trains on
    the v1 set; its honest measurement is eval v2 (fresh items).
    """
    from ..eval.datasets import items_for_task

    sent_model = CharNgramNB()
    sent_model.fit([(it["text"], it["label"]) for it in items_for_task("sentiment")])
    sig_model = CharNgramNB()
    sig_model.fit([(it["text"], it["label"]) for it in items_for_task("signal")])
    return sent_model, sig_model


class LocalModelClassifier:
    """Production wrapper: sentiment + signal from the local models.

    classify() returns a ClassifyResult with both labels and a confidence of
    the weaker of the two task margins, so the hybrid router can decide
    whether this result is trustworthy. Zero tokens, zero network.
    """

    def __init__(self, models: tuple[CharNgramNB, CharNgramNB] | None = None) -> None:
        self._sent, self._sig = models if models is not None else train_local()

    def classify(
        self, text: str, *, title: str | None = None, lang: str | None = None
    ) -> ClassifyResult:
        sent_label, sent_conf = self._sent.predict(text)
        sig_label, sig_conf = self._sig.predict(text)
        confidence = min(sent_conf, sig_conf)
        return ClassifyResult(
            sentiment_label=sent_label,
            signal_type=sig_label,
            confidence=confidence,
            detected_language=lang or detect_language(text),
            raw={"path": "local", "sentiment_conf": sent_conf,
                 "signal_conf": sig_conf},
            model_version=LOCAL_VERSION,
        )


def evaluate() -> dict:
    """Train on v1, measure on v2 (fresh items) - both tasks."""
    from ..eval.datasets_v2 import items_for_task_v2
    from .lexicon import LexiconClassifier

    sent_model, sig_model = train_local()
    local = LocalModelClassifier((sent_model, sig_model))
    lx = LexiconClassifier()

    for task in ("sentiment", "signal"):
        items = items_for_task_v2(task)
        local_ok = 0
        lex_ok = 0
        per_lang: dict[str, dict] = {}
        for it in items:
            lang = detect_language(it["text"])
            r = local.classify(it["text"], lang=lang)
            pred = r.sentiment_label if task == "sentiment" else r.signal_type
            if pred == it["label"]:
                local_ok += 1
            acc = per_lang.setdefault(lang, {"n": 0, "ok": 0})
            acc["n"] += 1
            if pred == it["label"]:
                acc["ok"] += 1
            lr = lx.classify(it["text"], lang=lang)
            lex_pred = lr.sentiment_label if task == "sentiment" else lr.signal_type
            if lex_pred == it["label"]:
                lex_ok += 1

        print(f"eval v2 - {task} ({len(items)} fresh items):")
        print(f"  local: {local_ok}/{len(items)} = {local_ok / len(items):.3f}")
        print(f"  lexicon: {lex_ok}/{len(items)} = {lex_ok / len(items):.3f}")
        for lang in ("ar", "arz", "en"):
            a = per_lang.get(lang)
            if a and a["n"]:
                print(f"    {lang}: {a['ok']}/{a['n']} = {a['ok'] / a['n']:.3f}")
    return {}


if __name__ == "__main__":
    evaluate()
