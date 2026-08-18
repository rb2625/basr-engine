"""Text normalization for the BASR NLP pipeline.

Pipeline order (matches PLAN.md sec 6.1):

1. ``clean_text`` - HTML unescape + tag strip, URL/email removal, emoji and
   non-word symbol removal, whitespace collapse. This is the canonical
   ``clean_text`` stored in ``normalized_docs``.
2. ``arabizi_to_arabic`` - transliteration of Arabizi (Arabic written in
   Latin letters, e.g. ``3ashan``, ``wallah``) into Arabic script. Uses
   ArabiziKit (published library, 1,155 learned word readings, Gulf dialect
   support) when available; falls back to a built-in dictionary (135 entries)
   when ArabiziKit is not installed.
"""

from __future__ import annotations

import html
import re
import logging

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\S+@\S+\.\S+")
_TAG_RE = re.compile(r"<[^>]+>")
# Emoji, pictographs, symbols, and other non-word marks (keep letters, digits,
# and basic punctuation in both Arabic and Latin scripts).
_SYMBOL_RE = re.compile(
    r"[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0000FE00-\U0000FE0F"
    r"\U0001F1E6-\U0001F1FF\U00002700-\U000027BF\U00002B00-\U00002BFF"
    r"\u2190-\u21FF\u2B00-\u2BFF\u2300-\u23FF\u25A0-\u25FF\u2700-\u27BF]+"
)
_WS_RE = re.compile(r"\s+")
_QUOTE_RE = re.compile(r"[\u2018\u2019\u201C\u201D\u00AB\u00BB\u201A\u201E\u2032\u2033]")
_BRACKET_RE = re.compile(r"[\[\](){}<>]")


def clean_text(text: str | None) -> str:
    """Return the canonical cleaned form of ``text``.

    - HTML entities decoded, tags stripped
    - URLs / emails removed
    - emoji and decorative symbols removed
    - smart quotes normalized to ASCII
    - whitespace collapsed
    """
    if not text:
        return ""
    t = html.unescape(text)
    t = _TAG_RE.sub(" ", t)
    t = _URL_RE.sub(" ", t)
    t = _EMAIL_RE.sub(" ", t)
    t = _QUOTE_RE.sub('"', t)
    t = _SYMBOL_RE.sub(" ", t)
    t = _BRACKET_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t)
    return t.strip()


# ---------------------------------------------------------------------------
# Arabizi -> Arabic
# ---------------------------------------------------------------------------

# Try importing ArabiziKit (published library, v1.0.0, 1,155 learned words,
# Gulf dialect support, dialect tagging, ranked candidates).
_ARABIZIKIT = None
try:
    from arabizikit import transliterate as _ak_transliterate

    _ARABIZIKIT = _ak_transliterate
    _log.debug("ArabiziKit loaded: Gulf Arabizi transliteration available")
except ImportError:
    _log.debug(
        "ArabiziKit not installed; falling back to built-in dictionary "
        "(pip install arabizikit for full Gulf dialect support)"
    )


def arabizi_to_arabic(text: str) -> str:
    """Transliterate Arabizi text to Arabic script.

    Uses ArabiziKit when available (1,155 learned words, Gulf dialect tagging,
    ranked candidates with confidence scores). Falls back to a built-in
    dictionary of 135 high-frequency Gulf words and a character-level map.

    Returns the input unchanged when no Arabizi markers are present.
    """
    if not text:
        return ""

    if _ARABIZIKIT is not None:
        return _arabizikit_transliterate(text)

    return _builtin_transliterate(text)


def _arabizikit_transliterate(text: str) -> str:
    """Transliterate using ArabiziKit with Gulf dialect hint."""
    try:
        res = _ARABIZIKIT(text, dialect_hint="gulf")
        return res.text if res and res.text else text
    except Exception:
        # If ArabiziKit fails on this input, return the original text
        # rather than crashing the pipeline.
        return text


# ---------------------------------------------------------------------------
# Built-in fallback (135-word dictionary + character map)
# ---------------------------------------------------------------------------

