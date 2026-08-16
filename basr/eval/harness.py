"""Eval harness - the platform's own scorecard (PLAN.md sec 6.7, sec 12.2).

Every classifier is scored on the labeled eval sets; scores are meant to be
published on the dashboard ("measured, not vibes"). This module:

1. runs the live classifier over labeled items,
2. computes accuracy + per-class precision/recall/F1 + macro averages,
3. prints a compact table + confusion matrix,
4. returns the metrics dict for optional logging into ``eval_runs``.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable

from ..nlp.classifier import GroqClassifier


def _f1(p: float, r: float) -> float:
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def compute_metrics(y_true: list[str], y_pred: list[str]) -> dict:
    """Accuracy + per-class + macro precision/recall/F1."""
    labels = sorted(set(y_true) | set(y_pred))
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / len(y_true) if y_true else 0.0

    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    for t, p in zip(y_true, y_pred):
        if t == p:
            tp[t] += 1
        else:
            fp[p] += 1
            fn[t] += 1

    per_class = {}
    for label in labels:
        precision = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) else 0.0
        recall = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) else 0.0
        per_class[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(_f1(precision, recall), 4),
            "support": tp[label] + fn[label],
        }

    n = len(labels)
    macro_p = sum(v["precision"] for v in per_class.values()) / n if n else 0.0
    macro_r = sum(v["recall"] for v in per_class.values()) / n if n else 0.0
    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(_f1(macro_p, macro_r), 4),
        "per_class": per_class,
        "n": len(y_true),
    }


def confusion(y_true: list[str], y_pred: list[str]) -> dict[str, dict[str, int]]:
    labels = sorted(set(y_true) | set(y_pred))
    mat = {t: {p: 0 for p in labels} for t in labels}
    for t, p in zip(y_true, y_pred):
        mat[t][p] += 1
    return mat


def run_eval(
    classifier: GroqClassifier,
    items: list[dict],
    task: str,
    *,
    extract: Callable[[object], str],
) -> dict:
    """Classify ``items`` and score predictions against their labels.

    ``extract`` maps a ClassifyResult to the predicted label for this task
    (e.g. ``lambda r: r.sentiment_label``).
    """
    y_true: list[str] = []
    y_pred: list[str] = []
    failures = 0
    for i, item in enumerate(items, 1):
        result = classifier.classify(item["text"])
        expected = item["label"]
        predicted = extract(result)
        y_true.append(expected)
        y_pred.append(predicted)
        if predicted != expected:
            print(f"    [{i}/{len(items)}] MISMATCH expected={expected!r} "
                  f"got={predicted!r} | {item['text'][:70]}")
        if result.confidence == 0.0:
            failures += 1
    metrics = compute_metrics(y_true, y_pred)
    metrics["task"] = task
    metrics["confusion"] = confusion(y_true, y_pred)
    metrics["failures"] = failures
    return metrics


def print_report(title: str, metrics: dict) -> None:
    print(f"\n  {title}")
    print(f"  accuracy={metrics['accuracy']:.3f}  macro-P={metrics['macro_precision']:.3f}  "
          f"macro-R={metrics['macro_recall']:.3f}  macro-F1={metrics['macro_f1']:.3f}  "
          f"n={metrics['n']}")
    rows = sorted(metrics["per_class"].items())
    if rows:
        width = max(len(k) for k, _ in rows)
        for label, v in rows:
            print(f"    {label:<{width}}  P={v['precision']:.3f}  R={v['recall']:.3f}  "
                  f"F1={v['f1']:.3f}  n={v['support']}")
    conf = metrics["confusion"]
    labels = sorted(conf)
    if labels:
        print("    confusion (rows=true, cols=pred):")
        print("      " + " ".join(f"{l[:8]:>8}" for l in labels))
        for t in labels:
            row = " ".join(f"{conf[t][p]:>8}" for p in labels)
            print(f"      {t[:8]:<6} {row}")
    if metrics.get("failures"):
        print(f"    [!] {metrics['failures']} failed calls (confidence 0)")
