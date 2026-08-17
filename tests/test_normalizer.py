"""Normalizer (Arabizi -> Arabic) and word-boundary matcher tests."""

from basr.nlp.normalizer import arabizi_to_arabic, clean_text
from basr.nlp.textmatch import has_word


def test_arabizi_digit_mapping():
    out = arabizi_to_arabic("3ashan")
    assert "ع" in out  # 3 -> ع
    assert "ش" in out  # sh -> ش


def test_arabizi_7_and_9():
    out = arabizi_to_arabic("7aram 9areeb")
    assert "ح" in out  # 7 -> ح
    assert "ق" in out  # 9 -> ق


def test_arabizi_inshallah():
    out = arabizi_to_arabic("inshallah")
    assert "إن شاء الله" in out or "ان شاء الله" in out


def test_arabizi_empty_and_none():
    assert arabizi_to_arabic("") == ""
    assert arabizi_to_arabic(None) == ""


def test_clean_text_strips_whitespace():
    # clean_text strips whitespace; lowercasing happens inside the matchers.
    assert clean_text("  Hello WORLD!!  ") == "Hello WORLD!!"


def test_has_word_boundaries():
    assert not has_word("dubai", "ai")      # ai inside dubai: no match
    assert not has_word("daily", "ai")
    assert not has_word("apart", "rta")     # rta inside apart: no match
    assert not has_word("renters", "rent")  # plural boundary respected
    assert has_word("rent increase", "rent")
    assert has_word("rta is closed", "rta")


def test_has_word_arabic():
    assert has_word("الأسعار غالية", "الأسعار")
