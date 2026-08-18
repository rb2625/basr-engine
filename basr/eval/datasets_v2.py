"""Eval v2 (Phase 6, Gate 2): the expanded, FRESH evaluation set.

These items are deliberately NOT part of the v1 500-item set: the local
fine-tuned model (basr/nlp/local_model.py) trains on v1, so v2 must be new
texts or the eval would be train-on-test. v2 is weighted toward the weakest
measured class - Arabizi - and the hard filtering traps (sarcasm, personal
complaints that are not economic signals, entertainment/weather factuals).

Each item carries both labels (sentiment + signal), matching the two
classifier tasks. Target: 120 items (40 ar, 40 en, 40 arz).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalItemV2:
    text: str
    lang: str                     # 'ar' | 'arz' | 'en'
    sentiment: str                # positive | negative | neutral | mixed
    signal: str                   # stress | closure | opportunity | neutral
    note: str = ""


ITEMS_V2: list[EvalItemV2] = [
    # ------------------------------------------------------------------ Arabic
    EvalItemV2("الموظفون في الشركة اشتكوا من تأخر الرواتب ثلاثة أشهر متتالية", "ar", "negative", "stress"),
    EvalItemV2("محطة تحلية جديدة بدأت تشغيلها التجريبي في رأس الخيمة", "ar", "positive", "opportunity"),
    EvalItemV2("أصحاب المحلات الصغيرة في السوق المركزي يهددون بالإضراب", "ar", "negative", "stress"),
    EvalItemV2("شركة الطيران الوطنية أعلنت أرباحا قياسية في النصف الأول", "ar", "positive", "opportunity"),
    EvalItemV2("ارتفعت رسوم المدارس الخاصة بنسبة عشرة بالمئة للعام المقبل", "ar", "negative", "stress"),
    EvalItemV2("بنك محلي أطلق تطبيقا جديدا للتحويلات بدون عمولات", "ar", "positive", "opportunity"),
    EvalItemV2("مصنع الألمنيوم خفض الإنتاج بسبب تراجع الطلب العالمي", "ar", "negative", "stress"),
    EvalItemV2("الحكومة خصصت أراض جديدة للمشاريع الصناعية في خليفة", "ar", "positive", "opportunity"),
    EvalItemV2("أسعار الخضار والفواكه ارتفعت بشكل ملحوظ هذا الأسبوع", "ar", "negative", "stress"),
    EvalItemV2("فندق شهير في دبي أغلق أبوابه بعد انتهاء عقود الموظفين", "ar", "negative", "closure"),
    EvalItemV2("الإمارات تحتل المركز الأول في مؤشر التنافسية الرقمية", "ar", "positive", "opportunity"),
    EvalItemV2("التأمين الصحي الجديد غطى خدمات إضافية لكنه رفع الأقساط", "ar", "negative", "stress"),
    EvalItemV2("شكاوى سكانية من ضعف شبكة الإنترنت في الأحياء الجديدة", "ar", "negative", "stress"),
    EvalItemV2("أغلقت ثلاث شركات عقارية مكاتبها في الشارقة هذا الشهر", "ar", "negative", "closure"),
    EvalItemV2("الطلب على الوظائف التقنية زاد بنسبة كبيرة في دبي", "ar", "positive", "opportunity"),
    EvalItemV2("أجور سائقي التوصيل انخفضت مع انتشار المنصات الجديدة", "ar", "negative", "stress"),
    EvalItemV2("مهرجان التسوق الشتوي بدأ بعروض مخفضة واسعة", "ar", "positive", "opportunity"),
    EvalItemV2("شركة الكهرباء أعلنت انقطاعات متكررة خلال الصيف", "ar", "negative", "stress"),
    EvalItemV2("روعة! زيادة أخرى على الإيجار بعد شهرين فقط", "ar", "negative", "stress", "sarcasm"),
    EvalItemV2("الجو جميل اليوم والرياح معتدلة", "ar", "neutral", "neutral", "weather factual"),
    EvalItemV2("أفضل مطعم شاورما في المدينة؟ سمعت عن مكان جديد", "ar", "neutral", "neutral", "consumer question"),
    EvalItemV2("رسوم خدمة التوصيل أصبحت تساوي ثمن الطلب نفسه", "ar", "negative", "stress"),
    EvalItemV2("الدولة خفضت رسوم التأشيرات السياحية لتنشيط القطاع", "ar", "positive", "opportunity"),
    EvalItemV2("الوضع مزري، الأسعار تزيد والرواتب ثابتة منذ سنوات", "ar", "negative", "stress"),
    EvalItemV2("الطاقة الشمسية تشكل الآن ربع إنتاج البلاد", "ar", "positive", "opportunity"),
    EvalItemV2("مطعمي المفضل أغلق لأن الإيجار تضاعف", "ar", "negative", "closure"),
    EvalItemV2("أعلن البنك المركزي عن خفض أسعار الفائدة", "ar", "positive", "opportunity"),
    EvalItemV2("المواصلات العامة أصبحت مزدحمة بشكل لا يطاق", "ar", "negative", "stress"),
    EvalItemV2("مهرجان سينمائي جديد سيقام في دبي هذا الخريف", "ar", "neutral", "neutral", "entertainment"),
    EvalItemV2("حملة لتنظيف الشواطئ بمشاركة آلاف المتطوعين", "ar", "positive", "neutral"),
    EvalItemV2("المعارض التجارية في أبوظبي تتعافى بقوة", "ar", "positive", "opportunity"),
    EvalItemV2("عشرات المطاعم أغلقت في مدينة الملك عبدالله", "ar", "negative", "closure"),
    EvalItemV2("أصبحت الشقق الفندقية أرخص في الموسم الحالي", "ar", "positive", "opportunity"),
    EvalItemV2("منصة حكومية جديدة لتسجيل الأعمال في دقائق", "ar", "positive", "opportunity"),

    # ------------------------------------------------------------------ English
    EvalItemV2("Rents in Abu Dhabi hit another record high this quarter", "en", "negative", "stress"),
    EvalItemV2("A new tech hub opens in Dubai with space for 200 startups", "en", "positive", "opportunity"),
    EvalItemV2("Delivery riders across the city say pay has been cut again", "en", "negative", "stress"),
    EvalItemV2("Emirates airline adds 12 new routes for winter", "en", "positive", "opportunity"),
    EvalItemV2("My favorite bookstore in Al Fahidi closed after 20 years", "en", "negative", "closure"),
    EvalItemV2("The weather in Dubai is great for beach days right now", "en", "neutral", "neutral", "weather factual"),
    EvalItemV2("Traffic on Sheikh Zayed Road is worse than ever at rush hour", "en", "negative", "stress"),
    EvalItemV2("Salik introduced another toll gate without any warning", "en", "negative", "stress"),
    EvalItemV2("UAE startup raises $50M to expand into Saudi Arabia", "en", "positive", "opportunity"),
    EvalItemV2("Two malls in Sharjah are converting floors into offices", "en", "neutral", "opportunity"),
    EvalItemV2("Oh wonderful, my rent doubled. Exactly what I needed", "en", "negative", "stress", "sarcasm"),
    EvalItemV2("Fresh produce prices jump after the heatwave", "en", "negative", "stress"),
    EvalItemV2("A major hotel brand opens its first property in Ras Al Khaimah", "en", "positive", "opportunity"),
    EvalItemV2("Gym membership auto-renewed at double the price. Fantastic", "en", "negative", "stress", "sarcasm"),
    EvalItemV2("Construction delays push back two big project launches", "en", "negative", "stress"),
    EvalItemV2("Government waives business license fees for home businesses", "en", "positive", "opportunity"),
    EvalItemV2("The new park in Jumeirah Village is lovely", "en", "positive", "neutral"),
    EvalItemV2("Best budget phone in Dubai under 500 dirhams?", "en", "neutral", "neutral", "consumer question"),
    EvalItemV2("Insurance renewal went up 40% with no explanation", "en", "negative", "stress"),
    EvalItemV2("Food delivery fees now cost more than the meal", "en", "negative", "stress"),
    EvalItemV2("A legacy fish market shuts down, vendors lose their income", "en", "negative", "closure"),
    EvalItemV2("Office rents in Business Bay finally stabilize", "en", "positive", "opportunity"),
    EvalItemV2("Dubai named the most popular remote-work city again", "en", "positive", "opportunity"),
    EvalItemV2("A popular chain of pharmacies closes 8 branches in the north", "en", "negative", "closure"),
    EvalItemV2("The weekend festival was fun but parking was a nightmare", "en", "neutral", "neutral"),
    EvalItemV2("Mortgage rates inch up for the sixth straight month", "en", "negative", "stress"),
    EvalItemV2("UAE inflation slows to 1.8%, the lowest in three years", "en", "positive", "opportunity"),
    EvalItemV2("A new desalination plant secures Fujairah water supply", "en", "positive", "opportunity"),
    EvalItemV2("Visa processing delays leave hundreds of families waiting", "en", "negative", "stress"),
    EvalItemV2("The startup scene in Abu Dhabi is getting real investment", "en", "positive", "opportunity"),
    EvalItemV2("Tenants complain about maintenance that never happens", "en", "negative", "stress"),

    # ------------------------------------------------------------------ Arabizi
    EvalItemV2("el 2ejar zed kteer hada el 3am, ma fi 2ad", "arz", "negative", "stress"),
    EvalItemV2("el shirkah 7alat, 2afsat kol el 3ommal", "arz", "negative", "closure"),
    EvalItemV2("el 7ukomah 3amlat 2e7sa2at 2aktar lal 2awam el jadideh, kol shi 2a7san", "arz", "positive", "opportunity"),
    EvalItemV2("el as3ar 3am t3alla kol youm, mesh 3arfeen shu nishtari", "arz", "negative", "stress"),
    EvalItemV2("bta3 el ma3ash 3am yt2akhar 3ala el 2awam, 5alas", "arz", "negative", "stress"),
    EvalItemV2("el 2as3ar rakhisat 3al akheer, 7amdella", "arz", "positive", "opportunity"),
    EvalItemV2("el shirkah waffat 2an el 2entej, kull shi wa2af", "arz", "negative", "closure"),
    EvalItemV2("el 7ukomah 2alelet 2ojoor el 2awam, 7elu", "arz", "positive", "opportunity"),
    EvalItemV2("el 2iskan 3ala el 2al, el 2awam mesh 3ayesheen", "arz", "negative", "stress"),
    EvalItemV2("el shirkah 3ayyant mowazafin jodod, 2akhbar 7elweh", "arz", "positive", "opportunity"),
    EvalItemV2("el ma3ishah sa2at, kol shi 2erghla", "arz", "negative", "stress"),
    EvalItemV2("7elu kteer! zedou 2al 2ejar 2a3ad", "arz", "negative", "stress", "sarcasm"),
    EvalItemV2("el 5edmah el 2amniah 7elweh, 7amdella", "arz", "positive", "neutral"),
    EvalItemV2("2a7san shawerma fel sheikh zayed?", "arz", "neutral", "neutral", "consumer question"),
    EvalItemV2("el mo2asasah 2afalsat 2ams, 5alas khalas", "arz", "negative", "closure"),
    EvalItemV2("el 2as3ar 2a7san min 2abl, kol shi 2erkhass", "arz", "positive", "opportunity"),
    EvalItemV2("el shughl 3am ykhsir, el 5awf 3ala el mizaneeyah", "arz", "negative", "stress"),
    EvalItemV2("el 3amal el jaded 3am yzid, el shirkah tawzaf kteer", "arz", "positive", "opportunity"),
    EvalItemV2("el 2usbu3 el jay 3am nfta7 2afran jadid, mabrook", "arz", "positive", "opportunity"),
    EvalItemV2("el bank 3am ywase3 khidmatoh, 7elu kteer", "arz", "positive", "opportunity"),
    EvalItemV2("el 7ukomah rafa3at 2al tashji3at lal 2iskan, 2akhbar 7elweh", "arz", "positive", "opportunity"),
    EvalItemV2("el 2ejar 3ala el 2al, mesh 2aderen n2a3ash", "arz", "negative", "stress"),
    EvalItemV2("el 2as3ar 3am y2allebo kol youm, ma fi 2ade", "arz", "negative", "stress"),
    # Fresh Arabizi items (verified no overlap with v1)
    EvalItemV2("el ijar zed b2a 2ad qima, ma fi 2amal khalas", "arz", "negative", "stress"),
    EvalItemV2("el wazifa ba2at 3ala el 2awam tawil, 7aram keda", "arz", "negative", "stress"),
    EvalItemV2("el sicaret 2alla3 2asri, ma ba2a fi 7al", "arz", "negative", "stress"),
    EvalItemV2("el 2awam ma 3ndhum flus yakhdo 2akl 2al bayt", "arz", "negative", "stress"),
    EvalItemV2("el mawasim el barideh 5allasat, el 2as3ar zadt", "arz", "negative", "stress"),
    EvalItemV2("el wazeefeh el jadideh ma t2abil 2al 2awam", "arz", "negative", "stress"),
    EvalItemV2("el sharika el kobra 5allasat, saf2at kol el nas", "arz", "negative", "closure"),
    EvalItemV2("el ma7al el 7elo fi market sakkar, ba2a khali", "arz", "negative", "closure"),
    EvalItemV2("el jihaz el jadid sarre3, 2a7san men 2abl kteer", "arz", "positive", "opportunity"),
    EvalItemV2("el 2amaken el hadideh sara3at w nadeefah, 7elo", "arz", "positive", "opportunity"),
    EvalItemV2("el 7ukuma 3amlat mashru3 jdid, 2awam 3azimah", "arz", "positive", "opportunity"),
    EvalItemV2("el 2akl fi el mat3am 7elo w rkhis, shukran", "arz", "positive", "opportunity"),
    EvalItemV2("3adi, el 7alat 3adiyah, ma fi 2adish", "arz", "neutral", "neutral"),
    EvalItemV2("shu raayek bil new metro? ana ma jarrabt", "arz", "neutral", "neutral"),
    EvalItemV2("el 2amaken el jadideh fi dubai, ma 3raft lau 7elweh", "arz", "neutral", "neutral"),
]


def items_for_task_v2(task: str) -> list[dict]:
    """Return the v2 dataset payload for a task (schema: eval_datasets.items)."""
    assert task in ("sentiment", "signal")
    out = []
    for it in ITEMS_V2:
        label = it.sentiment if task == "sentiment" else it.signal
        entry = {"text": it.text, "label": label}
        if it.note:
            entry["note"] = it.note
        out.append(entry)
    return out


DATASETS_V2 = [
    {"name": "sentiment-v2", "lang": "mixed", "task": "sentiment",
     "items": items_for_task_v2("sentiment")},
# Fresh Arabizi items (verified no overlap with v1)
    EvalItemV2("el ijar zed b2a 2ad qima, ma fi 2amal khalas", "arz", "negative", "stress"),
    EvalItemV2("el wazifa ba2at 3ala el 2awam tawil, 7aram keda", "arz", "negative", "stress"),
    EvalItemV2("el sicaret 2alla3 2asri, ma ba2a fi 7al", "arz", "negative", "stress"),
    EvalItemV2("el 2awam ma 3ndhum flus yakhdo 2akl 2al bayt", "arz", "negative", "stress"),
    EvalItemV2("el mawasim el barideh 5allasat, el 2as3ar zadt", "arz", "negative", "stress"),
    EvalItemV2("el wazeefeh el jadideh ma t2abil 2al 2awam", "arz", "negative", "stress"),
    EvalItemV2("el sharika el kobra 5allasat, saf2at kol el nas", "arz", "negative", "closure"),
    EvalItemV2("el ma7al el 7elo fi market sakkar, ba2a khali", "arz", "negative", "closure"),
    EvalItemV2("el jihaz el jadid sarre3, 2a7san men 2abl kteer", "arz", "positive", "opportunity"),
    EvalItemV2("el 2amaken el hadideh sara3at w nadeefah, 7elo", "arz", "positive", "opportunity"),
    EvalItemV2("el 7ukuma 3amlat mashru3 jdid, 2awam 3azimah", "arz", "positive", "opportunity"),
    EvalItemV2("el 2akl fi el mat3am 7elo w rkhis, shukran", "arz", "positive", "opportunity"),
    EvalItemV2("3adi, el 7alat 3adiyah, ma fi 2adish", "arz", "neutral", "neutral"),
    EvalItemV2("shu raayek bil new metro? ana ma jarrabt", "arz", "neutral", "neutral"),
    EvalItemV2("el 2amaken el jadideh fi dubai, ma 3raft lau 7elweh", "arz", "neutral", "neutral"),
# Fresh Arabizi items (verified no overlap with v1)
    EvalItemV2("el ijar zed b2a 2ad qima, ma fi 2amal khalas", "arz", "negative", "stress"),
    EvalItemV2("el wazifa ba2at 3ala el 2awam tawil, 7aram keda", "arz", "negative", "stress"),
    EvalItemV2("el sicaret 2alla3 2asri, ma ba2a fi 7al", "arz", "negative", "stress"),
    EvalItemV2("el 2awam ma 3ndhum flus yakhdo 2akl 2al bayt", "arz", "negative", "stress"),
    EvalItemV2("el mawasim el barideh 5allasat, el 2as3ar zadt", "arz", "negative", "stress"),
    EvalItemV2("el wazeefeh el jadideh ma t2abil 2al 2awam", "arz", "negative", "stress"),
    EvalItemV2("el sharika el kobra 5allasat, saf2at kol el nas", "arz", "negative", "closure"),
    EvalItemV2("el ma7al el 7elo fi market sakkar, ba2a khali", "arz", "negative", "closure"),
    EvalItemV2("el jihaz el jadid sarre3, 2a7san men 2abl kteer", "arz", "positive", "opportunity"),
    EvalItemV2("el 2amaken el hadideh sara3at w nadeefah, 7elo", "arz", "positive", "opportunity"),
    EvalItemV2("el 7ukuma 3amlat mashru3 jdid, 2awam 3azimah", "arz", "positive", "opportunity"),
    EvalItemV2("el 2akl fi el mat3am 7elo w rkhis, shukran", "arz", "positive", "opportunity"),
    EvalItemV2("3adi, el 7alat 3adiyah, ma fi 2adish", "arz", "neutral", "neutral"),
    EvalItemV2("shu raayek bil new metro? ana ma jarrabt", "arz", "neutral", "neutral"),
    EvalItemV2("el 2amaken el jadideh fi dubai, ma 3raft lau 7elweh", "arz", "neutral", "neutral"),
    {"name": "signal-v2", "lang": "mixed", "task": "signal",
     "items": items_for_task_v2("signal")},
]
