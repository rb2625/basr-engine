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

from .langid import detect_language
from .normalizer import clean_text

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


def evaluate() -> dict:
    from ..eval.datasets import items_for_task

    items = items_for_task("sentiment")
    train, test = _split(items)
    model = CharNgramNB()
    model.fit([(it["text"], it["label"]) for it in train])

    overall = {"n": 0, "ok": 0}
    per_lang: dict[str, dict] = {}
    for it in test:
        pred, conf = model.predict(it["text"])
        lang = detect_language(it["text"])
        acc = per_lang.setdefault(lang, {"n": 0, "ok": 0})
        acc["n"] += 1
        overall["n"] += 1
        if pred == it["label"]:
            acc["ok"] += 1
            overall["ok"] += 1

    print("local model v1 (char n-gram NB) - held-out 20%:")
    print(f"  overall: {overall['ok']}/{overall['n']} "
          f"= {overall['ok'] / overall['n']:.3f}")
    for lang in ("ar", "arz", "en"):
        a = per_lang.get(lang)
        if a and a["n"]:
            print(f"  {lang}: {a['ok']}/{a['n']} = {a['ok'] / a['n']:.3f}")

    # Compare with the lexicon on the same test items.
    from .lexicon import LexiconClassifier
    lx = LexiconClassifier()
    lex_ok = sum(
        1 for it in test
        if lx.classify(it["text"], lang=detect_language(it["text"])).sentiment_label
        == it["label"]
    )
    print(f"  lexicon on same split: {lex_ok}/{len(test)} "
          f"= {lex_ok / len(test):.3f}")
    return {"overall": overall["ok"] / overall["n"] if overall["n"] else 0.0,
            "lexicon": lex_ok / len(test) if test else 0.0}


if __name__ == "__main__":
    evaluate()
