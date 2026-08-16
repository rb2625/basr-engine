"""Zero-cost lexicon fast path (Amendment A7).

Classifies the clear-cut majority of docs with keyword evidence and ZERO
LLM tokens: sentiment, emotion, the v1 signal taxonomy, sector, and known
UAE entities. Confidence is deliberately conservative - anything ambiguous
(sarcasm, conflicting signals, weak evidence, questions) scores low and the
pipeline falls back to the LLM classifier (basr/nlp/pipeline.py).

Measured, not vibes: score it against the eval set with
    python -m basr.eval --path lexicon --dry-run
The routing threshold lives in pipeline.py (ROUTE_CONFIDENCE).

Design notes:
- Arabic words are matched with common clitic prefixes (و ف ب ل ال) stripped
  from each token, so "الإيجارات" hits "إيجارات".
- Signal words imply sentiment polarity (opportunity -> positive,
  stress/closure -> negative), so a doc like "New mega mall opens" gets
  positive sentiment from the signal evidence alone.
- Sarcasm always defers to the LLM: a positive word right after negative
  context, or a known sarcasm marker, collapses confidence.
- English/Arabizi are lowercased; Arabic keeps its script (content, not
  punctuation - working rule 6).
"""

from __future__ import annotations

import re
from typing import Any

from .classifier import (
    ClassifyResult,
    EMOTIONS,
    MODEL_VERSION,
    SECTORS,
    SIGNAL_TYPES,
)

LEXICON_VERSION = "lexicon-v1"
ROUTE_CONFIDENCE = 0.55  # pipeline: below this, fall back to the LLM

# ---------------------------------------------------------------------------
# Word lists: {word: weight}. Weight 2 = strong/clear, 1 = weak/topic.
# ---------------------------------------------------------------------------

# --- English sentiment ------------------------------------------------------
POS_EN = {
    "amazing": 2, "excellent": 2, "love": 2, "loved": 2, "best ever": 2,
    "superb": 2, "fantastic": 2, "wonderful": 2, "awesome": 2, "brilliant": 2,
    "perfect": 2, "great": 1, "good": 1, "nice": 1, "best": 1, "better": 1,
    "happy": 1, "enjoyed": 1, "like": 1, "liked": 1, "cute": 1, "helpful": 1,
    "fast": 1, "clean": 1, "convenient": 1, "easy": 1, "free": 1, "new": 1,
    "improved": 1, "welcome": 1, "win": 1, "success": 1, "successful": 1,
}
NEG_EN = {
    "terrible": 2, "awful": 2, "horrible": 2, "worst": 2, "hate": 2,
    "scam": 2, "fraud": 2, "ripoff": 2, "disgusting": 2, "failure": 2,
    "failed": 2, "out of control": 2, "ridiculous": 2, "outrageous": 2,
    "unaffordable": 2, "overpriced": 2, "not paid": 2, "not paying": 2,
    "eating my budget": 2, "so expensive": 2, "no service": 2, "broken": 2,
    "bad": 1, "worse": 1, "poor": 1, "slow": 1, "stuck": 1, "problem": 1,
    "problems": 1, "complaint": 1, "complaints": 1, "delay": 1, "delays": 1,
    "cancelled": 1, "canceled": 1, "expensive": 2, "overcharged": 1,
    "mess": 1, "frustrate": 2, "frustrates": 2, "frustrating": 2,
}

# --- Arabic sentiment -------------------------------------------------------
POS_AR = {
    "ممتاز": 2, "رائع": 2, "رائعة": 2, "أحب": 2, "نجاح": 2, "أرباح": 2,
    "ربح": 2, "جيد": 1, "جيدة": 1, "جميل": 1, "حلو": 1, "شكرا": 1,
    "سعيد": 1, "سعيدة": 1, "مبسوط": 1, "أفضل": 1, "يسعدني": 1,
}
NEG_AR = {
    "فظيع": 2, "مروع": 2, "غش": 2, "احتيال": 2, "نصب": 2, "جنوني": 2,
    "سيئ": 1, "سيئة": 1, "صعب": 1, "مزعج": 1, "مشكلة": 1, "مشاكل": 1,
    "شكاوى": 1, "شكوى": 1, "مستمرة": 1,
}

