"""Normalizer (Arabizi -> Arabic) and word-boundary matcher tests."""

from basr.nlp.normalizer import arabizi_to_arabic, clean_text
from basr.nlp.textmatch import has_word


def test_arabizi_digit_mapping():
    out = arabizi_to_arabic("3ashan")
    assert "\u0639" in out  # 3 -> ayn
    assert "\u0634" in out  # sh -> shin


def test_arabizi_7_and_9():
    out = arabizi_to_arabic("7aram 9areeb")
    assert "\u062d" in out  # 7 -> ha
    # 9 -> qaf (Egyptian) or sad (Gulf). ArabiziKit uses Gulf convention.
    assert "\u0642" in out or "\u0635" in out


def test_arabizi_inshallah():
    out = arabizi_to_arabic("inshallah")
    assert "\u0625\u0646 \u0634\u0627\u0621 \u0627\u0644\u0644\u0647" in out or "\u0627\u0646 \u0634\u0627\u0621 \u0627\u0644\u0644\u0647" in out


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
    assert has_word("\u0627\u0644\u0623\u0633\u0639\u0627\u0631 \u063a\u0627\u0644\u064a\u0629", "\u0627\u0644\u0623\u0633\u0639\u0627\u0631")
