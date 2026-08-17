"""Lexicon fast-path guard tests (Amendment A10 rules).

The lexicon is the zero-token layer: it should catch clear cases with high
confidence and DEFER the ambiguous ones (sarcasm, weather/entertainment
factuals, economic events it cannot price) to the LLM by returning low
confidence (< ROUTE_CONFIDENCE)."""

from basr.nlp.lexicon import LexiconClassifier, ROUTE_CONFIDENCE

lx = LexiconClassifier()


def _defer(text: str, lang: str = "en") -> bool:
    r = lx.classify(text, lang=lang)
    return r.confidence < ROUTE_CONFIDENCE


def test_clear_cost_complaint_is_kept():
    r = lx.classify("Rent increase next month, landlords are greedy",
                    lang="en")
    assert r.confidence >= ROUTE_CONFIDENCE
    assert r.signal_type == "stress"
    assert r.sentiment_label == "negative"


def test_sarcastic_rent_praise_defers():
    assert _defer("Great, another rent increase. Just what we needed.")


def test_sarcastic_salik_praise_defers():
    assert _defer("Salik charges are the best thing ever")


def test_weather_factual_defers():
    assert _defer("The weather is nice today")


def test_economic_event_fuel_defers():
    # The lexicon cannot price this; the LLM must see it.
    assert _defer("fuel price increase next month")


def test_salary_growth_defers():
    assert _defer("Salaries in the banking sector are rising")


def test_never_raises_on_garbage():
    r = lx.classify(None, lang=None)  # type: ignore[arg-type]
    assert r.confidence == 0.0
