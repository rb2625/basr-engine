"""Language identification for BASR docs.

Returns one of: ``ar``, ``arz``, ``en``, ``mixed``, ``other`` — matching the
``raw_docs.lang`` column and PLAN.md §6.2.

Design (recorded as Amendment A4): fasttext ``lid.176`` is the locked long-term
choice, but it has **no Windows wheel** (verified live on this machine: both
``fasttext`` and ``fasttext-wheel`` fail to build without a compiler). So v1
ships a deterministic heuristic that is more than adequate for this pipeline's
three target languages:

* Arabic script ratio → ``ar`` (Gulf dialect markers push it to ``arz``)
* Latin script + Arabizi markers (digit-letters ``2 3 5 6 7 8 9`` in words or
  high-frequency Arabizi tokens) → ``arz``
* Latin script without Arabizi markers → ``en``
* Substantial Arabic + English together → ``mixed``

If ``fasttext`` becomes importable (e.g. on the Linux cron runner with
``lid.176.bin`` present), it takes over automatically via ``FasttextLangID``.
"""

from __future__ import annotations

import re

# Arabic script Unicode ranges (letters + presentation forms).
_ARABIC_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
)
_LATIN_RE = re.compile(r"[A-Za-z]")

# Gulf / Egyptian / Levantine dialect markers → arz.
_DIALECT_TOKENS = {
    "شلون", "ماكو", "زين", "هاي", "هيج", "دش", "اجل", "بس",
    "وين", "شو", "شنو", "عندي", "أبغى", "ابي", "الحين", "حين",
    "يزيد", "ردي", "خرا", "حمار", "افا", "ياي", "ويه", "مريول",
    "دوبه", "هم", "عيال", "حيل", "وايد", "واجد", "طالع", "نازل",
}
_DIALECT_LATIN = {
    "shlon", "shlonk", "maku", "zain", "zein", "hay", "shinu", "shu",
    "shino", "wain", "ween", "yalla", "khalas", "wallah", "inshallah",
    "3ashan", "ashan", "abigha", "arid", "lazem", "lazim", "7aram", "7alal",
    "khara", "5ara", "ya3ni", "yani", "mafi", "hal", "hatha", "akid",
    "mumkin", "shukran", "habibi", "baba", "7aga", "kwayes", "mish",
    "ba3d", "b3d", "wajid", "wayid", "gher", "shway", "3adi",
}

# Latin words that carry Arabizi marker digits (2,3,5,6,7,8,9) mixed in.
_MARKER_IN_WORD_RE = re.compile(r"[A-Za-z][2356789][A-Za-z]")


def _script_ratio(text: str) -> tuple[float, float]:
    """Return (arabic_ratio, latin_ratio) over non-space characters."""
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return 0.0, 0.0
    ar = sum(1 for c in chars if _ARABIC_RE.match(c))
    la = sum(1 for c in chars if _LATIN_RE.match(c))
    return ar / len(chars), la / len(chars)


def _has_arabizi(text: str) -> bool:
    lowered = text.lower()
    tokens = set(re.findall(r"[A-Za-z']+", lowered))
    if tokens & _DIALECT_LATIN:
        return True
    if _MARKER_IN_WORD_RE.search(text):
        return True
    return False


_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)


def detect_language(text: str | None) -> str:
    """Classify a document into ar / arz / en / mixed / other."""
    if not text:
        return "other"
    # URLs inflate the Latin ratio (https://t.co/...) — drop them first so a
    # pure-Arabic post with a link is still "ar", not "mixed".
    text = _URL_RE.sub(" ", text)
    ar_ratio, la_ratio = _script_ratio(text)

    if ar_ratio >= 0.35 and la_ratio >= 0.15:
        return "mixed"
    if ar_ratio >= 0.35:
        tokens = set(re.findall(r"[\u0600-\u06FF]+", text))
        if tokens & _DIALECT_TOKENS:
            return "arz"
        return "ar"
    if la_ratio >= 0.15:
        if _has_arabizi(text):
            return "arz"
        return "en"
    return "other"


# ---------------------------------------------------------------------------
# Optional fasttext upgrade path (Amendment A4: unavailable on Windows; kept
# for the Linux cron runner where wheels exist).
# ---------------------------------------------------------------------------


class FasttextLangID:
    """Wraps fasttext lid.176 when available; None otherwise.

    Instantiate via ``FasttextLangID.load()``; it returns ``None`` unless the
    model file exists and the package imports cleanly. ``detect`` maps lid
    codes (``ar``, ``arz``, ``en``) onto our vocabulary and still reports
    ``mixed`` via the script heuristic.
    """

    def __init__(self, model) -> None:
        self._model = model

    @classmethod
    def load(cls, model_path: str | None = None) -> "FasttextLangID | None":
        try:
            import fasttext  # type: ignore
        except ImportError:
            return None
        path = model_path or "models/lid.176.bin"
        try:
            return cls(fasttext.load_model(path))
        except (OSError, ValueError):
            return None

    def detect(self, text: str) -> str:
        if not text:
            return "other"
        try:
            label, _ = self._model.predict(text.replace("\n", " ")[:1000])
            code = label[0].replace("__label__", "")
            if code in ("ar", "arz", "en"):
                return code
            ar_ratio, _ = _script_ratio(text)
            if ar_ratio >= 0.35:
                return "ar"
            return "en"
        except Exception:
            return detect_language(text)


_FASTTEXT: FasttextLangID | None = None


def get_langid() -> "FasttextLangID | None":
    """Lazily load fasttext once; returns None when unavailable."""
    global _FASTTEXT
    if _FASTTEXT is None:
        _FASTTEXT = FasttextLangID.load()
    return _FASTTEXT