# --- Arabizi sentiment ------------------------------------------------------
POS_ARZ = {
    "7elu": 1, "7elo": 1, "helw": 1, "tayyeb": 1, "barak allah": 1,
    "rakhis": 2, "nazele": 2, "ashal": 2, "jdid": 1, "jadidah": 1,
    "nadeef": 1, "sarre3": 1,
}
NEG_ARZ = {
    "ghali": 2, "ghaly": 2, "7araam": 2, "khara": 2, "zed": 2,
    "mesh 3adil": 2, "mesh muhimmah": 1, "za3lan": 1, "mushkilah": 1,
    "3ala el al": 2, "ma fi flous": 2, "z3alan": 1,
}

# --- Signal: stress ---------------------------------------------------------
STRESS_EN = {
    "layoffs": 2, "layoff": 2, "fired": 2, "let go": 2, "cut jobs": 2,
    "rent increase": 2, "rent increases": 2, "fees going up": 2,
    "prices going up": 2, "going up": 2, "out of control": 2,
    "ridiculous": 2, "expensive": 2, "unaffordable": 2, "crisis": 2,
    "struggling": 1, "struggle": 1, "losses": 2, "debt": 2, "default": 2,
    "delays": 2, "delayed": 2, "shortage": 2, "inflation": 2,
    "recession": 2, "overpriced": 2, "salary cut": 2, "fare increase": 2,
    "price hike": 2, "cost of living": 2, "not paid": 2, "eating my budget": 2,
    "rents": 1, "rent": 1, "fees": 1, "prices": 1, "costs": 1,
    "increase": 1, "increases": 1, "rising": 1, "fare": 1, "tolls": 1,
    "taxes": 2, "problems": 1, "complaints": 1, "wait times": 1,
    "frustrate": 2, "frustrating": 2, "traffic": 1,
}
STRESS_AR = {
    "جنوني": 2, "ارتفاع": 2, "ارتفعت": 2, "أرتفعت": 2, "غلاء": 2,
    "أزمة": 2, "ركود": 2, "تسريح": 2, "خسائر": 2, "ديون": 2, "تأخر": 2,
    "تأخير": 2, "انقطاع": 2, "نقص": 2, "تضخم": 2, "ضغوط": 2, "يضغط": 2,
    "تتفاقم": 2, "تدهور": 2, "رفع": 2, "رفعت": 2, "زيادة": 2, "زادت": 2,
    "مهددة": 2, "سوء الخدمة": 2, "مخاوف": 2, "تراجع": 2, "الضرائب": 2,
    "ضرائب": 2, "شكاوى": 2, "شكوى": 2, "إيجارات": 1, "إيجار": 1,
    "أسعار": 1, "رسوم": 1, "رواتب": 1, "وقود": 1, "كهرباء": 1,
    "مواقف": 1, "ازدحام": 1,
}
STRESS_ARZ = {
    "zed": 2, "ghali": 2, "ghaly": 2, "3ala el al": 2, "ma fi flous": 2,
    "saf2at": 2, "mowazafin": 1, "ijar": 1, "mushkilah": 1, "mesh 3adil": 2,
}

# --- Signal: closure --------------------------------------------------------
CLOSURE_EN = {
    "bankrupt": 2, "bankruptcy": 2, "insolvent": 2, "liquidated": 2,
    "liquidation": 2, "closed": 2, "closes": 2, "closing": 2, "shut down": 2,
    "shutdown": 2, "went under": 2, "folded": 2, "defunct": 2,
    "shut its doors": 2, "cease operations": 2, "closures": 2,
}
CLOSURE_AR = {
    "إفلاس": 2, "أفلس": 2, "أفلست": 2, "أغلقت": 2, "أغلق": 2, "إغلاق": 2,
    "توقفت": 2, "توقف": 2, "تصفية": 2,
}
CLOSURE_ARZ = {
    "7alat": 2, "sakkar": 2, "sakkaret": 2, "masakt": 2, "masaket": 2,
    "iflas": 2, "2afalet": 2,
}

