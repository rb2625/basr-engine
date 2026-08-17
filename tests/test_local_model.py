"""Local model + eval v2 integrity tests (Phase 6, A17)."""

from basr.eval.datasets import ITEMS
from basr.eval.datasets_v2 import ITEMS_V2
from basr.nlp.local_model import CharNgramNB, LocalModelClassifier, train_local


def test_v2_has_no_exact_overlap_with_v1():
    """The local model trains on v1; v2 must be fresh or the eval is
    train-on-test and its scores are meaningless (the trust layer dies)."""
    v1 = {i.text for i in ITEMS}
    overlap = [i.text for i in ITEMS_V2 if i.text in v1]
    assert not overlap


def test_v2_has_all_three_languages():
    langs = {i.lang for i in ITEMS_V2}
    assert {"ar", "arz", "en"} <= langs
    assert len(ITEMS_V2) >= 120


def test_local_model_trains_and_predicts():
    model = CharNgramNB()
    model.fit([("this is great news", "positive"),
               ("this is terrible news", "negative"),
               ("nothing special happened", "neutral")])
    label, conf = model.predict("really great news today")
    assert label == "positive"
    assert 0.0 <= conf <= 1.0


def test_local_classifier_wrapper_both_tasks():
    clf = LocalModelClassifier()
    r = clf.classify("الأسعار غالية أوي في الفترة دي")
    assert r.sentiment_label in ("positive", "negative", "neutral", "mixed")
    assert r.signal_type in ("stress", "closure", "opportunity", "neutral")
    assert r.confidence >= 0.0
    assert r.model_version.startswith("basr-local-")


def test_train_local_returns_two_models():
    sent, sig = train_local()
    assert len(sent.classes) >= 3
    assert len(sig.classes) >= 3
