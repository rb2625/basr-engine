"""Entity extraction + geocoding - zero tokens (Amendment A8).

A curated UAE gazetteer (locations with lat/lng), known companies/brands,
authorities, and universities. Entities map to the ``entities`` /
``doc_entities`` tables and feed the Phase 3 dashboard map. Extraction is
substring matching on the cleaned text - deliberately conservative and
deterministic; the LLM's richer entity pass can supersede it later, but this
is what makes every doc geocodable today without spending tokens.
"""

from __future__ import annotations

from typing import Any

from .textmatch import has_word

# ---------------------------------------------------------------------------
# Locations: name -> (lat, lng). Includes emirates, cities, and the areas
# that dominate UAE social posts. Arabic names for Arabic docs.
# ---------------------------------------------------------------------------

LOCATIONS: dict[str, tuple[float, float]] = {
    # Emirates + cities
    "dubai": (25.2048, 55.2708), "abu dhabi": (24.4539, 54.3773),
    "sharjah": (25.3463, 55.4209), "ajman": (25.4052, 55.5136),
    "umm al quwain": (25.5647, 55.5555), "ras al khaimah": (25.8007, 55.9762),
    "fujairah": (25.1288, 56.3265), "al ain": (24.1302, 55.8023),
    "hatta": (24.7960, 56.1180), "دبي": (25.2048, 55.2708),
    "أبوظبي": (24.4539, 54.3773), "الشارقة": (25.3463, 55.4209),
    "عجمان": (25.4052, 55.5136), "أم القيوين": (25.5647, 55.5555),
    "رأس الخيمة": (25.8007, 55.9762), "الفجيرة": (25.1288, 56.3265),
    "العين": (24.1302, 55.8023), "حتا": (24.7960, 56.1180),
    # Dubai areas
    "jumeirah": (25.2354, 55.2539), "palm jumeirah": (25.1124, 55.1390),
    "dubai marina": (25.0805, 55.1403), "marina": (25.0805, 55.1403),
    "downtown dubai": (25.1955, 55.2781), "difc": (25.2123, 55.2664),
    "business bay": (25.1886, 55.2663), "sheikh zayed road": (25.2270, 55.2841),
    "deira": (25.2711, 55.3259), "bur dubai": (25.2554, 55.2989),
    "dubai mall": (25.1980, 55.2796), "mall of the emirates": (25.1184, 55.2006),
    "dubai south": (24.9200, 55.1720), "dubai hills": (25.0650, 55.2400),
    "emirates hills": (25.0540, 55.1930), "arabian ranches": (25.0730, 55.2190),
    "jumeirah lake towers": (25.0669, 55.1427), "jlt": (25.0669, 55.1427),
    "silicon oasis": (25.1200, 55.3800), "dubai silicon oasis": (25.1200, 55.3800),
    "media city": (25.0900, 55.1650), "internet city": (25.0950, 55.1650),
    "dubai internet city": (25.0950, 55.1650), "jebel ali": (24.9950, 55.1100),
    "al quoz": (25.1470, 55.2700), "international city": (25.1500, 55.3200),
    "motor city": (25.0400, 55.2500), "discovery gardens": (25.0320, 55.1600),
    "dubai creek harbour": (25.2200, 55.3200), "city walk": (25.2040, 55.2640),
    "bluewaters": (25.0820, 55.1210), "bluewaters island": (25.0820, 55.1210),
    "dubai festival city": (25.2260, 55.3510), "mirdif": (25.2200, 55.4200),
    "al barsha": (25.1070, 55.1890), "karama": (25.2470, 55.3010),
    "satwa": (25.2350, 55.2790), "jumeirah village circle": (25.0740, 55.2320),
    "jvc": (25.0740, 55.2320), "damac hills": (25.0400, 55.2650),
    "the greens": (25.0800, 55.1800), "knowledge village": (25.0980, 55.1640),
    "dubai academic city": (25.1200, 55.3900), "port rashid": (25.2650, 55.2800),
    "al fahidi": (25.2630, 55.2970), "zabeel": (25.2400, 55.3100),
    "nad al sheba": (25.1730, 55.3400), "al wasl": (25.2120, 55.2700),
    "umm suqeim": (25.1550, 55.2150), "jumeirah beach residence": (25.0790, 55.1370),
    "jbr": (25.0790, 55.1370), "al satwa": (25.2350, 55.2790),
    "dubai hills estate": (25.0650, 55.2400), "al barsha south": (25.1070, 55.1800),
    "جميرا": (25.2354, 55.2539), "نخلة جميرا": (25.1124, 55.1390),
    "دبي مارينا": (25.0805, 55.1403), "مارينا": (25.0805, 55.1403),
    "وسط مدينة دبي": (25.1955, 55.2781), "الخليج التجاري": (25.1886, 55.2663),
    "ديرة": (25.2711, 55.3259), "بر دبي": (25.2554, 55.2989),
    "البرشاء": (25.1070, 55.1890), "القوز": (25.1470, 55.2700),
    "ند الشبا": (25.1730, 55.3400), "أم سقيم": (25.1550, 55.2150),
    "الورقاء": (25.2200, 55.3600), "المحيصنة": (25.2400, 55.3400),
    "دبي الجنوب": (24.9200, 55.1720), "جبل علي": (24.9950, 55.1100),
    # Abu Dhabi areas
    "saadiyat": (24.5360, 54.4230), "saadiyat island": (24.5360, 54.4230),
    "yas island": (24.4920, 54.6050), "yas": (24.4920, 54.6050),
    "corniche": (24.4770, 54.3410), "khalifa city": (24.4070, 54.5320),
    "reem island": (24.4960, 54.4140), "reem": (24.4960, 54.4140),
    "al reem": (24.4960, 54.4140), "khalidiyah": (24.5110, 54.3610),
    "al zahiyah": (24.5110, 54.3610), "mussafah": (24.3500, 54.4800),
    "masdar city": (24.4333, 54.6180), "sadiyaat": (24.5360, 54.4230),
    "جزر السعديات": (24.5360, 54.4230), "جزيرة ياس": (24.4920, 54.6050),
    "مدينة خليفة": (24.4070, 54.5320), "جزيرة الريم": (24.4960, 54.4140),
    "الخالدية": (24.5110, 54.3610), "مدينة مصدر": (24.4333, 54.6180),
    # Sharjah / other areas
    "al majaz": (25.3160, 55.3860), "al khan": (25.3370, 55.3810),
    "al zahia": (25.3400, 55.4300), "المجز": (25.3160, 55.3860),
    "الخان": (25.3370, 55.3810), "الزاهية": (25.3400, 55.4300),
    "khorfakkan": (25.3389, 56.3550), "كلباء": (25.0740, 56.3540),
    "خورفكان": (25.3389, 56.3550), "dibba": (25.6180, 56.2720),
    "دبا": (25.6180, 56.2720),
}

