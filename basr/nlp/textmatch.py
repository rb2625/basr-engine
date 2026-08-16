"""Shared word matching for the zero-token keyword stages.

The trap this avoids: bare substring matching makes short ASCII tokens like
"ai", "du", "rta" fire inside unrelated words ("Dubai", "daily", "apart").
ASCII and Arabizi words match on word boundaries; multi-word phrases and
Arabic words match as substrings (Arabic clitics like ال/و/ب attach to words,
so a strict boundary would miss الإيجارات hitting إيجارات).
"""

from __future__ import annotations

import re

_WORD_RE_CACHE: dict[str, re.Pattern] = {}


def has_word(text: str, word: str) -> bool:
    """True when ``word`` occurs in ``text`` with sensible boundaries."""
    if " " in word:
        return word in text
    if any("\u0600" <= c <= "\u06FF" for c in word):
        return word in text
    pattern = _WORD_RE_CACHE.get(word)
    if pattern is None:
        pattern = re.compile(rf"\b{re.escape(word)}\b")
        _WORD_RE_CACHE[word] = pattern
    return pattern.search(text) is not None
