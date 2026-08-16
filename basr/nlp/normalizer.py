"""Text normalization for the BASR NLP pipeline (pure Python, no deps).

Pipeline order (matches PLAN.md §6.1):

1. ``clean_text`` — HTML unescape + tag strip, URL/email removal, emoji and
   non-word symbol removal, whitespace collapse. This is the canonical
   ``clean_text`` stored in ``normalized_docs``.
2. ``arabizi_to_arabic`` — best-effort transliteration of Arabizi (Arabic
   written in Latin letters, e.g. ``3ashan``, ``wallah``) into Arabic script.
   High-frequency Gulf words are in a dictionary; anything else with Arabizi
   marker characters goes through a conservative character map. The output is
   a *hint* for the classifier, never a replacement — the cleaned original is
   always kept (the v1 LLM understands Arabizi natively).
"""

from __future__ import annotations

import html
import re

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
# Arabizi → Arabic
# ---------------------------------------------------------------------------

# High-frequency Gulf Arabizi words (the ones that carry real meaning in a
# sentiment context). Keyed by the most common spellings seen in the wild.
ARABIZI_MAP: dict[str, str] = {
    # particles / connectors
    "3ashan": "عشان", "3shan": "عشان", "3ashaan": "عشان", "ashan": "عشان",
    "3ala": "على", "3alayh": "عليه", "3an": "عن", "3and": "عند", "3ind": "عند",
    "3adi": "عادي", "3ajab": "عجب", "3ibara": "عبارة",
    "ma3a": "مع", "ma3": "مع", "min": "من", "il": "إلى", "fi": "في",
    "wala": "ولا", "aw": "أو", "bas": "بس", "bass": "بس",
    # affirmations / fillers
    "wallah": "والله", "wallahi": "والله", "walah": "والله",
    "inshallah": "إن شاء الله", "inshaallah": "إن شاء الله", "insha'allah": "إن شاء الله",
    "yalla": "يلا", "yallah": "يلا",
    "khalas": "خلاص", "khalaas": "خلاص", "khelas": "خلاص",
    "shukran": "شكرا", "shokran": "شكرا", "thx": "شكرا",
    "afwan": "عفوا", "mabrouk": "مبروك", "mubarak": "مبارك",
    "allah": "الله", "ya": "يا",
    # everyday verbs / adjectives
    "mafi": "مافي", "mafee": "مافي", "mafish": "مافيش",
    "lazem": "لازم", "lazim": "لازم", "lazm": "لازم",
    "zain": "زين", "zein": "زين", "zayn": "زين",
    "7elou": "حلو", "7elo": "حلو", "7elwa": "حلوة", "7ilw": "حلو",
    "7aram": "حرام", "7alal": "حلال",
    "khara": "خرا", "5ara": "خرا",
    "yani": "يعني", "ya3ni": "يعني", "yaani": "يعني",
    "shinu": "شو", "shu": "شو", "shino": "شو",
    "wain": "وين", "ween": "وين",
    "hal": "هذا", "hatha": "هذا", "haza": "هذا",
    "shlon": "شلون", "shlonk": "شلونك",
    "akid": "أكيد", "akked": "أكيد", "akeed": "أكيد",
    "mumkin": "ممكن", "momken": "ممكن",
    "zaid": "زيادة", "zayid": "زيادة", "zyada": "زيادة",
    "wa7ed": "واحد", "wahed": "واحد", "7ad": "حد",
    "kill": "كل", "kull": "كل",
    "arid": "أريد", "ared": "أريد", "abga": "أبي", "abigha": "أبي",
    "aywa": "أيوه", "na3am": "نعم", "la": "لا",
    "habibi": "حبيبي", "7abibi": "حبيبي", "habib": "حبيب",
    "baba": "بابا", "mama": "ماما", "ukhti": "أختي", "akhi": "أخي",
    "kelma": "كلمة", "kalam": "كلام",
    "mashkila": "مشكلة", "moshkila": "مشكلة",
    "ta3al": "تعال", "taal": "تعال", "ruh": "روح",
    "7aga": "حاجة", "haga": "حاجة",
    "kwayes": "كويس", "kuwayyis": "كويس", "kwayis": "كويس",
    "mish": "مش", "maish": "مش",
    "b3d": "بعد", "ba3d": "بعد",
    "7atta": "حتى", "hatta": "حتى",
    "meshwar": "مشوار", "mashwar": "مشوار",
    "3umr": "عمر", "3omr": "عمر",
    "wajid": "واجد", "wayid": "وايد", "kathir": "كثير",
    "gher": "غير", "ghair": "غير",
    "shway": "شوي", "shwaya": "شوية",
    "3esh": "عيش", "3aysh": "عايش",
    "wala shay": "ولا شيء", "wala shi": "ولا شي",
    "7ayati": "حياتي", "7ayat": "حياة",
    "mabrook": "مبروك",
    "ya3ni": "يعني",
    "3asr": "عصر", "3asab": "عصب",
}

# Character-level fallback: Arabizi marker digits → Arabic letters, applied
# only to words that contain markers (so English words are never touched).
_CHAR_MAP = {
    "2": "أ",  # also used for ء/إ — 'أ' is the safest common form
    "3": "ع",
    "5": "خ",
    "6": "ط",
    "7": "ح",
    "8": "ق",  # Egyptian usage; rare in Gulf but seen
    "9": "ق",
    "'": "ء",
    "`": "ء",
}

# Digraphs are matched before single chars, longest first.
_DIGRAPH_MAP = {
    "kh": "خ", "sh": "ش", "th": "ث", "dh": "ذ", "gh": "غ",
    "aa": "ا", "ee": "ي", "oo": "و", "ei": "ي", "ou": "و", "ay": "ي",
}

_MARKER_RE = re.compile(r"[2356789'`]")
_VOWELISH_DIGRAPHS = ("aa", "ee", "oo", "ei", "ou", "ay")


def _transliterate_word(word: str) -> str:
    """Best-effort word-level transliteration. Conservative: only rewrites
    characters that have a confident mapping and keeps the rest as-is."""
    if word in ARABIZI_MAP:
        return ARABIZI_MAP[word]

    # Only attempt character rewriting when the word actually carries Arabizi
    # markers (digit-letters or apostrophes) — protects English words like
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


_EDGE_PUNCT = ". ,!?;:\"'()[]"


def arabizi_to_arabic(text: str) -> str:
    """Transliterate Arabizi text to Arabic script (best effort).

    Returns the input unchanged when no Arabizi markers are present. When a
    text is fully Arabizi the result is a readable Arabic hint; for mixed text
    only the Arabizi words are rewritten.
    """
    if not text:
        return ""
    words = text.split()
    out = []
    for word in words:
        stripped = word.strip(_EDGE_PUNCT)
        if not stripped:
            out.append(word)
            continue
        # Leading and trailing punctuation are computed independently so a
        # word like "kteer," keeps its comma exactly once.
        head_len = len(word) - len(word.lstrip(_EDGE_PUNCT))
        tail_len = len(word) - len(word.rstrip(_EDGE_PUNCT))
        head = word[:head_len]
        tail = word[len(word) - tail_len:] if tail_len else ""
        out.append(head + _transliterate_word(stripped) + tail)
    return " ".join(out)


def normalize(text: str | None) -> str:
    """Full normalization pass → the canonical clean text."""
    return clean_text(text)