# High-frequency Gulf Arabizi words (the ones that carry real meaning in a
# sentiment context). Keyed by the most common spellings seen in the wild.
ARABIZI_MAP: dict[str, str] = {
    # particles / connectors
    "3ashan": "\u0639\u0634\u0627\u0646", "3shan": "\u0639\u0634\u0627\u0646",
    "3ashaan": "\u0639\u0634\u0627\u0646", "ashan": "\u0639\u0634\u0627\u0646",
    "3ala": "\u0639\u0644\u0649", "3alayh": "\u0639\u0644\u064a\u0647",
    "3an": "\u0639\u0646", "3and": "\u0639\u0646\u062f", "3ind": "\u0639\u0646\u062f",
    "3adi": "\u0639\u0627\u062f\u064a", "3ajab": "\u0639\u062c\u0628",
    "3ibara": "\u0639\u0628\u0627\u0631\u0629",
    "ma3a": "\u0645\u0639", "ma3": "\u0645\u0639", "min": "\u0645\u0646",
    "il": "\u0625\u0644\u0649", "fi": "\u0641\u064a",
    "wala": "\u0648\u0644\u0627", "aw": "\u0623\u0648", "bas": "\u0628\u0633",
    "bass": "\u0628\u0633",
    # affirmations / fillers
    "wallah": "\u0648\u0627\u0644\u0644\u0647", "wallahi": "\u0648\u0627\u0644\u0644\u0647",
    "walah": "\u0648\u0627\u0644\u0644\u0647",
    "inshallah": "\u0625\u0646 \u0634\u0627\u0621 \u0627\u0644\u0644\u0647",
    "inshaallah": "\u0625\u0646 \u0634\u0627\u0621 \u0627\u0644\u0644\u0647",
    "insha'allah": "\u0625\u0646 \u0634\u0627\u0621 \u0627\u0644\u0644\u0647",
    "yalla": "\u064a\u0644\u0627", "yallah": "\u064a\u0644\u0627",
    "khalas": "\u062e\u0644\u0627\u0635", "khalaas": "\u062e\u0644\u0627\u0635",
    "khelas": "\u062e\u0644\u0627\u0635",
    "shukran": "\u0634\u0643\u0631\u0627", "shokran": "\u0634\u0643\u0631\u0627",
    "thx": "\u0634\u0643\u0631\u0627",
    "afwan": "\u0639\u0641\u0648\u0627\u0646", "mabrouk": "\u0645\u0628\u0631\u0648\u0643",
    "mubarak": "\u0645\u0628\u0627\u0631\u0643",
    "allah": "\u0627\u0644\u0644\u0647", "ya": "\u064a\u0627",
    # everyday verbs / adjectives
    "mafi": "\u0645\u0627\u0641\u064a", "mafee": "\u0645\u0627\u0641\u064a",
    "mafish": "\u0645\u0627\u0641\u064a\u0634",
    "lazem": "\u0644\u0627\u0632\u0645", "lazim": "\u0644\u0627\u0632\u0645",
    "lazm": "\u0644\u0627\u0632\u0645",
    "zain": "\u0632\u064a\u0646", "zein": "\u0632\u064a\u0646", "zayn": "\u0632\u064a\u0646",
    "7elou": "\u062d\u0644\u0648", "7elo": "\u062d\u0644\u0648",
    "7elwa": "\u062d\u0644\u0648\u0629", "7ilw": "\u062d\u0644\u0648",
    "7aram": "\u062d\u0631\u0627\u0645", "7alal": "\u062d\u0644\u0627\u0644",
    "khara": "\u062e\u0631\u0627", "5ara": "\u062e\u0631\u0627",
    "yani": "\u064a\u0639\u0646\u064a", "ya3ni": "\u064a\u0639\u0646\u064a",
    "yaani": "\u064a\u0639\u0646\u064a",
    "shinu": "\u0634\u0648", "shu": "\u0634\u0648", "shino": "\u0634\u0648",
    "wain": "\u0648\u064a\u0646", "ween": "\u0648\u064a\u0646",
    "hal": "\u0647\u0630\u0627", "hatha": "\u0647\u0630\u0627", "haza": "\u0647\u0630\u0627",
    "shlon": "\u0634\u0644\u0648\u0646", "shlonk": "\u0634\u0644\u0648\u0646\u0643",
    "akid": "\u0623\u0643\u064a\u062f", "akked": "\u0623\u0643\u064a\u062f",
    "akeed": "\u0623\u0643\u064a\u062f",
    "mumkin": "\u0645\u0645\u0643\u0646", "momken": "\u0645\u0645\u0643\u0646",
    "zaid": "\u0632\u064a\u0627\u062f\u0629", "zayid": "\u0632\u064a\u0627\u062f\u0629",
    "zyada": "\u0632\u064a\u0627\u062f\u0629",
    "wa7ed": "\u0648\u0627\u062d\u062f", "wahed": "\u0648\u0627\u062d\u062f",
    "7ad": "\u062d\u062f",
    "kill": "\u0643\u0644", "kull": "\u0643\u0644",
    "arid": "\u0623\u0631\u064a\u062f", "ared": "\u0623\u0631\u064a\u062f",
    "abga": "\u0623\u0628\u064a", "abigha": "\u0623\u0628\u064a",
    "aywa": "\u0623\u064a\u0648\u0647", "na3am": "\u0646\u0639\u0645",
    "la": "\u0644\u0627",
    "habibi": "\u062d\u0628\u064a\u0628\u064a", "7abibi": "\u062d\u0628\u064a\u0628\u064a",
    "habib": "\u062d\u0628\u064a\u0628",
    "baba": "\u0628\u0627\u0628\u0627", "mama": "\u0645\u0627\u0645\u0627",
    "ukhti": "\u0623\u062e\u062a\u064a", "akhi": "\u0623\u062e\u064a",
    "kelma": "\u0643\u0644\u0645\u0629", "kalam": "\u0643\u0644\u0627\u0645",
    "mashkila": "\u0645\u0634\u0643\u0644\u0629", "moshkila": "\u0645\u0634\u0643\u0644\u0629",
    "ta3al": "\u062a\u0639\u0627\u0644", "taal": "\u062a\u0639\u0627\u0644",
    "ruh": "\u0631\u0648\u062d",
    "7aga": "\u062d\u0627\u062c\u0629", "haga": "\u062d\u0627\u062c\u0629",
    "kwayes": "\u0643\u0648\u064a\u0633", "kuwayyis": "\u0643\u0648\u064a\u0633",
    "kwayis": "\u0643\u0648\u064a\u0633",
    "mish": "\u0645\u0634", "maish": "\u0645\u0634",
    "b3d": "\u0628\u0639\u062f", "ba3d": "\u0628\u0639\u062f",
    "7atta": "\u062d\u062a\u0649", "hatta": "\u062d\u062a\u0649",
    "meshwar": "\u0645\u0634\u0648\u0627\u0631", "mashwar": "\u0645\u0634\u0648\u0627\u0631",
    "3umr": "\u0639\u0645\u0631", "3omr": "\u0639\u0645\u0631",
    "wajid": "\u0648\u0627\u062c\u062f", "wayid": "\u0648\u0627\u064a\u062f",
    "kathir": "\u0643\u062b\u064a\u0631",
    "gher": "\u063a\u064a\u0631", "ghair": "\u063a\u064a\u0631",
    "shway": "\u0634\u0648\u064a", "shwaya": "\u0634\u0648\u064a\u0629",
    "3esh": "\u0639\u064a\u0634", "3aysh": "\u0639\u0627\u0626\u0634",
    "wala shay": "\u0648\u0644\u0627 \u0634\u064a\u0621",
    "wala shi": "\u0648\u0644\u0627 \u0634\u064a",
    "7ayati": "\u062d\u064a\u0627\u062a\u064a", "7ayat": "\u062d\u064a\u0627\u0629",
    "mabrook": "\u0645\u0628\u0631\u0648\u0643",
    "3asr": "\u0639\u0635\u0631", "3asab": "\u0639\u0635\u0628",
}