# --- Signal: opportunity ----------------------------------------------------
OPP_EN = {
    "opens": 2, "opening": 2, "launches": 2, "launch": 2, "launched": 2,
    "hiring": 2, "hiring surge": 2, "expands": 2, "expansion": 2,
    "expanding": 2, "record high": 2, "record": 2, "rally": 2,
    "record profit": 2, "grants": 2, "scholarships": 2, "visa reforms": 2,
    "incentive": 2, "free training": 2, "booming": 2, "new branch": 2,
    "new store": 2, "new mall": 2, "new campus": 2, "new line": 2,
    "direct flights": 2, "doubled": 2, "double-digit": 2, "new": 1,
    "growth": 1, "grow": 1, "grows": 1, "growing": 1, "investment": 1,
    "invest": 1, "boost": 1, "opportunity": 1, "opportunities": 1,
    "affordable": 1, "discount": 1, "improved": 1, "profit": 1,
    "profits": 1, "surge": 1, "surged": 1, "announces": 1,
    "announced": 1, "welcomes": 1,
}
OPP_AR = {
    "افتتاح": 2, "افتتح": 2, "افتتحت": 2, "أطلقت": 2, "إطلاق": 2,
    "توظيف": 2, "تعيين": 2, "منح": 2, "قياسيا": 2, "قياسي": 2,
    "مبادرة": 2, "مجانا": 2, "فرص": 2, "استثمار": 2, "إقبالا": 2,
    "إقبال": 2, "ينمو": 2, "نموا": 2, "نمو": 2, "تزايد": 2, "يتزايد": 2,
    "ازدهار": 2, "تزدهر": 2, "تفتح": 2, "تخفيضات": 2, "خفض": 2,
    "جديدة": 1, "جديد": 1, "تعلن": 1, "أعلنت": 1, "رقمية": 1, "منصة": 1,
}
OPP_ARZ = {
    "tashji3": 2, "tawzif": 2, "nazele": 2, "rakhis": 2, "ashal": 2,
    "jdid": 1, "jadidah": 1, "yftah": 2, "yaftah": 2,
}

# --- Emotions ---------------------------------------------------------------
EMOTION_WORDS: dict[str, dict[str, int]] = {
    "anger": {"غاضب": 2, "غضب": 2, "angry": 2, "furious": 2, "pissed": 2,
              "mad": 2, "za3lan": 1, "زعلان": 1, "مستاء": 1},
    "fear": {"خوف": 2, "خائف": 2, "worried": 2, "fear": 2, "scared": 2,
             "قلق": 2, "anxious": 2, "مخاوف": 2},
    "joy": {"فرح": 2, "سعيد": 2, "سعيدة": 2, "مبسوط": 2, "happy": 2,
            "excited": 2, "delighted": 2, "فرحة": 2},
    "sadness": {"حزين": 2, "حزن": 2, "sad": 2, "upset": 2, "depressed": 2,
                "disappointed": 2, "مكتئب": 2},
    "disgust": {"مقرف": 2, "disgusting": 2, "gross": 2, "سئم": 2},
    "surprise": {"مفاجأة": 2, "مفاجئ": 2, "wow": 2, "shocked": 2, "صدمة": 2},
    "trust": {"وثوق": 2, "trust": 2, "reliable": 2, "trustworthy": 2,
              "موثوق": 2},
    "anticipation": {"ترقب": 2, "anticipate": 2, "looking forward": 2,
                     "يتطلع": 2},
}

