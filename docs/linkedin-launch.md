# LinkedIn Launch Post

---

I built a free real-time sentiment intelligence platform for the UAE.

It monitors what people actually say about the UAE across Reddit, news, YouTube, app reviews, and live social feeds -- in Arabic, Arabizi, and English -- and classifies sentiment, detects emerging issues, and delivers decision-ready briefings.

The entire thing runs on zero budget. GitHub Actions for cron. Groq free tier for the LLM. Supabase free tier for the database. Vercel free tier for the dashboard. No credit card required anywhere.

What makes it different:

1. Arabizi support. Most Arabic NLP tools handle formal Arabic. This handles how millions of Gulf residents actually type -- "3ashan", "khalas", "yalla" -- using a published library (ArabiziKit, 1,155 learned Gulf word readings).

2. 3-tier classification. Local n-gram model (instant, zero tokens) for the clear-cut majority. Lexicon fallback. LLM only for genuinely ambiguous items. 80%+ of docs classified without any API call.

3. Anomaly detection with seasonality. STL decomposition separates real emerging issues from Tuesday afternoon traffic spikes.

4. Public dashboard. Anyone can see UAE sentiment without logging in. No paywall.

5. Eval harness. Every model is scored on labeled sets. 88.3% sentiment accuracy. Scores are logged to the database. No black boxes.

The tech: Python pipeline, Next.js dashboard, Supabase Postgres, 5 data sources, 14 UAE-specific topics, 40 geocoded entities, Telegram alerts.

Live dashboard: https://dashboard-gamma-roan-31.vercel.app

Open source: https://github.com/rb2625/basr-engine

Looking for feedback from anyone working in UAE data, policy, or media. What would you want to see in a tool like this?

---

*Tags: #UAE #NLP #Arabic #SentimentAnalysis #OpenSource #DataIntelligence #Dubai #AbuDhabi #PublicPolicy*
