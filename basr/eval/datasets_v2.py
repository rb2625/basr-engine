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
    EvalItemV2("سوق دبي المالي سجل أعلى مستوى له منذ خمس سنوات", "ar", "positive", "opportunity"),
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
    EvalItemV2("التأمين الصحي الجديد غطى خدمات إضافية لكنه رفع الأقساط", "ar", "mixed", "stress"),
    EvalItemV2("شكاوى سكانية من ضعف شبكة الإنترنت في الأحياء الجديدة", "ar", "negative", "stress"),
    EvalItemV2("مطاعم منطقة الواجهة البحرية تشهد رواجا غير مسبوق", "ar", "positive", "opportunity"),
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
    EvalItemV2("شقة جديدة في العين بأسعار معقولة مقارنة بالعام الماضي", "ar", "positive", "opportunity"),
    EvalItemV2("مطعمي المفضل أغلق لأن الإيجار تضاعف", "ar", "negative", "closure"),
    EvalItemV2("أعلن البنك المركزي عن خفض أسعار الفائدة", "ar", "positive", "opportunity"),
    EvalItemV2("المواصلات العامة أصبحت مزدحمة بشكل لا يطاق", "ar", "negative", "stress"),
    EvalItemV2("مهرجان سينمائي جديد سيقام في دبي هذا الخريف", "ar", "neutral", "neutral", "entertainment"),
    EvalItemV2("حملة لتنظيف الشواطئ بمشاركة آلاف المتطوعين", "ar", "positive", "neutral"),
    EvalItemV2("المعارض التجارية في أبوظبي تتعافى بقوة", "ar", "positive", "opportunity"),
    EvalItemV2("عشرات المطاعم أغلقت في مدينة الملك عبدالله", "ar", "negative", "closure"),
    EvalItemV2("خدمة العملاء في الشركة سيئة جدا ولا أحد يرد", "ar", "negative", "stress"),
    EvalItemV2("المستشفى الجديد يفتح أبوابه الأسبوع القادم", "ar", "positive", "opportunity"),
    EvalItemV2("أصبحت الشقق الفندقية أرخص في الموسم الحالي", "ar", "positive", "opportunity"),
    EvalItemV2("العاملون في المقاهي يعانون من ساعات عمل طويلة", "ar", "negative", "stress"),
    EvalItemV2("منصة حكومية جديدة لتسجيل الأعمال في دقائق", "ar", "positive", "opportunity"),

    # ------------------------------------------------------------------ English
    EvalItemV2("Rents in Abu Dhabi hit another record high this quarter", "en", "negative", "stress"),
    EvalItemV2("A new tech hub opens in Dubai with space for 200 startups", "en", "positive", "opportunity"),
    EvalItemV2("Delivery riders across the city say pay has been cut again", "en", "negative", "stress"),
    EvalItemV2("Emirates airline adds 12 new routes for winter", "en", "positive", "opportunity"),
    EvalItemV2("My favorite bookstore in Al Fahidi closed after 20 years", "en", "negative", "closure"),
    EvalItemV2("The weather in Dubai is great for beach days right now", "en", "neutral", "neutral", "weather factual"),
    EvalItemV2("School fees freeze for the third year in a row", "en", "positive", "opportunity"),
    EvalItemV2("Traffic on Sheikh Zayed Road is worse than ever at rush hour", "en", "negative", "stress"),
    EvalItemV2("Salik introduced another toll gate without any warning", "en", "negative", "stress"),
    EvalItemV2("UAE startup raises $50M to expand into Saudi Arabia", "en", "positive", "opportunity"),
    EvalItemV2("Two malls in Sharjah are converting floors into offices", "en", "mixed", "opportunity"),
    EvalItemV2("Oh wonderful, my rent doubled. Exactly what I needed", "en", "negative", "stress", "sarcasm"),
    EvalItemV2("The new metro extension cuts my commute in half", "en", "positive", "opportunity"),
    EvalItemV2("Fresh produce prices jump after the heatwave", "en", "negative", "stress"),
    EvalItemV2("A major hotel brand opens its first property in Ras Al Khaimah", "en", "positive", "opportunity"),
    EvalItemV2("Gym membership auto-renewed at double the price. Fantastic", "en", "negative", "stress", "sarcasm"),
    EvalItemV2("Construction delays push back two big project launches", "en", "negative", "stress"),
    EvalItemV2("Government waives business license fees for home businesses", "en", "positive", "opportunity"),
    EvalItemV2("The new park in Jumeirah Village is lovely", "en", "positive", "neutral"),
    EvalItemV2("Best budget phone in Dubai under 500 dirhams?", "en", "neutral", "neutral", "consumer question"),
    EvalItemV2("Insurance renewal went up 40% with no explanation", "en", "negative", "stress"),
    EvalItemV2("Food delivery fees now cost more than the meal", "en", "negative", "stress"),
    EvalItemV2("Salaries in fintech are rising faster than any other sector", "en", "positive", "opportunity"),
    EvalItemV2("A legacy fish market shuts down, vendors lose their income", "en", "negative", "closure"),
    EvalItemV2("Flights were delayed three hours but the airline compensated us", "en", "mixed", "neutral"),
    EvalItemV2("Gold prices dip and shoppers flock to the souq", "en", "positive", "opportunity"),
    EvalItemV2("Office rents in Business Bay finally stabilize", "en", "positive", "opportunity"),
    EvalItemV2("My package has been stuck in customs for three weeks", "en", "negative", "stress"),
    EvalItemV2("Dubai named the most popular remote-work city again", "en", "positive", "opportunity"),
    EvalItemV2("A popular chain of pharmacies closes 8 branches in the north", "en", "negative", "closure"),
    EvalItemV2("The weekend festival was fun but parking was a nightmare", "en", "mixed", "neutral"),
    EvalItemV2("Mortgage rates inch up for the sixth straight month", "en", "negative", "stress"),
    EvalItemV2("UAE inflation slows to 1.8%, the lowest in three years", "en", "positive", "opportunity"),
    EvalItemV2("Cafeteria at my office raised prices again", "en", "negative", "stress"),
    EvalItemV2("A new desalination plant secures Fujairah water supply", "en", "positive", "opportunity"),
    EvalItemV2("Online grocery orders are now delivered within an hour", "en", "positive", "opportunity"),
    EvalItemV2("Visa processing delays leave hundreds of families waiting", "en", "negative", "stress"),
    EvalItemV2("The startup scene in Abu Dhabi is getting real investment", "en", "positive", "opportunity"),
    EvalItemV2("Tenants complain about maintenance that never happens", "en", "negative", "stress"),
    EvalItemV2("A logistics firm cuts 200 jobs as demand slows", "en", "negative", "closure"),

    # ------------------------------------------------------------------ Arabizi
    EvalItemV2("el 2ejar zed kteer hada el 3am, ma fi 2ad", "arz", "negative", "stress"),
    EvalItemV2("el shirkah 7alat, 2afsat kol el 3ommal", "arz", "negative", "closure"),
    EvalItemV2("el 7ukomah 3amlat 2e7sa2at 2aktar lal 2awam el jadideh, kol shi 2a7san", "arz", "positive", "opportunity"),
    EvalItemV2("el metro sara3, 2a7san min 2abl kteer", "arz", "positive", "opportunity"),
    EvalItemV2("el as3ar 3am t3alla kol youm, mesh 3arfeen shu nishtari", "arz", "negative", "stress"),
    EvalItemV2("bta3 el ma3ash 3am yt2akhar 3ala el 2awam, 5alas", "arz", "negative", "stress"),
    EvalItemV2("el 2amaken el jadideh 7elweh, mabrook lal 2awam", "arz", "positive", "opportunity"),
    EvalItemV2("el bank 3am ykhaser 3amala, el 2awam 2etelef", "arz", "negative", "closure"),
    EvalItemV2("el 5edmah fel bank sare3a 2awi, shukran", "arz", "positive", "opportunity"),
    EvalItemV2("el 2as3ar rakhisat 3al akheer, 7amdella", "arz", "positive", "opportunity"),
    EvalItemV2("el shirkah waffat 2an el 2entej, kull shi wa2af", "arz", "negative", "closure"),
    EvalItemV2("el zaw2ameh fel sha2e3 2aswa3 min 2abl", "arz", "negative", "stress"),
    EvalItemV2("el 7ukomah 2alelet 2ojoor el 2awam, 7elu", "arz", "positive", "opportunity"),
    EvalItemV2("3am n2affel 2abwaab el 5idmet, ma fi 2amal", "arz", "negative", "closure"),
    EvalItemV2("el 2iskan 3ala el 2al, el 2awam mesh 3ayesheen", "arz", "negative", "stress"),
    EvalItemV2("el tawseel b2a 2asra3 2awi, 7elu", "arz", "positive", "opportunity"),
    EvalItemV2("el shirkah 3ayyant mowazafin jodod, 2akhbar 7elweh", "arz", "positive", "opportunity"),
    EvalItemV2("el 5adamah 2a2tar 5erbah, 2asif 2awi", "arz", "negative", "stress"),
    EvalItemV2("el bank 7al 2eshkilti 3ala 2asra3 wa2t, shukran", "arz", "positive", "opportunity"),
    EvalItemV2("el ma3ishah sa2at, kol shi 2erghla", "arz", "negative", "stress"),
    EvalItemV2("7elu kteer! zedou 2al 2ejar 2a3ad", "arz", "negative", "stress", "sarcasm"),
    EvalItemV2("el 2a7wal el jadideh 7elweh, 2a7san men 2abl", "arz", "positive", "opportunity"),
    EvalItemV2("el 5edmah el 2amniah 7elweh, 7amdella", "arz", "positive", "neutral"),
    EvalItemV2("2a7san shawerma fel sheikh zayed?", "arz", "neutral", "neutral", "consumer question"),
    EvalItemV2("el mo2asasah 2afalsat 2ams, 5alas khalas", "arz", "negative", "closure"),
    EvalItemV2("el 2as3ar 2a7san min 2abl, kol shi 2erkhass", "arz", "positive", "opportunity"),
    EvalItemV2("el shughl 3am ykhsir, el 5awf 3ala el mizaneeyah", "arz", "negative", "stress"),
    EvalItemV2("el 3amal el jaded 3am yzid, el shirkah tawzaf kteer", "arz", "positive", "opportunity"),
    EvalItemV2("el 2awam 3am yz3aloo men el 2ojoor", "arz", "negative", "stress"),
    EvalItemV2("el 2usbu3 el jay 3am nfta7 2afran jadid, mabrook", "arz", "positive", "opportunity"),
    EvalItemV2("el 2amaken el 3amah mesh nazeefeh, 5alas", "arz", "negative", "stress"),
    EvalItemV2("el bank 3am ywase3 khidmatoh, 7elu kteer", "arz", "positive", "opportunity"),
    EvalItemV2("el 5edmah 2et2akharet 3ala el 2awam, mesh 3arfeen", "arz", "negative", "stress"),
    EvalItemV2("el 7ukomah rafa3at 2al tashji3at lal 2iskan, 2akhbar 7elweh", "arz", "positive", "opportunity"),
    EvalItemV2("el 2ejar 3ala el 2al, mesh 2aderen n2a3ash", "arz", "negative", "stress"),
    EvalItemV2("el shirkah 2ete2asat 2al 2amal, 2akhbar 2a7san", "arz", "positive", "opportunity"),
    EvalItemV2("el 5ayet 2a2tar 5erbah, kol shi 3am yt2akhar", "arz", "negative", "stress"),
    EvalItemV2("el 2amaken el jadideh tistghil, 2awam 3azimah", "arz", "positive", "opportunity"),
    EvalItemV2("el 2as3ar 3am y2allebo kol youm, ma fi 2ade", "arz", "negative", "stress"),
    EvalItemV2("el 3amal el jadid 7elo, 2a7san men 2abl kteer", "arz", "positive", "opportunity"),
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
    {"name": "signal-v2", "lang": "mixed", "task": "signal",
     "items": items_for_task_v2("signal")},
]
