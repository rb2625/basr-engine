# BASR 2.0 — Master Plan (single source of truth)

> **Standard:** the product will be *finished perfectly*, not "good enough." Nothing ships
> half-done. Monetization is a consequence of a perfect product, and only begins after the
> **Perfection Gate** (§12) passes — the gate is binary.
>
> **Discipline:** we move by this plan, phase by phase, in order. A phase is done only when
> its Definition of Done passes. No scope drift, no version churn. Changes to this plan
> require an explicit amendment (marked here).

**Name:** BASR (بصيرة — "insight")
**One-liner:** *UAE public sentiment intelligence and decision support — real-time, Arabic-native, early-warning, measured.*

---

## 1. Vision

BASR continuously ingests what people say about the UAE across Reddit, news, YouTube,
reviews, and live feeds — in Arabic, Arabizi, and English — classifies signals, detects
emerging issues *before they blow up*, and produces decision-ready briefings for
universities, brands, agencies, government entities, and analysts. A free public dashboard
is the users layer and the proof of quality; org-facing intelligence is the product.

## 2. Product definition

| Layer | Who | What |
|---|---|---|
| Public dashboard (free) | students, residents, analysts, media | live sentiment map, trends, topics, anomaly feed, search |
| Org console (paid, post-gate) | universities, PR agencies, real estate, government | entity trackers, alerts, briefs, reports, white-label |
| Deliverables | orgs + media | PDF reports (v1 lineage), scheduled briefs, API |

**What BASR is NOT (out of scope, locked):**
- No private/closed data, no personal-data targeting, no login-walled scraping.
- No LinkedIn scraping (ToS + fragile) — replaced by YouTube + reviews + live feed.
- No crypto/blockchain, no mobile apps in v1 (PWA later if warranted), no paid APIs.
- No scope expansion until the Perfection Gate passes.

## 3. Architecture (locked)

```
ADAPTERS (one contract → RawDoc)          STORE (Supabase)
  reddit_arctic (posts+comments)      →   raw_docs (immutable, deduped, hashed authors)
  reddit_rss (freshness)              →   normalized_docs
  news_rss (11 feeds)                 →   classifications / topics / entities
  youtube_comments                    →   time_series (hour/day aggregates)
  google_reviews                      →   alerts / briefs / orgs / eval_*
  bluesky_firehose (live)
        │
        ▼
NLP PIPELINE                           INTELLIGENCE
  normalizer (Arabizi→Arabic)          time-series aggregation
  language detection (fasttext)        anomaly detection (STL + z-score ensemble)
  sentiment/emotion (fine-tuned        alerting (severity low→critical)
    Gulf Arabic model + LLM ensemble)  agent layer: briefs, severity, responses,
  signal taxonomy (v1 lineage)           scheduled reports
  topics (BERTopic + LLM labels)       EVAL HARNESS: every model + agent scored
  entities + geocoding
        │
        ▼
DELIVERY
  Next.js dashboard (public + org console) · PDF reports (upgraded) · alerts (email/Telegram)
```

## 4. Technology decisions — LOCKED

| Concern | Decision | Why |
|---|---|---|
| Language | Python 3.11+ (cron parity) / TS for dashboard | v1 parity + ecosystem |
| Ingestion | `httpx` async, per-source adapters on `basr/adapters/base.py` | source immunity |
| Reddit data | Arctic Shift archive (keyless, verified live) + RSS | official API gated |
| DB | Supabase Postgres + PostGIS (`basr/schema.sql`) | zero cost, geo, auth |
| Queue/schedule | GitHub Actions cron; Upstash Redis later if needed | zero cost today |
| LLM | Groq free tier (v1 prompt, retained) for synthesis; fine-tuned small model for high-volume sentiment | zero marginal cost |
| Arabic model | CAMeL-Lab AraBERT fine-tune on Gulf + Arabizi (Kaggle/Colab free GPU), served on HF Spaces | Arabic-native, measurable |
| Language ID | fasttext lid.176 (offline, free) | fast + free |
| Topics | BERTopic (offline) + LLM labeling | stable clusters |
| Anomaly | statsmodels STL + rolling z-score ensemble | simple, auditable |
| Dashboard | Next.js + Tailwind + Mapbox GL + Recharts + Supabase Auth | proven stack, free |
| Reports | fpdf2 (upgraded: sentiment stats, anomaly section) | v1 lineage |
| Alerts | Email (Resend free) + Telegram bot | free |
| Deploy | Vercel (dashboard) · HF Spaces (models) · Supabase (db) · GH Actions (cron) | 0 AED hard cap |

## 5. Data sources — LOCKED