# ---------------------------------------------------------------------------
# Known companies / brands (type 'brand')
# ---------------------------------------------------------------------------

BRANDS: set[str] = {
    "emaar", "damac", "aldar", "nakheel", "majid al futtaim", "dubai holding",
    "adnoc", "dewa", "etisalat", "du", "careem", "talabat", "noon", "lulu",
    "al futtaim", "emirates", "etihad", "flydubai", "air arabia", "salik",
    "emirates nbd", "first abu dhabi bank", "fab", "mashreq", "adcb",
    "abu dhabi commercial bank", "dubai islamic bank", "rak bank",
    "gulf news", "khaleej times", "dubai media office", "arn", "ajman bank",
    "virgin", "swvl", "yango", "botim", "keeta", "deliveroo", "noon food",
    "careem food", "souq", "amazon", "damac properties", "emaar properties",
    "إعمار", "داماك", "الدار", "نخيل", "أدنوك", "اتصالات", "كريم",
    "طلبات", "نون", "لولو", "الإمارات", "الاتحاد", "فلاي دبي",
    "طيران الإمارات", "دبي القابضة", "مصرف أبوظبي", "مشرق", "بنك دبي الإسلامي",
    "خليج تايمز", "غلف نيوز", "مكتب دبي الإعلامي",
}

# ---------------------------------------------------------------------------
# Authorities (type 'authority')
# ---------------------------------------------------------------------------

