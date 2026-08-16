"""Eval sets for the BASR classifiers (Phase 2, sec 6.7 + sec 11).

Every item carries two labels - ``sentiment`` and ``signal`` - matching the two
headline classifier tasks. The full v1 target is **500 labeled items**; this
module ships a curated seed (187) that covers Arabic (MSA + Gulf), Arabizi,
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
    # ------------------------------------------------- batch 2 (toward 500)
    # Arabic
    EvalItem("الطلب على الشقق في دبي انخفض بعد ارتفاع الأسعار", "ar", "negative", "stress"),
    EvalItem("مطار دبي الجديد سيستقبل 260 مليون مسافر سنويا", "ar", "positive", "opportunity"),
    EvalItem("الرواتب في القطاع الخاص ارتفعت بنسبة خمسة بالمئة", "ar", "positive", "opportunity"),
    EvalItem("متاجر التجزئة تشهد تراجعا في المبيعات هذا الربع", "ar", "negative", "stress"),
    EvalItem("افتتاح مستشفى جديد في دبي يضم ثلاثمائة سرير", "ar", "positive", "opportunity"),
    EvalItem("شركة إعمار أعلنت أرباحا قياسية في النصف الأول", "ar", "positive", "opportunity"),
    EvalItem("أسعار الذهب في دبي وصلت أعلى مستوى لها", "ar", "negative", "stress"),
    EvalItem("الطلاب يشكون من ارتفاع رسوم المدارس الخاصة", "ar", "negative", "stress"),
    EvalItem("حكومة دبي أطلقت مبادرة المدن الذكية", "ar", "positive", "opportunity"),
    EvalItem("أزمة السكن في أبوظبي تتفاقم بسبب نقص الوحدات", "ar", "negative", "stress"),
    EvalItem("إفلاس متجر إلكتروني شهير في الإمارات", "ar", "negative", "closure"),
    EvalItem("البنك المركزي رفع الفائدة على القروض", "ar", "negative", "stress"),
    EvalItem("شركة طيران جديدة تطلق رحلات إلى دبي", "ar", "positive", "opportunity"),
    EvalItem("مقاهي دبي تستمر في الازدهار رغم المنافسة", "ar", "positive", "opportunity"),
    EvalItem("قطاع العقارات في الشارقة يشهد نموا ملحوظا", "ar", "positive", "opportunity"),
    EvalItem("تأخر مشاريع البنية التحتية في العين", "ar", "negative", "stress"),
    EvalItem("الحكومة أعلنت عن خطة دعم للشركات الصغيرة", "ar", "positive", "opportunity"),
    EvalItem("أسعار الطعام في المطاعم ارتفعت بشكل ملحوظ", "ar", "negative", "stress"),
    EvalItem("شركة أدنوك تعلن عن استثمارات جديدة في الطاقة", "ar", "positive", "opportunity"),
    EvalItem("تسريح جماعي في شركة تقنية في دبي", "ar", "negative", "stress"),
    EvalItem("افتتاح أول متجر أبل في دبي مول", "ar", "positive", "opportunity"),
    EvalItem("المواصلات العامة في دبي تشهد ازدحاما شديدا", "ar", "negative", "stress"),
    EvalItem("جامعة خليفة تحصل على تمويل جديد للأبحاث", "ar", "positive", "opportunity"),
    EvalItem("إغلاق مصنع في المنطقة الصناعية بالشارقة", "ar", "negative", "closure"),
    EvalItem("أسعار التأمين على السيارات زادت هذا العام", "ar", "negative", "stress"),
    EvalItem("شركة ناشئة إماراتية تجمع استثمارا كبيرا", "ar", "positive", "opportunity"),
    EvalItem("مستشفى خاص يواجه تحقيقا بعد شكاوى المرضى", "ar", "negative", "stress"),
    EvalItem("دبي تستضيف معرضا عالميا جديدا", "ar", "positive", "opportunity"),
    EvalItem("الضرائب الجديدة أثرت على أرباح المطاعم الصغيرة", "ar", "negative", "stress"),
    EvalItem("سوق العمل الإماراتي يجذب المواهب العالمية", "ar", "positive", "opportunity"),
    EvalItem("أغلقت شركة سياحة أبوابها في أبوظبي", "ar", "negative", "closure"),
    EvalItem("ارتفاع فواتير الكهرباء في الصيف", "ar", "negative", "stress"),
    EvalItem("منصة رقمية جديدة لتسجيل الشركات في دقيقة", "ar", "positive", "opportunity"),
    EvalItem("الوضع الجوي ممتاز اليوم في دبي", "ar", "neutral", "neutral", "weather, no economic signal"),
    EvalItem("شكرا لموظفي مترو دبي على التعامل الرائع", "ar", "positive", "neutral", "service praise"),
    EvalItem("أين أفضل مكان لشراء هاتف؟", "ar", "neutral", "neutral", "consumer preference question"),
    EvalItem("الفيلم الجديد في السينما كان جميلا", "ar", "neutral", "neutral", "entertainment"),
    EvalItem("شركة الاتصالات تعلن عن باقات أرخص للإنترنت", "ar", "positive", "opportunity"),
    EvalItem("ارتفاع أسعار الإيجار في الشارقة يدفع العائلات للانتقال", "ar", "negative", "stress"),
    EvalItem("طيران الإمارات يزيد عدد الرحلات إلى آسيا", "ar", "positive", "opportunity"),
    # English
    EvalItem("Rental prices in Abu Dhabi jumped another 15% this year", "en", "negative", "stress"),
    EvalItem("New free zone launches with tax incentives for startups", "en", "positive", "opportunity"),
    EvalItem("Two more gyms closed in Marina this month", "en", "negative", "closure"),
    EvalItem("Salaries in the banking sector are rising faster than inflation", "en", "positive", "opportunity"),
    EvalItem("The new Dubai airport expansion is ahead of schedule", "en", "positive", "opportunity"),
    EvalItem("Delivery workers report longer shifts and lower pay", "en", "negative", "stress"),
    EvalItem("Emaar reports record sales in Q2", "en", "positive", "opportunity"),
    EvalItem("School bus fees increased by 10% for next year", "en", "negative", "stress"),
    EvalItem("UAE launches digital visa platform for remote workers", "en", "positive", "opportunity"),
    EvalItem("Hospital wait times in public clinics are getting worse", "en", "negative", "stress"),
    EvalItem("Another food delivery startup shut down in Dubai", "en", "negative", "closure"),
    EvalItem("Dubai property developers announce 50 new projects", "en", "positive", "opportunity"),
    EvalItem("Utility bills doubled this summer, residents frustrated", "en", "negative", "stress"),
    EvalItem("New direct flight connects Dubai to 30 more cities", "en", "positive", "opportunity"),
    EvalItem("Bank loan rejection rate rises among small businesses", "en", "negative", "stress"),
    EvalItem("AURAK signs partnership with German university", "en", "positive", "opportunity"),
    EvalItem("Groceries cost noticeably more this month", "en", "negative", "stress"),
    EvalItem("Etihad announces record passenger numbers", "en", "positive", "opportunity"),
    EvalItem("Parking fees at malls are getting out of hand", "en", "negative", "stress"),
    EvalItem("New AI company opens headquarters in DIFC", "en", "positive", "opportunity"),
    EvalItem("Tenant evictions rise as rents outpace salaries", "en", "negative", "stress"),
    EvalItem("Dubai Metro extends service to new areas", "en", "positive", "opportunity"),
    EvalItem("Salik hikes toll prices again", "en", "negative", "stress"),
    EvalItem("Startup funding in the UAE hit an all-time high", "en", "positive", "opportunity"),
    EvalItem("Pharmacy chain closes 5 branches after losses", "en", "negative", "closure"),
    EvalItem("Traffic on Sheikh Zayed Road is unbearable in the evenings", "en", "negative", "stress"),
    EvalItem("Government scholarship covers tuition for 10,000 students", "en", "positive", "opportunity"),
    EvalItem("Inflation is eating into household budgets across the Emirates", "en", "negative", "stress"),
    EvalItem("New hotel opens on Yas Island with 800 rooms", "en", "positive", "opportunity"),
    EvalItem("Construction companies report slower payments from developers", "en", "negative", "stress"),
    EvalItem("Free coding bootcamps announced for UAE citizens", "en", "positive", "opportunity"),
    EvalItem("Coffee shop prices in Dubai are now higher than London", "en", "negative", "stress"),
    EvalItem("ADNOC signs major LNG export deal", "en", "positive", "opportunity"),
    EvalItem("Small retailers struggle as online shopping grows", "en", "negative", "stress"),
    EvalItem("Dubai South gets a new logistics hub", "en", "positive", "opportunity"),
    EvalItem("Wow, another fee increase. Absolutely fantastic.", "en", "negative", "stress", "sarcasm"),
    EvalItem("I just love paying Salik every single day.", "en", "negative", "stress", "sarcasm"),
    EvalItem("Best burger place in Al Barsha?", "en", "neutral", "neutral", "consumer preference question"),
    EvalItem("The weather in Abu Dhabi is lovely today", "en", "neutral", "neutral"),
    EvalItem("Has anyone tried the new bus route to DIFC?", "en", "neutral", "neutral"),
    EvalItem("My favorite thing is waiting an hour for a delivery", "en", "negative", "stress", "sarcasm"),
    EvalItem("Rent check bounced, landlord gave us 30 days", "en", "negative", "stress"),
    EvalItem("New Emirati fashion brand opens flagship store", "en", "positive", "opportunity"),
    EvalItem("Visa processing times tripled this month", "en", "negative", "stress"),
    EvalItem("DIFC reports record company registrations", "en", "positive", "opportunity"),
    # Arabizi
    EvalItem("el ijar fi dubai kteer ghali, kol sana zayed", "arz", "negative", "stress"),
    EvalItem("el shirkah iflasat w sakkaret kol el furoo3", "arz", "negative", "closure"),
    EvalItem("el 7ukuma fat7at markaz jdid lil istithmar", "arz", "positive", "opportunity"),
    EvalItem("el ma3ashat ghalyan w ma fi zyada bil rwatib", "arz", "negative", "stress"),
    EvalItem("3andak el metro jdid, kull shi ashal", "arz", "positive", "neutral", "service praise"),
    EvalItem("el bank rafa3 el fawayed, mesh mertah", "arz", "negative", "stress"),
    EvalItem("fata7o mall jdid fi sharjah, 7elu kteer", "arz", "positive", "opportunity"),
    EvalItem("el zaw3ameh fi tarek sheikh zayed aswa min ay wa2t", "arz", "negative", "stress"),
    EvalItem("shirkit el tech taradet 200 mowazaf", "arz", "negative", "stress"),
    EvalItem("el talabat wala 7ada yeradd, 3am y3amlo 3ala el 5afif", "arz", "negative", "stress"),
    EvalItem("7elwa el mubadara el jadidah lil shabab", "arz", "positive", "opportunity"),
    EvalItem("el as3ar el youm 7ilwa, kol shi nazele!", "arz", "positive", "opportunity"),
    EvalItem("yalla nshuf, el sakan mesh 3adil fi dubai", "arz", "negative", "stress"),
    EvalItem("el jame3a 3amilat takhfidat lil rusum", "arz", "positive", "opportunity"),
    EvalItem("mesh 3aref, ana bas shari mobayil jdid", "arz", "neutral", "neutral", "personal, no economic signal"),
    EvalItem("el filim kan 7elu bas tawil", "arz", "neutral", "neutral", "entertainment"),
    EvalItem("shu ahsan mat3am fi al barsha?", "arz", "neutral", "neutral", "consumer preference question"),
    EvalItem("el 7ukuma 3amilat system tashji3 lil mustathmareen", "arz", "positive", "opportunity"),
    EvalItem("el shirkah sakkaret el bab w tal3at men el su2", "arz", "negative", "closure"),
    EvalItem("ma fi shughl, kol el nas bat3at 3an shughl", "arz", "negative", "stress"),
    EvalItem("el mawasefat el 3ama t7assanat kteer", "arz", "positive", "neutral", "service praise"),
    EvalItem("el as3ar nazele 3al akheer, kull shi arkhas", "arz", "positive", "opportunity"),
    EvalItem("walaw, el shakwa mesh muhimmah", "arz", "neutral", "neutral"),
    EvalItem("3indi mushkilah ma3 el internet, ma yreddoon", "arz", "negative", "stress"),
    EvalItem("el bank 7al mushkilti bsur3a, shukran", "arz", "positive", "neutral", "service praise"),
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