| # | Source | Adapter | Status |
|---|---|---|---|
| 1 | Reddit posts+comments (freshness + depth) | `reddit_arctic` (keyless archive) | ✅ built, live-tested (13 docs) |
| 2 | ~~Reddit RSS~~ **removed — see Amendment A1** (Reddit blocks keyless RSS) | — | — |
| 3 | News RSS (11 feeds incl. Khaleej, Gulf News, The National, WAM) | `news_rss` (refactor of v1) | ✅ built, live-tested (30 items/feed) |
| 4 | YouTube comments (UAE news channels) | `youtube_comments` (keyless RSS discovery + Data API, no card) | ✅ built, live-tested (5 channels pinned; commentsDisabled handled) |
| 5 | ~~Google reviews~~ **replaced — Amendment A2** · Apple App Store reviews (UAE gov + delivery apps) | `apple_reviews` (official iTunes RSS, keyless, no card) | ✅ built, live-tested (10 reviews, Arabic + EN) |
| 6 | Live global feed filtered to UAE | `bluesky_firehose` (Jetstream v2, free) | ✅ built, live-tested (513 frames/15s; word-boundary UAE filter) |
| — | LinkedIn | **excluded** (locked) | — |

**Adapter contract:** `RawDoc{source, external_id, url, title, text, author_hash,
published_at, fetched_at, lang, location_hint, media_links, meta}` → `raw_docs` table.
Dedupe key: `source:external_id`.

## 6. NLP pipeline spec — LOCKED

1. **Normalize:** strip HTML/URLs/emoji; transliterate Arabizi → Arabic; normalize dialect spellings.
2. **Language ID:** fasttext → `ar` / `arz` / `en` / `mixed`.
3. **Sentiment + emotion:** fine-tuned Gulf-Arabic model (primary) for ar/arz; English model for en; **Groq LLM ensemble** for mixed/ambiguous/neutral-judgment calls. Output: score (-1..1), label, emotion, sarcasm flag, confidence.
4. **Signal taxonomy (v1 lineage):** `signal_type` (stress/closure/opportunity/neutral), `sector`, `intensity` (1–5), `confidence`, `summary_en` — via the v1 prompt (kept, it is good).
5. **Topics:** BERTopic clusters → LLM labels → stable topic table.
6. **Entities:** gazetteer (UAE cities/areas, authorities, universities, brands) + LLM extraction → geocoded (Mapbox geocoding free tier) → PostGIS.
7. **Eval:** every component scored on the eval set (Phase 2). Scores published on the dashboard ("measured platform").

**Targets:** sentiment F1 ≥ 88% (eval v1), ≥ 90% (eval v2 after iteration); language ID ≥ 97%.

## 7. Intelligence spec — LOCKED

- **Time series:** hourly + daily buckets; dimensions: entity / topic / sector / emirate / global. Aggregates: volume, sentiment mean/std.
- **Anomaly:** STL decomposition (seasonality: day-of-week, Ramadan, exam seasons) + rolling z-score ensemble → `anomaly_score`, flag when above threshold and volume ≥ minimum and evidence exists.
- **Alerts:** severity low/medium/high/critical; status lifecycle open → acknowledged → dismissed/promoted; channels: email + Telegram (WhatsApp after gate).
- **Human-in-the-loop:** analyst/org can promote an alert into a brief.

## 8. Agent spec — LOCKED

Agents (scheduled + on-alert) produce, **always measured by the eval harness**:
1. **Issue brief** — what/where/who, sentiment trajectory, top evidence with links.
2. **Severity assessment** — impact × urgency × spread, justified.
3. **Recommended responses** — ordered options for the owning org.
4. **Scheduled reports** — daily "UAE Pulse", weekly sector digest, custom org reports (v1 lineage, upgraded with sentiment + anomaly + Arabic).

## 9. Dashboard spec — LOCKED

- **Public (free):** live UAE sentiment map (Mapbox), trend charts, topic explorer, anomaly feed, search, published eval scores. The acquisition + proof layer.
- **Org console (post-gate, paid):** entity trackers, alert management, brief library, report builder, white-label.
- **Tech:** Next.js + Tailwind + Mapbox GL + Recharts + Supabase (Postgres/Auth/Realtime).

## 10. Deliverables (final output set)

1. Live public dashboard (URL, always up).
2. Org console + paid tiers (post-gate).
3. PDF intelligence reports (upgraded).
4. Alerts (email/Telegram).
5. Scheduled reports (daily/weekly).
6. Open eval sets + published scores (the trust layer).

## 11. Roadmap — phases with strict Definitions of Done

> Order is fixed. A phase is complete only when its DoD fully passes. No "almost."

**Phase 0 — Foundations** ✅ **COMPLETE (2026-08-16)**
- ✅ `basr/` package, `config.py`, adapter contract (`base.py`)
- ✅ Reddit Arctic adapter (live-tested: 13 real docs)
- ✅ `schema.sql` executed in Supabase — all 15 tables verified live via the API
- ✅ DoD passed: contract + schema reviewed and locked