AUTHORITIES: set[str] = {
    "rta", "dha", "dewa", "khda", "ded", "tecom", "dmcc", "vara", "sca",
    "mohre", "gdrfa", "ica", "dubai police", "abu dhabi police",
    "dubai municipality", "ministry of education", "ministry of labour",
    "ministry of interior", "federal tax authority", "emirates id",
    "dubai customs", "dubai economy", "dubai courts", "federal authority",
    "municipality of abu dhabi city", "ministry of human resources",
    "هيئة الطرق والمواصلات", "بلدية دبي", "شرطة دبي", "وزارة التعليم",
    "وزارة العمل", "وزارة الداخلية", "الهيئة الاتحادية للضرائب",
    "هيئة الهوية", "الهوية الإماراتية", "الإقامة وشؤون الأجانب",
}

# ---------------------------------------------------------------------------
# Universities (type 'university')
# ---------------------------------------------------------------------------

UNIVERSITIES: set[str] = {
    "khalifa university", "uaeu", "united arab emirates university",
    "american university of sharjah", "aus", "american university in dubai",
    "aud", "university of dubai", "zayed university", "nyu abu dhabi",
    "mbzuai", "hct", "higher colleges of technology", "aurak",
    "american university of ras al khaimah", "sorbonne abu dhabi",
    "middlesex dubai", "heriot-watt dubai", "university of wollongong dubai",
    "bits pilani dubai", "canadian university dubai", "university of sharjah",
    "abu dhabi university", "paris-sorbonne", "durham dubai",
    "university of birmingham dubai", "جامعة خليفة", "جامعة الإمارات",
    "الجامعة الأمريكية في الشارقة", "جامعة زايد", "جامعة نيويورك أبوظبي",
    "جامعة الشارقة", "جامعة أبوظبي", "كليات التقنية العليا",
    "الجامعة الأمريكية في رأس الخيمة", "جامعة دبي",
}

ENTITY_TYPES = ("location", "brand", "authority", "university")


class EntityExtractor:
    """Deterministic gazetteer extraction. Returns entries shaped for the
    ``entities`` table ({name, type, normalized, lat, lng})."""

    def extract(self, text: str) -> list[dict[str, Any]]:
        """Deterministic gazetteer extraction. Returns entries shaped for the
        ``entities`` table ({name, type, normalized, lat, lng})."""
        lower = text.lower()
        out: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        for name, (lat, lng) in LOCATIONS.items():
            if has_word(lower, name) and ("location", name) not in seen:
                seen.add(("location", name))
                out.append({
                    "name": name, "type": "location", "normalized": name,
                    "lat": lat, "lng": lng,
                })

        for name in BRANDS:
            if has_word(lower, name) and ("brand", name) not in seen:
                seen.add(("brand", name))
                out.append({
                    "name": name, "type": "brand", "normalized": name,
                    "lat": None, "lng": None,
                })

        for name in AUTHORITIES:
            if has_word(lower, name) and ("authority", name) not in seen:
                seen.add(("authority", name))
                out.append({
                    "name": name, "type": "authority", "normalized": name,
                    "lat": None, "lng": None,
                })

        for name in UNIVERSITIES:
            if has_word(lower, name) and ("university", name) not in seen:
                seen.add(("university", name))
                out.append({
                    "name": name, "type": "university", "normalized": name,
                    "lat": None, "lng": None,
                })

        return out


# ---------------------------------------------------------------------------
# Standalone smoke test:  python -m basr.nlp.entities
# ---------------------------------------------------------------------------
_SAMPLES = [
    "Rents in Dubai are out of control, families are leaving for Abu Dhabi",
    "Emaar launches new waterfront project on Palm Jumeirah",
    "KHDA announces school fee review for Dubai private schools",
    "أغلقت شركة التوصيل ثلاثة فروع في أبوظبي بسبب الخسائر",
]


def _smoke_test() -> None:
    ex = EntityExtractor()
    for t in _SAMPLES:
        ents = ex.extract(t)
        print(f"{[(e['type'], e['name']) for e in ents]} | {t[:55]}")


if __name__ == "__main__":
    _smoke_test()
