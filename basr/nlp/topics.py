"""Topic assignment - zero tokens (Amendment A8).

A v1 topic taxonomy with keyword rules maps each doc to up to 3 topics
(multi-label, scored). Topics feed the dashboard's trend views and the
time-series aggregation in Phase 4. Runs on the cleaned text regardless of
which classifier (lexicon or LLM) handled sentiment, so enrichment backfills
every doc without spending LLM tokens.

Measured like everything else: topics get their own eval task once the eval
set grows to include topic labels (plan sec 6.7).
"""

from __future__ import annotations

from typing import Any

from .textmatch import has_word

TOPIC_KEYS = (
    "rent-housing", "jobs-labor", "prices-inflation", "business-closures",
    "transport", "government-services", "education", "healthcare",
    "tech-digital", "retail-consumer", "finance-banking",
    "tourism-hospitality", "utilities-infra", "food-delivery",
)

# {key: {label_en, label_ar, words: {word: weight}}}
TOPICS: dict[str, dict[str, Any]] = {
    "rent-housing": {
        "label_en": "Rent and housing",
        "label_ar": "الإيجارات والسكن",
        "words": {
            "rent": 2, "rents": 2, "rental": 2, "ijar": 2, "إيجار": 2,
            "إيجارات": 2, "apartment": 2, "villa": 2, "landlord": 2,
            "mortgage": 2, "tenants": 2, "housing": 2, "property": 2,
            "real estate": 2, "سكن": 2, "السكن": 2, "شقة": 2, "فيلا": 2,
            "عقارات": 2, "عقار": 2, "مالك": 1, "مستأجر": 2,
            "مستأجرين": 2, "lease": 2, "إسكان": 2,
        },
    },
    "jobs-labor": {
        "label_en": "Jobs and labor",
        "label_ar": "الوظائف وسوق العمل",
        "words": {
            "layoffs": 2, "layoff": 2, "hiring": 2, "fired": 2, "jobs": 2,
            "job": 1, "salary": 2, "salaries": 2, "wages": 2, "employees": 1,
            "recruitment": 2, "توظيف": 2, "تسريح": 2, "رواتب": 2,
            "وظائف": 2, "وظيفة": 2, "موظفين": 2, "موظفون": 2, "تعيين": 2,
            "mowazafin": 2, "mowazaf": 1, "engineers": 1, "mohandeseen": 1,
            "مهندسين": 1, "عاملين": 1, "عمال": 1,
        },
    },
    "prices-inflation": {
        "label_en": "Prices and inflation",
        "label_ar": "الأسعار والتضخم",
        "words": {
            "prices": 2, "price": 1, "expensive": 2, "inflation": 2,
            "costs": 2, "fees": 2, "rising": 2, "increase": 2, "hike": 2,
            "أسعار": 2, "غلاء": 2, "تضخم": 2, "رسوم": 2, "ارتفاع": 2,
            "زيادة": 2, "زاد": 2, "غالي": 2, "ghali": 2, "ghaly": 2,
            "cost of living": 2, "غلاء المعيشة": 2, "أسعار": 2,
        },
    },
    "business-closures": {
        "label_en": "Business closures",
        "label_ar": "إغلاق الأعمال",
        "words": {
            "closed": 2, "closing": 2, "closure": 2, "closures": 2,
            "bankrupt": 2, "bankruptcy": 2, "shut": 2, "shutdown": 2,
            "liquidat": 2, "went under": 2, "defunct": 2, "إفلاس": 2,
            "أغلق": 2, "أغلقت": 2, "إغلاق": 2, "توقف": 2, "sakkar": 2,
            "7alat": 2, "iflas": 2, "masakt": 2, "تصفية": 2, "أفلست": 2,
        },
    },
    "transport": {
        "label_en": "Transport",
        "label_ar": "النقل والمواصلات",
        "words": {
            "metro": 2, "taxi": 2, "uber": 2, "salik": 2, "rta": 2,
            "traffic": 2, "flights": 2, "flight": 1, "airport": 2,
            "airline": 2, "airlines": 2, "tram": 2, "bus": 1, "parking": 2,
            "مترو": 2, "طيران": 2, "رحلات": 2, "مطار": 2, "مواقف": 2,
            "سالك": 2, "أوبر": 2, "أجرة": 2, "مواصلات": 2, "حافلة": 1,
            "سيارات الأجرة": 2, "الطرق": 2, "طريق": 1,
        },
    },
    "government-services": {
        "label_en": "Government services",
        "label_ar": "الخدمات الحكومية",
        "words": {
            "government": 2, "ministry": 2, "visa": 2, "visas": 2,
            "passport": 2, "emirates id": 2, "citizenship": 2, "policy": 2,
            "regulation": 2, "حكومة": 2, "وزارة": 2, "تأشيرة": 2, "فيزا": 2,
            "جواز": 2, "هوية": 2, "معاملات": 2, "قانون": 2, "قرار": 2,
            "لوائح": 2, "منصة حكومية": 2,
        },
    },
    "education": {
        "label_en": "Education",
        "label_ar": "التعليم",
        "words": {
            "school": 2, "schools": 2, "university": 2, "universities": 2,
            "college": 2, "students": 2, "tuition": 2, "scholarships": 2,
            "جامعة": 2, "جامعات": 2, "مدرسة": 2, "مدارس": 2, "طلاب": 2,
            "تعليم": 2, "منح": 2, "دراسية": 2, "معهد": 2, "كلية": 2,
            "رسوم الدراسة": 2, "academic": 2,
        },
    },
    "healthcare": {
        "label_en": "Healthcare",
        "label_ar": "الصحة",
        "words": {
            "hospital": 2, "hospitals": 2, "clinic": 2, "clinics": 2,
            "doctor": 2, "doctors": 2, "health": 2, "healthcare": 2,
            "medical": 2, "insurance": 2, "مستشفى": 2, "مستشفيات": 2,
            "عيادة": 2, "عيادات": 2, "أطباء": 2, "صحة": 2, "علاج": 2,
            "تأمين": 2, "طبيب": 2, "الرعاية الصحية": 2,
        },
    },
    "tech-digital": {
        "label_en": "Tech and digital",
        "label_ar": "التقنية والرقمنة",
        "words": {
            "tech": 2, "technology": 2, "app": 2, "apps": 2, "startup": 2,
            "startups": 2, "software": 2, "digital": 2, "ai": 2,
            "platform": 2, "تكنولوجيا": 2, "تقنية": 2, "تطبيق": 2,
            "تطبيقات": 2, "منصة": 2, "رقمية": 2, "برمجة": 2, "إنترنت": 2,
            "انترنت": 2, "شركة ناشئة": 2, "الذكاء الاصطناعي": 2,
            "ذكاء اصطناعي": 2, "e-commerce": 2, "تجارة إلكترونية": 2,
        },
    },
    "retail-consumer": {
        "label_en": "Retail and consumer",
        "label_ar": "التجزئة والاستهلاك",
        "words": {
            "mall": 2, "malls": 2, "store": 2, "stores": 2, "shop": 2,
            "shopping": 2, "retail": 2, "supermarket": 2, "restaurant": 2,
            "restaurants": 2, "cafe": 2, "cafes": 2, "food": 1, "مول": 2,
            "متجر": 2, "متاجر": 2, "مطعم": 2, "مطاعم": 2, "مقهى": 2,
            "مقاهي": 2, "تسوق": 2, "سوبرماركت": 2, "محل": 2, "محلات": 2,
            "سلسلة": 2, "brand": 2,
        },
    },
    "finance-banking": {
        "label_en": "Finance and banking",
        "label_ar": "المال والأعمال",
        "words": {
            "bank": 2, "banks": 2, "banking": 2, "loan": 2, "loans": 2,
            "interest": 2, "fintech": 2, "shares": 2, "stock": 2,
            "stocks": 2, "profit": 1, "profits": 1, "بنك": 2, "البنك": 2,
            "قروض": 2, "فوائد": 2, "فائدة": 2, "مصرف": 2, "أسهم": 2,
            "سهم": 2, "أرباح": 2, "إيداعات": 2, "درهم": 1, "عملة": 2,
            "استثمار": 2, "استثمارات": 2, "سوق المال": 2,
        },
    },
    "tourism-hospitality": {
        "label_en": "Tourism and hospitality",
        "label_ar": "السياحة والضيافة",
        "words": {
            "tourism": 2, "tourist": 2, "tourists": 2, "hotel": 2,
            "hotels": 2, "visitors": 2, "travel": 2, "سياحة": 2, "سائح": 2,
            "سياح": 2, "فنادق": 2, "فندق": 2, "زوار": 2, "سفر": 2,
            "وجهة": 2, "ضيافة": 2, "hospitality": 2, "cruise": 2,
        },
    },
    "utilities-infra": {
        "label_en": "Utilities and infrastructure",
        "label_ar": "المرافق والبنية التحتية",
        "words": {
            "electricity": 2, "power": 2, "water": 2, "internet": 2,
            "network": 2, "outage": 2, "infrastructure": 2, "كهرباء": 2,
            "مياه": 2, "إنترنت": 2, "انترنت": 2, "انقطاع": 2, "شبكة": 2,
            "اتصالات": 2, "بنية تحتية": 2, "صيانة": 2, "تعطل": 2,
            "جودة الإنترنت": 2, "الإنترنت": 2,
        },
    },
    "food-delivery": {
        "label_en": "Food delivery",
        "label_ar": "توصيل الطعام",
        "words": {
            "delivery": 2, "talabat": 2, "deliveroo": 2, "order": 2,
            "توصيل": 2, "طلبات": 2, "طلب": 2, "وجبات": 2, "مطعم توصيل": 2,
            "خدمة توصيل": 2, "food delivery": 2, "keeta": 2, "noon food": 2,
            "careem food": 2, "زاد": 2, "اسأل": 2,
        },
    },
}


