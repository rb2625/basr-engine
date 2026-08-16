"""Eval sets for the BASR classifiers (Phase 2, sec 6.7 + sec 11).

Every item carries two labels - ``sentiment`` and ``signal`` - matching the two
headline classifier tasks. The full v1 target is **500 labeled items**; this
module ships a curated seed (80) that covers Arabic (MSA + Gulf), Arabizi,
English, sarcasm, and the classic filtering traps (personal complaints that
must NOT be economic signals). Additions go here, in the same shape, until the
DoD's 500 is reached.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalItem:
    text: str
    lang: str                     # 'ar' | 'arz' | 'en' | 'mixed'
    sentiment: str                # positive | negative | neutral | mixed
    signal: str                   # stress | closure | opportunity | neutral
    note: str = ""


ITEMS: list[EvalItem] = [
    # ------------------------------------------------------------------ Arabic
    EvalItem("أرتفعت الإيجارات في دبي بشكل جنوني هذا العام، العائلات بدأت تغادر", "ar", "negative", "stress"),
    EvalItem("أغلقت شركة التوصيل ثلاثة فروع في أبوظبي بسبب الخسائر", "ar", "negative", "closure"),
    EvalItem("وزارة التعليم أعلنت عن منح جديدة للطلبة المتفوقين", "ar", "positive", "opportunity"),
    EvalItem("مستشفى خاص في الشارقة يواجه شكاوى من سوء الخدمة", "ar", "negative", "stress"),
    EvalItem("سوق العقارات في دبي يشهد إقبالا قياسيا من المستثمرين الأجانب", "ar", "positive", "opportunity"),
    EvalItem("البنك الوطني رفع فوائد القروض الشخصية", "ar", "negative", "stress"),
    EvalItem("افتتحت سلسلة مقاهي جديدة في مركز دبي المالي", "ar", "positive", "opportunity"),
    EvalItem("شكاوى من انقطاع الكهرباء في مناطق سكنية بالعين", "ar", "negative", "stress"),
    EvalItem("شركة طيران الإمارات تعلن عن توظيف 500 مضيف جديد", "ar", "positive", "opportunity"),
    EvalItem("أغلق مطعم شهير في دبي مول بعد خلاف مع المالك", "ar", "negative", "closure"),
    EvalItem("الضرائب الجديدة على الشركات الصغيرة أثرت على أرباحهم", "ar", "negative", "stress"),
    EvalItem("قطاع التكنولوجيا في الإمارات ينمو بسرعة ويجذب الشركات الناشئة", "ar", "positive", "opportunity"),
    EvalItem("ارتفاع أسعار المواد الغذائية يضغط على الأسر ذات الدخل المحدود", "ar", "negative", "stress"),
    EvalItem("افتتاح أول فرع لسلسلة متاجر أوروبية في دبي", "ar", "positive", "opportunity"),
    EvalItem("الحكومة أطلقت منصة رقمية جديدة لتسهيل المعاملات", "ar", "positive", "opportunity"),
    EvalItem("زيادة جديدة في أسعار الوقود الشهر القادم", "ar", "negative", "stress"),
    EvalItem("أزمة مواقف في دبي تتفاقم خاصة في الأحياء السكنية", "ar", "negative", "stress"),
    EvalItem("افتتاح جامعة جديدة في رأس الخيمة تستقطب الطلاب الدوليين", "ar", "positive", "opportunity"),
    EvalItem("تأخر صرف الرواتب في إحدى الشركات الخاصة", "ar", "negative", "stress"),
    EvalItem("الطلب على السكن الفاخر في أبوظبي يتزايد", "ar", "positive", "opportunity"),
    EvalItem("مخاوف من ركود في قطاع الضيافة بعد تراجع السياحة", "ar", "negative", "stress"),
    EvalItem("إطلاق خدمة توصيل جديدة بأسعار تنافسية", "ar", "positive", "opportunity"),
    EvalItem("إفلاس شركة مقاولات كبرى تاركة آلاف الوظائف مهددة", "ar", "negative", "stress", "no named entity -> systemic stress per v1 rules (named business would be closure)"),
    EvalItem("البنك المركزي خفض الفائدة على الإيداعات", "ar", "positive", "opportunity"),
    EvalItem("أسعار التأمين الصحي ارتفعت بشكل ملحوظ", "ar", "negative", "stress"),
    EvalItem("مبادرة جديدة لتدريب الشباب على البرمجة مجانا", "ar", "positive", "opportunity"),
    EvalItem("القطاع الصناعي في الإمارات يشهد نموا متسارعا", "ar", "positive", "opportunity"),
    EvalItem("تأخر الرحلات في مطار دبي بسبب الأحوال الجوية", "ar", "negative", "stress"),
    EvalItem("مطاعم جديدة تفتح أبوابها في المنطقة السياحية", "ar", "positive", "opportunity"),
    EvalItem("شكاوى مستمرة من جودة الإنترنت في المناطق النائية", "ar", "negative", "stress"),
    EvalItem("الجامعة أعلنت تخفيضات في الرسوم الدراسية", "ar", "positive", "opportunity"),
    EvalItem("سوق العمل يشهد إقبالا على الوظائف التقنية", "ar", "positive", "opportunity"),
    EvalItem("شكرا جزيلا لخدمة العملاء، حلوا مشكلتي بسرعة", "ar", "positive", "neutral", "service praise, no economic signal"),
    EvalItem("الوضع الاقتصادي جيد بشكل عام", "ar", "neutral", "neutral", "vague, no named entity"),
    # ---------------------------------------------------------------- Arabizi
    EvalItem("3ashan el ijar zed kteer, kol 7ada 3am yruh", "arz", "negative", "stress"),
    EvalItem("wallah el shirkah 7alat w saf2at kol el mowazafin", "arz", "negative", "closure"),
    EvalItem("el talabat bta3na ba2a ghali 7elw, mesh 3adil", "arz", "negative", "stress"),
    EvalItem("habibi el mat3am el 7elo fi jumeirah sakkar, 3ala 7sab el ijar", "arz", "negative", "closure"),
    EvalItem("el bank rad 3ala talabi, za3lan", "arz", "negative", "stress"),
    EvalItem("yalla nshuf el market, el as3ar nazele!", "arz", "positive", "opportunity"),
    EvalItem("el hukuma 3amlat system jdid lil tashjer, kull shi ashal", "arz", "positive", "opportunity"),
    EvalItem("3adi, el shakwa mesh muhimmah", "arz", "neutral", "neutral"),
    EvalItem("ana shuft el film akher usbu3, kan 7elo", "arz", "neutral", "neutral", "entertainment, not economic"),
    EvalItem("el metro fi dubai 7elu, sarre3 w nadeef", "arz", "positive", "neutral", "service praise, no economic signal"),
    EvalItem("shu ra'yek bil shirkah el jadidah? ana mesh mota2aked", "arz", "neutral", "neutral"),
    EvalItem("el 7ukuma 3amilah tashji3 lil shabab, barak allah fihom", "arz", "positive", "opportunity"),
    EvalItem("3indi mushkilah ma3 el bank, ma yreddoon 3ala talabati", "arz", "negative", "stress"),
    EvalItem("el as3ar fi el dukaan 3ala el al, kull shi ghaly", "arz", "negative", "stress"),
    # ----------------------------------------------------------------- English
    EvalItem("Rents in Dubai are out of control, families are leaving for Abu Dhabi", "en", "negative", "stress"),
    EvalItem("Tech layoffs hit the DIFC again, 200 engineers let go this week", "en", "negative", "stress"),
    EvalItem("New mega mall opens on Palm Jumeirah, 300 stores", "en", "positive", "opportunity"),
    EvalItem("The National Bank just doubled its profit, shares up 15%", "en", "positive", "opportunity"),
    EvalItem("Uber prices in Dubai are ridiculous now", "en", "negative", "stress"),
    EvalItem("My shawarma place closed after a rent dispute with the landlord", "en", "negative", "closure"),
    EvalItem("I love the new Dubai Metro extension, so convenient", "en", "positive", "neutral", "service praise, no economic signal"),
    EvalItem("Government launches free AI training for citizens", "en", "positive", "opportunity"),
    EvalItem("School fees are going up again next year", "en", "negative", "stress"),
    EvalItem("Emirates announces direct flights to 12 new destinations", "en", "positive", "opportunity"),
    EvalItem("What's the best phone under 2000 dirhams?", "en", "neutral", "neutral", "consumer preference question"),
    EvalItem("Weather is nice today in Dubai", "en", "neutral", "neutral"),
    EvalItem("Great, another rent increase. Just what we needed.", "en", "negative", "stress", "sarcasm - still negative"),
    EvalItem("Salik charges are the best thing ever", "en", "negative", "stress", "sarcasm"),
    EvalItem("Amazing, our flight got cancelled. Fantastic service.", "en", "negative", "neutral", "sarcasm; personal service complaint -> no economic signal"),
    EvalItem("Dubai Real Estate prices hit record high in Q3", "en", "positive", "opportunity"),
    EvalItem("Restaurant industry struggling as costs rise, several closures in Marina", "en", "negative", "closure"),
    EvalItem("New visa reforms expected to boost talent inflow", "en", "positive", "opportunity"),
    EvalItem("Metro service delays frustrate morning commuters", "en", "negative", "stress"),
    EvalItem("Watch this cute cat video", "en", "neutral", "neutral"),
    EvalItem("Why is the internet so expensive in UAE?", "en", "negative", "stress"),
    EvalItem("Delivery app fees are eating my budget", "en", "negative", "stress"),
    EvalItem("Best dental clinic in Abu Dhabi?", "en", "neutral", "neutral", "consumer preference question"),
    EvalItem("Emaar launches new waterfront project", "en", "positive", "opportunity"),
    EvalItem("GCC markets rally after oil price surge", "en", "positive", "opportunity"),
    EvalItem("Salary not paid on time for 3 months, thinking of leaving", "en", "negative", "stress"),
    EvalItem("Anyone know a good gym in Sharjah?", "en", "neutral", "neutral"),
    EvalItem("Great news for renters: another 20% increase next year. Fantastic.", "en", "negative", "stress", "sarcasm"),
    EvalItem("I miss when delivery was free. Now every order has five fees. Love it.", "en", "negative", "stress", "sarcasm"),
]


def items_for_task(task: str) -> list[dict]:
    """Return the dataset payload for a task (schema: eval_datasets.items)."""
    assert task in ("sentiment", "signal")
    out = []
    for it in ITEMS:
        label = it.sentiment if task == "sentiment" else it.signal
        entry = {"text": it.text, "label": label}
        if it.note:
            entry["note"] = it.note
        out.append(entry)
    return out


DATASETS = [
    {"name": "sentiment-seed-v1", "lang": "mixed", "task": "sentiment",
     "items": items_for_task("sentiment")},
    {"name": "signal-seed-v1", "lang": "mixed", "task": "signal",
     "items": items_for_task("signal")},
]
