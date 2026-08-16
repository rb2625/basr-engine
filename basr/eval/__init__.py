"""BASR eval: labeled datasets + scoring harness (the trust layer)."""

from .datasets import DATASETS, EvalItem, ITEMS, items_for_task
from .harness import compute_metrics, confusion, print_report, run_eval

__all__ = [
    "DATASETS",
    "EvalItem",
    "ITEMS",
    "items_for_task",
    "compute_metrics",
    "confusion",
    "print_report",
    "run_eval",
]