class TopicAssigner:
    """Assign up to 3 topics per doc from weighted keyword evidence."""

    MIN_SCORE = 2  # weighted evidence needed before a topic is claimed
    MAX_TOPICS = 3

    def assign(self, text: str) -> list[dict[str, Any]]:
        """Return [{key, label_en, label_ar, score}] sorted desc, top 3."""
        lower = text.lower()
        scores: list[tuple[int, str]] = []
        for key, spec in TOPICS.items():
            score = 0
            for word, weight in spec["words"].items():
                if has_word(lower, word):
                    score += weight
            if score >= self.MIN_SCORE:
                scores.append((score, key))
        scores.sort(reverse=True)
        out = []
        for score, key in scores[: self.MAX_TOPICS]:
            spec = TOPICS[key]
            out.append({
                "key": key,
                "label_en": spec["label_en"],
                "label_ar": spec["label_ar"],
                "score": score,
            })
        return out


# ---------------------------------------------------------------------------
# Standalone smoke test:  python -m basr.nlp.topics
# ---------------------------------------------------------------------------
_SAMPLES = [
    "Rents in Dubai are out of control, families are leaving for Abu Dhabi",
    "Tech layoffs hit the DIFC again, 200 engineers let go this week",
    "أغلقت شركة التوصيل ثلاثة فروع في أبوظبي بسبب الخسائر",
    "Government launches free AI training for citizens",
    "School fees are going up again next year",
]


def _smoke_test() -> None:
    a = TopicAssigner()
    for t in _SAMPLES:
        topics = a.assign(t)
        print(f"{[x['key'] for x in topics]} | {t[:60]}")


if __name__ == "__main__":
    _smoke_test()
