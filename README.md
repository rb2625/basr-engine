# BASR / بصيرة

**Real-time UAE sentiment intelligence. Arabic-native. Zero cost.**

BASR monitors what people actually say about the UAE across Reddit, news, YouTube, app reviews, and live social feeds -- in Arabic, Arabizi, and English. It classifies sentiment, detects emerging issues before they trend, and delivers decision-ready briefings.

**[Live Dashboard](https://dashboard-gamma-roan-31.vercel.app)** -- public, no login required.

---

## What it does

Every day, thousands of people discuss UAE housing, jobs, prices, government services, and businesses across social media and news. Most of it is in Arabic or Arabizi (Arabic written in Latin script: `3ashan`, `khalas`, `yalla`). Existing sentiment tools either don't handle Arabizi, charge $15K+/year, or both.

BASR fills that gap:

- **Ingests** from 5 sources: Reddit (Arctic archive), 11 news RSS feeds (Khaleej Times, Gulf News, The National, WAM, and more), YouTube comments, Apple App Store reviews, and Bluesky live posts
- **Normalizes** text across Arabic, Arabizi, and English using [ArabiziKit](https://github.com/rb2625/arabizi-kit) (1,155 learned Gulf word readings)
- **Classifies** sentiment (positive/negative/neutral) and signal type (closure, opportunity, stress, government-services) with a 3-tier hybrid model: local n-gram (instant, zero tokens) -> lexicon (zero tokens) -> LLM (Groq free tier)
- **Enriches** with 14 UAE-specific topics (rent-housing, jobs-labor, prices-inflation, etc.) and 40 geocoded entities (Dubai Marina, RTA, DEWA, etc.)
- **Detects anomalies** using STL seasonality decomposition + rolling z-score -- separates real emerging issues from weekday traffic patterns
- **Delivers** alerts over Telegram, daily "UAE Pulse" reports, and weekly sector digests

## Dashboard

The public dashboard shows live UAE sentiment data:

| View | What you see |
|------|-------------|
| **Overview** | KPIs, signal mix, top topics, 30-day volume/sentiment trends |
| **Map** | Entity sentiment map with geocoded UAE locations |
| **Trends** | Daily volume + sentiment + stress by topic |
| **Topics** | 14 topic cards with sentiment breakdown |
| **Feed** | Latest classified documents with badges |
| **Alerts** | Active anomaly alerts with severity |
| **Briefs** | Decision-ready issue briefs |
| **Reports** | UAE Pulse daily + weekly sector digests |

## Architecture

```
DATA SOURCES                   STORE (Supabase Postgres)
  Reddit Arctic archive    ->    raw_docs (deduped, hashed authors)
  News RSS (11 feeds)      ->    normalized_docs
  YouTube comments         ->    classifications / topics / entities
  Apple App Store reviews  ->    time_series (hourly/daily aggregates)
  Bluesky live feed        ->    alerts / briefs / orgs / eval_*
        |
        v
NLP PIPELINE                 INTELLIGENCE
  normalizer (ArabiziKit)     time-series aggregation
  language detection           anomaly detection (STL + z-score)
  3-tier classifier           alerting (severity low -> critical)
  topic tagging (14 topics)   agent layer (briefs, severity, reports)
  entity extraction (40+)     eval harness (every model scored)
        |
        v
DELIVERY
  Next.js dashboard (Vercel) + Telegram alerts + Email digest
```

## Tech stack

| Layer | Tool | Cost |
|-------|------|------|
| Database | Supabase Postgres + PostGIS | Free tier |
| Cron | GitHub Actions (2x daily) | Free |
| LLM | Groq free tier (gpt-oss-120b) | Free |
| Language ID | fasttext lid.176 (offline) | Free |
| Arabizi | ArabiziKit (Gulf dialect) | Free, open source |
| Dashboard | Next.js 14 + Tailwind + Leaflet + Recharts | Free (Vercel) |
| Alerts | Telegram bot + email (SendGrid) | Free tiers |
| **Total** | | **0 AED** |

## Setup

```bash
# Clone
git clone https://github.com/rabeeeeehhh/basr-engine.git
cd basr-engine

# Install
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt  # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # Linux/Mac

# Configure
cp .env.example .env
# Add your keys: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, GROQ_API_KEY

# Run the pipeline
python -m basr.orchestrator --intel --agents
```

## Data sources

| # | Source | Method | Status |
|---|--------|--------|--------|
| 1 | Reddit posts + comments | Arctic Shift archive (keyless) | Live |
| 2 | News RSS (11 feeds) | Khaleej Times, Gulf News, The National, WAM, Zawya, etc. | Live |
| 3 | YouTube comments | YouTube Data API (free tier) | Live |
| 4 | Apple App Store reviews | iTunes RSS (keyless) | Live |
| 5 | Bluesky live feed | Jetstream v2 (free) | Live |

## Eval scores

Every model in BASR is scored on labeled eval sets. Scores are logged to the database and public.

| Task | Accuracy | Notes |
|------|----------|-------|
| Sentiment (hybrid) | **88.3%** | positive F1=0.916, negative F1=0.895 |
| Signal taxonomy | **80.8%** | closure F1=1.000, stress F1=0.843 |
| Agent briefs | **100%** | grounded, complete, format-valid |

## Commands

| What | Command |
|------|---------|
| Run full pipeline | `python -m basr.orchestrator --intel --agents` |
| Ingest only | `python -m basr.orchestrator` |
| Early warning | `python -m basr.intel` |
| Build a brief | `python -m basr.agents --brief <id> --publish` |
| Daily report | `python -m basr.agents --report daily --deliver` |
| Run eval | `python -m basr.eval --path hybrid` |
| Run tests | `python -m pytest tests/ -q` |

## How it's different

1. **Arabizi-native** -- uses ArabiziKit (1,155 learned Gulf word readings) instead of a basic character map. Handles `shlonak ya 7al` -> `شلونك يا حال` correctly.
2. **Zero-cost architecture** -- every layer runs on free tiers. No credit card required. The 0 AED cap is proven in production, not aspirational.
3. **3-tier classification** -- local n-gram (instant, zero tokens) -> lexicon (zero tokens) -> LLM (Groq free). 80%+ of docs classified without any API call.
4. **Anomaly detection with seasonality** -- STL decomposition separates real emerging issues from Tuesday afternoon traffic spikes.
5. **Decision-ready output** -- not just charts. Severity-scored briefs with recommended responses, delivered over Telegram.
6. **Public and measured** -- every model score is logged. The eval harness runs on labeled sets. No black boxes.

## License

MIT

## Author

Muhammed Rabeeh Mattath