**Phase 1 — Full ingestion** *(in progress — see §13)*
- ✅ `news_rss` refactored onto the contract (live-tested: Google News UAE 30 items/feed)
- ~~`reddit_rss`~~ removed by **Amendment A1** (Reddit blocks keyless RSS — 302→login, 403)
- ✅ `bluesky_firehose` built + live-tested (Jetstream v2 spec, word-boundary UAE keywords; false-positive bug 'choradeira'→'deira' found & fixed)
- ✅ `apple_reviews` built + live-tested (keyless iTunes RSS; replaces Google Places by **Amendment A2**; Arabic + English review sentiment)
- ✅ `youtube_comments` built + live-tested (keyless RSS video discovery + Data API comments; 5 UAE news channels pinned in config; commentsDisabled handled without false quota errors)
- ⬜ Build `basr/store/` (persistence: dedupe upserts, batches) + `basr/orchestrator.py`
- ⬜ Update GitHub Actions cron (2×/day, staggered sources)
- **DoD:** full end-to-end run: all sources → deduped rows in Supabase, zero crashes, retries verified, cron produces a run log

**Phase 2 — NLP v1 + eval**
- Normalizer + language ID + sentiment/emotion (LLM ensemble first) + signal taxonomy + topics + entities/geocoding
- Eval set v1: 500 labeled items (ar/arz/en) + eval harness
- **DoD:** sentiment F1 ≥ 88% on eval v1; every ingested doc classified; scores logged

**Phase 3 — Dashboard v1 (public)**
- Next.js app: map, trends, topics, anomaly feed, search; deployed to Vercel
- **DoD:** live URL; loads real Supabase data; works on mobile

**Phase 4 — Early warning**
- time_series aggregation + anomaly detection + alerts
- **DoD:** a real alert fires on a real spike (verified, not simulated); alert → email/Telegram delivered

**Phase 5 — Agents + reports**
- Briefs, severity, recommended responses, scheduled reports; agent eval harness
- **DoD:** briefs pass eval suite; daily/weekly reports auto-generated and delivered

**Phase 6 — Perfection pass**
- Backfill history, tests (unit + integration), docs (README, architecture, runbook), privacy/ToS audit, performance, Arabic coverage pass, dead-code removal (praw)
- **DoD:** Perfection Gate checklist (§12) all-green

**Phase 7 — Pilot & monetization** *(only after Phase 6 passes)*
- Pilot: AURAK comms (free) → case study
- Org plans: free/pro/enterprise; custom reports; media licensing of "UAE Pulse"
- **DoD:** signed pilot + first paid customer + public case study

## 12. Perfection Gate (binary — all must pass)

1. All Phase DoDs passed, in order, no skipped items.
2. Sentiment F1 ≥ 90% on eval v2 (expanded set); eval scores public.
3. Ingestion runs 30 consecutive days with zero unhandled failures; uptime of dashboard ≥ 99%.
4. A real (non-simulated) anomaly alert has fired and been delivered.
5. Tests pass in CI; docs complete (README, architecture, runbook, data sources, privacy policy).
6. Privacy audit green: authors hashed, no private data, robots.txt + ToS respected, UAE media-law compliant (aggregated trends only, no individual accusations).
7. No known bugs labeled "acceptable for now." **There is no acceptable-for-now.**

Only then does monetization begin (Phase 7). Before the gate: no charging, no pitching, no "good enough."

## 13. Status — where we are (checkpoint, 2026-08-16)

**Done:** package structure · adapter contract · Reddit Arctic adapter (verified live:
13 real posts+comments from r/dubai + r/UAE on 2026-08-16) · full schema.sql (269 lines).

**Critical finding this checkpoint:** PullPush blocks programmatic access ("paid
scraping" 429) → replaced with Arctic Shift, verified working from the user's IP.

**Phase 0 COMPLETE (2026-08-16):** schema executed in Supabase; all 15 tables verified
live via the PostgREST API from the user's machine (doc_topics/doc_entities use
composite keys — no `id` column, verified via their real columns).**Next:** Phase 1 — store layer (`basr/store/`: dedupe upserts, batches) → orchestrator → cron → end-to-end run.

## 14. Working rules

1. Move by this plan, in order. One phase at a time.
2. Test live before assuming anything works (PullPush proved why).
3. Every source failure degrades gracefully; the platform never dies with one source.
4. Quality over speed; "step by step even if it takes time" is the operating principle.
5. This plan changes only by explicit amendment, recorded here.

---

## 15. Amendments

**A2 (2026-08-16): Google Places API replaced with Apple App Store reviews.** Google's
Places API requires a billing account (card on file), which the project rule forbids
(hard 0-AED cap, no card risk). Replaced with the official iTunes customer-reviews
RSS feed — free, keyless, no card, verified live (UAE PASS, DubaiNow, talabat, RTA
Dubai; Arabic + English reviews captured). YouTube Data API v3 does NOT require a
card (free 10,000 quota units/day per Google docs, 2026) — kept as source #4.

**A1 (2026-08-16): Reddit RSS adapter removed.** Verified live from the user's IP:
`old.reddit.com/r/dubai/new/.rss` now 302→login and `www.reddit.com` returns 403
Blocked. Keyless Reddit RSS is dead. Arctic Shift (already built, keyless) is the
single Reddit source — it covers posts + comments, freshness + depth. `feed_common.py`
is retained (news_rss uses it). No other change: news_rss is live-tested at 30 items/feed.

---

*Last amended: 2026-08-16 — plan created, all decisions locked; Phase 0 completed; Phase 1 started; Amendment A1 (reddit_rss removed).*