# --- Sectors ----------------------------------------------------------------
SECTOR_WORDS: dict[str, dict[str, int]] = {
    "Real Estate": {
        "rent": 2, "rents": 2, "rental": 2, "property": 2, "real estate": 2,
        "mortgage": 2, "apartment": 2, "villa": 2, "landlord": 2,
        "tenants": 2, "housing": 2, "ijar": 2, "إيجارات": 2, "إيجار": 2,
        "العقارات": 2, "عقار": 2, "سكن": 2, "شقة": 2, "فيلا": 2,
        "مالك": 1, "مستأجرين": 2, "إسكان": 2, "السكن": 2, "عقاري": 2,
        "العقاري": 2,
    },
    "Finance": {
        "bank": 2, "banks": 2, "banking": 2, "loan": 2, "loans": 2,
        "interest": 2, "fintech": 2, "shares": 2, "stocks": 2, "profit": 1,
        "profits": 1, "financial": 2, "بنك": 2, "البنك": 2, "قروض": 2,
        "فوائد": 2, "فائدة": 2, "مصرف": 2, "أسهم": 2, "سهم": 2, "أرباح": 2,
        "إيداعات": 2, "مصرفية": 2,
    },
    "Retail": {
        "mall": 2, "malls": 2, "store": 2, "stores": 2, "shop": 2,
        "shops": 2, "retail": 2, "supermarket": 2, "shopping": 2, "مول": 2,
        "متجر": 2, "متاجر": 2, "سوبرماركت": 2, "تسوق": 2, "محل": 2,
        "محلات": 2, "سلسلة": 2,
    },
    "F&B": {
        "restaurant": 2, "restaurants": 2, "cafe": 2, "cafes": 2, "food": 2,
        "delivery": 2, "مطعم": 2, "مطاعم": 2, "مقهى": 2, "مقاهي": 2,
        "طعام": 2, "توصيل": 2, "وجبات": 2, "خدمة توصيل": 2,
    },
    "Transport": {
        "metro": 2, "taxi": 2, "taxis": 2, "uber": 2, "salik": 2, "rta": 2,
        "flights": 2, "flight": 2, "airport": 2, "airline": 2,
        "airlines": 2, "traffic": 2, "مترو": 2, "طيران": 2, "رحلات": 2,
        "مطار": 2, "مواقف": 2, "أجرة": 2, "أوبر": 2, "سالك": 2,
        "هيئة الطرق": 2, "المواصلات": 2,
    },
    "Tech": {
        "tech": 2, "technology": 2, "app": 2, "apps": 2, "startup": 2,
        "startups": 2, "software": 2, "digital": 2, "ai": 2, "platform": 2,
        "تكنولوجيا": 2, "تقنية": 2, "تطبيق": 2, "تطبيقات": 2,
        "شركة ناشئة": 2, "منصة": 2, "رقمية": 2, "برمجة": 2, "الإنترنت": 2,
        "انترنت": 2, "إنترنت": 2,
    },
    "Education": {
        "school": 2, "schools": 2, "university": 2, "universities": 2,
        "students": 2, "tuition": 2, "جامعة": 2, "جامعات": 2, "مدرسة": 2,
        "مدارس": 2, "طلاب": 2, "رسوم": 2, "دراسية": 2, "تعليم": 2, "منح": 2,
    },
    "Healthcare": {
        "hospital": 2, "hospitals": 2, "clinic": 2, "clinics": 2,
        "doctor": 2, "doctors": 2, "health": 2, "healthcare": 2,
        "insurance": 2, "مستشفى": 2, "مستشفيات": 2, "عيادة": 2, "عيادات": 2,
        "طبيب": 2, "أطباء": 2, "صحة": 2, "علاج": 2, "تأمين": 2,
        "التأمين": 2,
    },
    "Government Services": {
        "government": 2, "ministry": 2, "visa": 2, "visas": 2,
        "passport": 2, "emirates id": 2, "citizenship": 2, "حكومة": 2,
        "وزارة": 2, "تأشيرة": 2, "فيزا": 2, "جواز": 2, "هوية": 2,
        "معاملات": 2, "المعاملات": 2, "منحة": 2,
    },
    "Logistics": {
        "shipping": 2, "courier": 2, "cargo": 2, "logistics": 2, "شحن": 2,
        "لوجستيات": 2, "بريد": 2,
    },
}