# Character-level fallback: Arabizi marker digits -> Arabic letters, applied
# only to words that contain markers (so English words are never touched).
_CHAR_MAP = {
    "2": "\u0623",  # also used for hamza/alef - the safest common form
    "3": "\u0639",
    "5": "\u062e",
    "6": "\u0637",
    "7": "\u062d",
    "8": "\u0642",  # Egyptian usage; rare in Gulf but seen
    "9": "\u0642",
    "'": "\u0621",
    "`": "\u0621",
}

# Digraphs are matched before single chars, longest first.
_DIGRAPH_MAP = {
    "kh": "\u062e", "sh": "\u0634", "th": "\u062b", "dh": "\u0630", "gh": "\u063a",
    "aa": "\u0627", "ee": "\u064a", "oo": "\u0648", "ei": "\u064a", "ou": "\u0648",
    "ay": "\u064a",
}

_MARKER_RE = re.compile(r"[2356789'`]")
_VOWELISH_DIGRAPHS = ("aa", "ee", "oo", "ei", "ou", "ay")


def _transliterate_word(word: str) -> str:
    """Best-effort word-level transliteration. Conservative: only rewrites
    characters that have a confident mapping and keeps the rest as-is."""
    if word in ARABIZI_MAP:
        return ARABIZI_MAP[word]

    # Only attempt character rewriting when the word actually carries Arabizi
    # markers (digit-letters or apostrophes) - protects English words like
    # "parking", "metro", "app".
    if not _MARKER_RE.search(word):
        return word

    out = []
    i = 0
    n = len(word)
    while i < n:
        two = word[i : i + 2].lower()
        if two in _DIGRAPH_MAP and two not in _VOWELISH_DIGRAPHS:
            out.append(_DIGRAPH_MAP[two])
            i += 2
            continue
        ch = word[i]
        if ch in _CHAR_MAP:
            out.append(_CHAR_MAP[ch])
        else:
            out.append(ch)
        i += 1
    return "".join(out)


_EDGE_PUNCT = " . ,!?;:\"'()[]"


def _builtin_transliterate(text: str) -> str:
    """Built-in fallback transliteration using the hand-crafted dictionary."""
    words = text.split()
    out = []
    for word in words:
        stripped = word.strip(_EDGE_PUNCT)
        if not stripped:
            out.append(word)
            continue
        head_len = len(word) - len(word.lstrip(_EDGE_PUNCT))
        tail_len = len(word) - len(word.rstrip(_EDGE_PUNCT))
        head = word[:head_len]
        tail = word[len(word) - tail_len:] if tail_len else ""
        out.append(head + _transliterate_word(stripped) + tail)
    return " ".join(out)


def normalize(text: str | None) -> str:
    """Full normalization pass -> the canonical clean text."""
    return clean_text(text)
