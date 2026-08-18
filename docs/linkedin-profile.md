# LinkedIn Project Description (Updated)

## BASR (بصر) -- UAE Real-Time Sentiment Intelligence Platform

Jan 2026 -- Present

Built a free, open-source public sentiment intelligence platform for the UAE. Monitors what people actually say about the UAE across Reddit, news outlets, YouTube, app reviews, and live social feeds -- in Arabic, Arabizi, and English -- and classifies sentiment, detects emerging issues, and delivers decision-ready briefings.

What it does:
- Ingests from 5 data sources: Reddit (r/dubai, r/abudhabi, r/UAE), 11 news RSS feeds (Khaleej Times, Gulf News, The National, WAM), YouTube comments, Apple App Store reviews, and Bluesky live posts
- Normalizes text across Arabic, Arabizi, and English using ArabiziKit (1,155 learned Gulf word readings) -- handles how millions of Gulf residents actually type
- Classifies sentiment and signal type with a 3-tier hybrid model: local n-gram (instant, zero API calls) -> lexicon (zero tokens) -> LLM (Groq free tier). 80%+ classified without any API call
- Enriches with 14 UAE-specific topics (rent-housing, jobs-labor, prices-inflation, etc.) and 40 geocoded entities (Dubai Marina, RTA, DEWA, etc.)
- Detects anomalies using STL seasonality decomposition + rolling z-score -- separates real emerging issues from weekday traffic patterns
- Delivers alerts over Telegram, daily "UAE Pulse" reports, and weekly sector digests
- Public dashboard with 8 views: Overview, Map, Trends, Topics, Feed, Alerts, Briefs, Reports

The entire pipeline runs on zero budget: GitHub Actions cron (2x daily), Groq free tier, Supabase free tier, Vercel free tier. No credit card required anywhere.

Eval harness scored on labeled datasets: 88.3% sentiment accuracy. Positive F1: 0.916, Negative F1: 0.895. Every model is measured, no black boxes.

Tech: Python pipeline, Next.js dashboard, Supabase Postgres, GitHub Actions, Telegram bot, Groq LLM, fastText language detection, ArabiziKit transliteration.

Live: https://dashboard-gamma-roan-31.vercel.app
Open source: https://github.com/rb2625/basr-engine

Skills: Python, NLP, Sentiment Analysis, Arabic Language Processing, Next.js, Supabase, LLM Integration, Data Pipeline Design, Anomaly Detection, Open Source

---

## Short version (for the LinkedIn project card):

BASR (بصر) -- UAE Real-Time Sentiment Intelligence

Free, open-source platform monitoring UAE public sentiment across Reddit, news, YouTube, app reviews, and social feeds in Arabic, Arabizi, and English. 5 data sources, 14 topics, 40 geocoded entities, 88.3% sentiment accuracy. Runs on zero budget.
