# HackerNews Show HN Post

---

**Show HN: BASR -- Free real-time UAE sentiment intelligence with Arabizi support**

https://dashboard-gamma-roan-31.vercel.app

BASR ( Arabic for "insight") is a free, open-source sentiment intelligence platform for the UAE. It monitors Reddit, news RSS, YouTube comments, App Store reviews, and Bluesky -- in Arabic, Arabizi, and English -- classifies sentiment, detects anomalies, and delivers alerts via Telegram.

**What makes it different:**

1. **Arabizi support.** Most Arabic NLP tools handle formal Arabic. This handles how millions of Gulf residents actually type -- "3ashan", "khalas", "yalla" -- using a published library with 1,155 learned Gulf word readings ([ArabiziKit](https://github.com/rb2625/arabizi-kit)).

2. **3-tier hybrid classification.** Local n-gram model (instant, zero API calls) for the clear-cut majority. Lexicon fallback. LLM only for genuinely ambiguous items. 80%+ of docs classified without any API call.

3. **Zero-cost architecture.** GitHub Actions cron, Groq free tier, Supabase free tier, Vercel free tier. Hard 0 AED cap, proven in production.

4. **Anomaly detection with seasonality.** STL decomposition separates real emerging issues from weekday traffic patterns.

5. **Eval harness.** Every model scored on labeled sets. 88.3% sentiment accuracy. No black boxes.

**Stack:** Python pipeline, Next.js dashboard, Supabase Postgres, 5 data sources, 14 UAE-specific topics, 40 geocoded entities, Telegram alerts.

**Repo:** https://github.com/rb2625/basr-engine

Looking for feedback from anyone working in NLP, Arabic language, or public data.

---

*Tags: Show HN, NLP, Arabic, Sentiment Analysis, Open Source, UAE*