# --- Known UAE entities -----------------------------------------------------
COMPANIES = {
    "emaar", "damac", "aldar", "nakheel", "majid al futtaim", "dubai holding",
    "adnoc", "dewa", "etisalat", "careem", "talabat", "noon", "lulu",
    "al futtaim", "emirates", "etihad", "flydubai", "rta", "salik",
    "dubai ports", "dubai world", "air arabia", "emirates nbd",
    "first abu dhabi bank", "fab", "mashreq", "adcb",
    "abu dhabi commercial bank", "dubai islamic bank", "rak bank",
    "gulf news", "khaleej times", "dubai media office", "arn", "ajman bank",
    "إعمار", "داماك", "الدار", "نخيل", "أدنوك", "اتصالات", "كريم",
    "طلبات", "نون", "لولو", "الإمارات", "الاتحاد", "فلاي دبي",
    "طيران الإمارات", "دبي القابضة", "مصرف أبوظبي", "مشرق",
}
LOCATIONS = {
    "dubai", "abu dhabi", "sharjah", "ajman", "umm al quwain",
    "ras al khaimah", "fujairah", "al ain", "jumeirah", "palm jumeirah",
    "downtown dubai", "dubai marina", "marina", "difc", "business bay",
    "sheikh zayed road", "deira", "bur dubai", "dubai mall",
    "mall of the emirates", "dubai south", "dubai hills", "emirates hills",
    "arabian ranches", "jlt", "jumeirah lake towers", "saadiyat",
    "yas island", "corniche", "khalifa city", "reem island", "al reem",
    "silicon oasis", "media city", "internet city", "jebel ali", "al quoz",
    "international city", "motor city", "dubai investment park",
    "discovery gardens", "dubai creek harbour", "city walk", "bluewaters",
    "dubai festival city", "الخليج التجاري", "وسط المدينة",
    "دبي", "أبوظبي", "الشارقة", "عجمان", "رأس الخيمة", "الفجيرة",
    "أم القيوين", "العين", "جميرا", "ديرة", "بر دبي", "مارينا", "ياس",
    "جبل علي", "ند الشبا",
}

# --- Sarcasm markers (always defer to the LLM when negative context exists) -
SARCASM_MARKERS = (
    "best thing ever", "just what we needed", "love it", "love that",
    "fantastic service", "so lucky", "so much fun", "great news",
)

# --- Arabic clitic prefixes to strip before dictionary lookup ---------------
_AR_PREFIXES = ("وال", "بال", "فال", "لل", "ال", "و", "ف", "ب", "ل")

# ---------------------------------------------------------------------------
# Matching helpers
# ---------------------------------------------------------------------------


def _tokens(text: str) -> list[str]:
    """Lowercase + tokenize on non-word chars (works for ar/en/arz)."""
    return [t for t in re.split(r"[^\w]+", text.lower()) if t]


def _ar_root(token: str) -> str:
    """Strip common Arabic clitic prefixes so 'الإيجارات' hits 'إيجارات'."""
    t = token
    for prefix in _AR_PREFIXES:
        if t.startswith(prefix) and len(t) > len(prefix) + 1:
            t = t[len(prefix):]
            break
    return t


def _match_counts(text: str, words: dict[str, int]) -> dict[str, int]:
    """Weighted hit counts. Multi-word phrases match as substrings; single
    words match token-wise (Arabic tokens get prefix-stripped)."""
    lower = text.lower()
    counts: dict[str, int] = {}
    for word, weight in words.items():
        if " " in word:
            if word in lower:
                counts[word] = counts.get(word, 0) + weight
        else:
            if word in lower and re.search(rf"\b{re.escape(word)}\b", lower):
                counts[word] = counts.get(word, 0) + weight
    return counts


def _ar_match_counts(text: str, words: dict[str, int]) -> dict[str, int]:
    """Arabic variant: match on prefix-stripped tokens too."""
    counts = _match_counts(text, words)
    ar_words = {w: wt for w, wt in words.items()
                if any("\u0600" <= c <= "\u06FF" for c in w)}
    if not ar_words:
        return counts
    roots = {_ar_root(t): t for t in _tokens(text)
             if any("\u0600" <= c <= "\u06FF" for c in t)}
    for w, wt in ar_words.items():
        if w in roots and w not in counts:
            counts[w] = counts.get(w, 0) + wt
    return counts


def _weighted_sum(counts: dict[str, int]) -> int:
    return sum(counts.values())


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------


def _conf(evidence: int, conflict: int, scale: float = 1.5) -> float:
    """Confidence from weighted evidence: agreement ratio x saturation.

    evidence=1 -> ~0.37, evidence=2 -> ~0.60, evidence=4 -> ~0.84. Conflict
    (opposite polarity) pulls it toward the LLM's turf via the ratio term.
    """
    if evidence <= 0:
        return 0.0
    agree = evidence / (evidence + conflict)
    sat = 1 - 0.5 ** (evidence / scale)
    return agree * sat


