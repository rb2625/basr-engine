# Reddit Launch Post (r/dubai)

---

## I built a free tool that tracks what people actually say about the UAE

Hey r/dubai. I've been working on something and wanted to share it with the community.

**BASR** (بصيرة, Arabic for "insight") is a free, real-time sentiment intelligence platform for the UAE. It monitors what people say about the UAE across Reddit, news outlets, YouTube, app reviews, and live social feeds -- in Arabic, Arabizi, and English -- and classifies the sentiment, detects emerging issues, and produces briefings.

**Live dashboard:** https://dashboard-gamma-roan-31.vercel.app

**What it does:**
- Tracks 5 data sources: Reddit (r/dubai, r/abudhabi, r/UAE), 11 news RSS feeds (Khaleej Times, Gulf News, The National, WAM, etc.), YouTube comments, Apple App Store reviews, and Bluesky live posts
- Classifies sentiment (positive/negative/neutral) and signal type (stress, closure, opportunity, government-services)
- Detects anomalies in sentiment trends using STL seasonality decomposition
- Covers 14 UAE-specific topics: rent-housing, jobs-labor, prices-inflation, business-closures, transport, government-services, education, healthcare, tech-digital, retail-consumer, finance-banking, tourism-hospitality, utilities-infra, food-delivery
- 40 geocoded UAE entities (Dubai Marina, RTA, DEWA, etc.)

**What makes it different:**
- It handles Arabizi (Arabic written in Latin script: "3ashan", "khalas", "yalla") using a published library with 1,155 learned Gulf word readings
- It runs on zero budget -- every layer uses free tiers
- The entire pipeline is scored on labeled eval sets (88.3% sentiment accuracy)
- It's public and open source

**Tech stack:** Python, Next.js, Supabase Postgres, GitHub Actions, Groq free tier

**Repo:** https://github.com/rb2625/basr-engine

Looking for feedback from anyone in the UAE who works with data, media, or policy. What topics would you want to see tracked? What data sources would be useful?

---

*Flair: Project / Personal*