def _hit_keys(counts: dict[str, int]) -> list[str]:
    return sorted(counts, key=lambda k: -counts[k])[:5]


# ---------------------------------------------------------------------------
# The classifier
# ---------------------------------------------------------------------------


class LexiconClassifier:
    """Zero-token keyword classifier. Mirrors GroqClassifier.classify's
    signature so the eval harness and pipeline can use either."""

    def __init__(self) -> None:
        pass

    def classify(
        self,
        text: str,
        *,
        title: str | None = None,
        lang: str | None = None,
    ) -> ClassifyResult:
        """Classify one doc. Low confidence (< ROUTE_CONFIDENCE) means the
        caller should fall back to the LLM. Never raises."""
        try:
            return self._classify(text, title=title, lang=lang)
        except Exception as exc:  # defensive: fast path must never crash
            return ClassifyResult(
                confidence=0.0,
                raw={"error": f"lexicon: {str(exc)[:200]}"},
                model_version=LEXICON_VERSION,
            )

    # ------------------------------------------------------------------

    def _classify(
        self,
        text: str,
        *,
        title: str | None,
        lang: str | None,
    ) -> ClassifyResult:
        if lang is None:
            from .langid import detect_language
            lang = detect_language(text)

        # Sentiment evidence: direct words + signal words mapped to polarity.
        pos = {**_match_counts(text, POS_EN), **_match_counts(text, POS_ARZ)}
        neg = {**_match_counts(text, NEG_EN), **_match_counts(text, NEG_ARZ)}
        pos.update(_ar_match_counts(text, POS_AR))
        neg.update(_ar_match_counts(text, NEG_AR))

        stress = {**_match_counts(text, STRESS_EN),
                  **_match_counts(text, STRESS_ARZ)}
        stress.update(_ar_match_counts(text, STRESS_AR))
        closure = {**_match_counts(text, CLOSURE_EN),
                   **_match_counts(text, CLOSURE_ARZ)}
        closure.update(_ar_match_counts(text, CLOSURE_AR))
        opp = {**_match_counts(text, OPP_EN), **_match_counts(text, OPP_ARZ)}
        opp.update(_ar_match_counts(text, OPP_AR))

        # Polarity implied by signal groups.
        pos_ev = _weighted_sum(pos) + _weighted_sum(opp)
        neg_ev = _weighted_sum(neg) + _weighted_sum(stress) + _weighted_sum(closure)

        stress_ev = _weighted_sum(stress)
        closure_ev = _weighted_sum(closure)
        opp_ev = _weighted_sum(opp)

        # Sentiment label from evidence (ties go neutral).
        if pos_ev == 0 and neg_ev == 0:
            sent_label, sent_score = "neutral", 0.0
        elif pos_ev > neg_ev:
            sent_label, sent_score = "positive", min(1.0, pos_ev / 4.0)
        elif neg_ev > pos_ev:
            sent_label, sent_score = "negative", -min(1.0, neg_ev / 4.0)
        else:
            sent_label, sent_score = "mixed", 0.0

        # Signal: strongest group wins; >1 group with strong evidence is
        # genuinely ambiguous -> defer to the LLM (signal_blocked).
        groups = {"stress": stress_ev, "closure": closure_ev,
                  "opportunity": opp_ev}
        strong_groups = {k for k, v in groups.items() if v >= 2}
        signal_blocked = False
        if not strong_groups:
            signal_type, signal_conf = "neutral", 0.0
        elif len(strong_groups) == 1:
            signal_type = strong_groups.pop()
            signal_conf = _conf(groups[signal_type], 0)
        else:
            # Conflicting strong signals (e.g. 'struggling' + 'closures').
            signal_type, signal_conf = "neutral", 0.0
            signal_blocked = True

        # Sentiment confidence on the dominant polarity (the minority side is
        # the conflict that pulls ambiguous docs toward the LLM).
        dominant = max(pos_ev, neg_ev)
        minority = min(pos_ev, neg_ev)
        sent_conf = _conf(dominant, minority) if dominant else 0.0
        overall = sent_conf if signal_conf == 0.0 else min(sent_conf, signal_conf)
        if signal_blocked:
            # A doc where two strong signals compete must not be decided by
            # keyword counts alone - collapse confidence and defer.
            overall *= 0.4

        # Emotion: best emotion group with at least one hit.
        emotion = "neutral"
        best_em, best_em_ev = "", 0
        for name, words in EMOTION_WORDS.items():
            ev = _weighted_sum(_match_counts(text, words))
            if ev > best_em_ev:
                best_em, best_em_ev = name, ev
        if best_em_ev > 0:
            emotion = best_em

        # Sector: best sector group.
        sector = "General"
        best_sec, best_sec_ev = "", 0
        for name, words in SECTOR_WORDS.items():
            ev = _weighted_sum(_match_counts(text, words))
            if ev > best_sec_ev:
                best_sec, best_sec_ev = name, ev
        if best_sec_ev > 0:
            sector = best_sec

        # Sarcasm: known marker + negative context, or a positive word
        # appearing after negative evidence -> always defer to the LLM.
        sarcasm = False
        lower = text.lower()
        if neg_ev > 0 and any(m in lower for m in SARCASM_MARKERS):
            sarcasm = True
        elif neg_ev > 0 and pos_ev > 0:
            # 'Love it.' at the end after 'five fees' is irony, not joy.
            tail = lower[-120:]
            if any(w in tail for w in ("love", "great", "amazing", "fantastic",
                                       "perfect", "wonderful", "best")):
                sarcasm = True

        # Entities: known companies + UAE locations.
        companies = [c for c in COMPANIES if c in lower][:10]
        locations = [l for l in LOCATIONS if l in lower][:10]

        # Confidence penalties: sarcasm, questions without strong signals.
        if sarcasm:
            overall *= 0.3
        if "?" in text and signal_conf == 0.0:
            overall *= 0.5
        overall = max(0.0, min(1.0, overall))

        intensity = 1
        if signal_conf >= 0.8:
            intensity = 3
        elif signal_conf >= 0.6:
            intensity = 2

        keywords = _hit_keys({**stress, **closure, **opp, **pos, **neg})
        summary = (
            f"Lexicon fast path: {sent_label} sentiment, {signal_type} signal"
            f" (evidence: {', '.join(keywords) if keywords else 'none'})."
        )

        return ClassifyResult(
            sentiment_score=round(sent_score, 3),
            sentiment_label=sent_label,
            emotion=emotion,
            sarcasm=sarcasm,
            signal_type=signal_type,
            sector=sector,
            intensity_score=intensity,
            confidence=round(overall, 3),
            detected_language=lang,
            extracted_entities={"companies": companies, "locations": locations},
            summary_en=summary[:300],
            raw={"evidence": {"stress": stress_ev, "closure": closure_ev,
                              "opportunity": opp_ev, "positive": pos_ev,
                              "negative": neg_ev},
                 "sarcasm": sarcasm},
            model_version=LEXICON_VERSION,
        )


# ---------------------------------------------------------------------------
# Standalone smoke test:  python -m basr.nlp.lexicon
# ---------------------------------------------------------------------------
_SAMPLES = [
    ("Rents in Dubai are out of control, families are leaving for Abu Dhabi", "en"),
    ("New mega mall opens on Palm Jumeirah, 300 stores", "en"),
    ("Great, another rent increase. Just what we needed.", "en"),
    ("أغلقت شركة التوصيل ثلاثة فروع في أبوظبي بسبب الخسائر", "ar"),
    ("3ashan el ijar zed kteer, kol 7ada 3am yruh", "arz"),
    ("Watch this cute cat video", "en"),
]


def _smoke_test() -> None:
    lex = LexiconClassifier()
    for text, lang in _SAMPLES:
        r = lex.classify(text, lang=lang)
        print(f"[{lang}] conf={r.confidence:.2f} sent={r.sentiment_label} "
              f"signal={r.signal_type} emotion={r.emotion} "
              f"sarcasm={r.sarcasm} sector={r.sector}")
        print(f"      {text[:70]}")


if __name__ == "__main__":
    _smoke_test()
