# BASR 2.0 - Master Plan (single source of truth)

> **Standard:** the product will be *finished perfectly*, not "good enough." Nothing ships
> half-done. Monetization is a consequence of a perfect product, and only begins after the
> **Perfection Gate** (sec 12) passes - the gate is binary.
>
> **Discipline:** we move by this plan, phase by phase, in order. A phase is done only when
> its Definition of Done passes. No scope drift, no version churn. Changes to this plan
> require an explicit amendment (marked here).

**Name:** BASR (بصيرة - "insight")
**One-liner:** *UAE public sentiment intelligence and decision support - real-time, Arabic-native, early-warning, measured.*

---

## 1. Vision

BASR continuously ingests what people say about the UAE across Reddit, news, YouTube,
reviews, and live feeds - in Arabic, Arabizi, and English - classifies signals, detects
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
- No LinkedIn scraping (ToS + fragile) - replaced by YouTube + reviews + live feed.
- No crypto/blockchain, no mobile apps in v1 (PWA later if warranted), no paid APIs.
- No scope expansion until the Perfection Gate passes.

## 3. Architecture (locked)

```
ADAPTERS (one contract -> RawDoc)          STORE (Supabase)
  reddit_arctic (posts+comments)      ->   raw_docs (immutable, deduped, hashed authors)
  reddit_rss (freshness)              ->   normalized_docs
  news_rss (11 feeds)                 ->   classifications / topics / entities
  youtube_comments                    ->   time_series (hour/day aggregates)
  google_reviews                      ->   alerts / briefs / orgs / eval_*
  bluesky_firehose (live)
        |
        v
NLP PIPELINE                           INTELLIGENCE
  normalizer (Arabizi->Arabic)          time-series aggregation
  language detection (fasttext)        anomaly detection (STL + z-score ensemble)
  sentiment/emotion (fine-tuned        alerting (severity low->critical)
    Gulf Arabic model + LLM ensemble)  agent layer: briefs, severity, responses,
  signal taxonomy (v1 lineage)           scheduled reports
  topics (BERTopic + LLM labels)       EVAL HARNESS: every model + agent scored
  entities + geocoding
        |
        v
DELIVERY
  Next.js dashboard (public + org console)  -  PDF reports (upgraded)  -  alerts (email/Telegram)
```

## 4. Technology decisions - LOCKED

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
| Deploy | Vercel (dashboard)  -  HF Spaces (models)  -  Supabase (db)  -  GH Actions (cron) | 0 AED hard cap |

## 5. Data sources - LOCKED

| # | Source | Adapter | Status |
|---|---|---|---|
| 1 | Reddit posts+comments (freshness + depth) | `reddit_arctic` (keyless archive) | [x] built, live-tested (13 docs) |
| 2 | ~~Reddit RSS~~ **removed - see Amendment A1** (Reddit blocks keyless RSS) | - | - |
| 3 | News RSS (11 feeds incl. Khaleej, Gulf News, The National, WAM) | `news_rss` (refactor of v1) | [x] built, live-tested (30 items/feed) |
| 4 | YouTube comments (UAE news channels) | `youtube_comments` (keyless RSS discovery + Data API, no card) | [x] built, live-tested (5 channels pinned; commentsDisabled handled) |
| 5 | ~~Google reviews~~ **replaced - Amendment A2**  -  Apple App Store reviews (UAE gov + delivery apps) | `apple_reviews` (official iTunes RSS, keyless, no card) | [x] built, live-tested (10 reviews, Arabic + EN) |
| 6 | Live global feed filtered to UAE | `bluesky_firehose` (Jetstream v2, free) | [x] built, live-tested (513 frames/15s; word-boundary UAE filter) |
| - | LinkedIn | **excluded** (locked) | - |

**Adapter contract:** `RawDoc{source, external_id, url, title, text, author_hash,
published_at, fetched_at, lang, location_hint, media_links, meta}` -> `raw_docs` table.
Dedupe key: `source:external_id`.

## 6. NLP pipeline spec - LOCKED

1. **Normalize:** strip HTML/URLs/emoji; transliterate Arabizi -> Arabic; normalize dialect spellings.
2. **Language ID:** fasttext -> `ar` / `arz` / `en` / `mixed`.
3. **Sentiment + emotion:** fine-tuned Gulf-Arabic model (primary) for ar/arz; English model for en; **Groq LLM ensemble** for mixed/ambiguous/neutral-judgment calls. Output: score (-1..1), label, emotion, sarcasm flag, confidence.
4. **Signal taxonomy (v1 lineage):** `signal_type` (stress/closure/opportunity/neutral), `sector`, `intensity` (1-5), `confidence`, `summary_en` - via the v1 prompt (kept, it is good).
5. **Topics:** BERTopic clusters -> LLM labels -> stable topic table.
6. **Entities:** gazetteer (UAE cities/areas, authorities, universities, brands) + LLM extraction -> geocoded (Mapbox geocoding free tier) -> PostGIS.
7. **Eval:** every component scored on the eval set (Phase 2). Scores published on the dashboard ("measured platform").

**Targets:** sentiment F1 >= 88% (eval v1), >= 90% (eval v2 after iteration); language ID >= 97%.

## 7. Intelligence spec - LOCKED

- **Time series:** hourly + daily buckets; dimensions: entity / topic / sector / emirate / global. Aggregates: volume, sentiment mean/std.
- **Anomaly:** STL decomposition (seasonality: day-of-week, Ramadan, exam seasons) + rolling z-score ensemble -> `anomaly_score`, flag when above threshold and volume >= minimum and evidence exists.
- **Alerts:** severity low/medium/high/critical; status lifecycle open -> acknowledged -> dismissed/promoted; channels: email + Telegram (WhatsApp after gate).
- **Human-in-the-loop:** analyst/org can promote an alert into a brief.

## 8. Agent spec - LOCKED

Agents (scheduled + on-alert) produce, **always measured by the eval harness**:
1. **Issue brief** - what/where/who, sentiment trajectory, top evidence with links.
2. **Severity assessment** - impact x urgency x spread, justified.
3. **Recommended responses** - ordered options for the owning org.
4. **Scheduled reports** - daily "UAE Pulse", weekly sector digest, custom org reports (v1 lineage, upgraded with sentiment + anomaly + Arabic).

## 9. Dashboard spec - LOCKED

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

## 11. Roadmap - phases with strict Definitions of Done

> Order is fixed. A phase is complete only when its DoD fully passes. No "almost."

**Phase 0 - Foundations** [x] **COMPLETE (2026-08-16)**
- [x] `basr/` package, `config.py`, adapter contract (`base.py`)
- [x] Reddit Arctic adapter (live-tested: 13 real docs)
- [x] `schema.sql` executed in Supabase - all 15 tables verified live via the API
- [x] DoD passed: contract + schema reviewed and locked

**Phase 1 - Full ingestion** *(in progress - see sec 13)*
- [x] `news_rss` refactored onto the contract (live-tested: Google News UAE 30 items/feed)
- ~~`reddit_rss`~~ removed by **Amendment A1** (Reddit blocks keyless RSS - 302->login, 403)
- [x] `bluesky_firehose` built + live-tested (Jetstream v2 spec, word-boundary UAE keywords; false-positive bug 'choradeira'->'deira' found & fixed)
- [x] `apple_reviews` built + live-tested (keyless iTunes RSS; replaces Google Places by **Amendment A2**; Arabic + English review sentiment)
- [x] `youtube_comments` built + live-tested (keyless RSS video discovery + Data API comments; 5 UAE news channels pinned in config; commentsDisabled handled without false quota errors)
- [x] Build `basr/store/` (persistence: dedupe upserts, batches, retry) + `basr/orchestrator.py` - **live-verified**
- [x] Update GitHub Actions cron (2x/day, staggered sources, run-log artifact)
- [x] **DoD PASSED (2026-08-16):** end-to-end run inserted **270 deduped rows** (reddit 61, news 100, apple 100, youtube 9); second run proved idempotency (**0 inserted / 269 skipped**); zero crashes; retries verified live
- [x] `schema.sql` re-run in Supabase (idempotency fix: `DROP POLICY IF EXISTS` before each `CREATE POLICY` - the 42710 fix); `pipeline_runs` live, run logging verified end-to-end

**Phase 2 - NLP v1 + eval** *(in progress - see sec 13)*
- [x] `basr/nlp/` built: normalizer (HTML/emoji/URL cleanup + Arabizi->Arabic dictionary & char-map), language ID (heuristic ar/arz/en/mixed + optional fasttext path - **A4**), classifier (Groq llama-3.3-70b-v, v1-lineage prompt + sentiment/emotion/sarcasm), pipeline, CLI (`python -m basr.nlp`, incremental flush, budget-aware)
- [x] Live-verified end-to-end: 10 real docs classified into Supabase (sentiment/emotion/signal/entities), idempotent re-runs
- [x] `basr/eval/` built: 77-item curated seed (ar/arz/en, sarcasm, filtering traps) + scoring harness (accuracy/P/R/F1 + confusion) - **full 500-item set is the remaining labeling work**
- [ ] Topics (BERTopic) + entities/geocoding - next after eval closes
- [ ] Eval run v1 (needs Groq budget) + score published
- **DoD (revised, see A5):** sentiment F1 >= 88% on eval v1; every ingested doc classified *within the free-tier daily token budget*; scores logged

**Phase 3 - Dashboard v1 (public)**
- Next.js app: map, trends, topics, anomaly feed, search; deployed to Vercel
- **DoD:** live URL; loads real Supabase data; works on mobile

**Phase 4 - Early warning**
- time_series aggregation + anomaly detection + alerts
- **DoD:** a real alert fires on a real spike (verified, not simulated); alert -> email/Telegram delivered

**Phase 5 - Agents + reports**
- Briefs, severity, recommended responses, scheduled reports; agent eval harness
- **DoD:** briefs pass eval suite; daily/weekly reports auto-generated and delivered

**Phase 6 - Perfection pass**
- Backfill history, tests (unit + integration), docs (README, architecture, runbook), privacy/ToS audit, performance, Arabic coverage pass, dead-code removal (praw)
- **DoD:** Perfection Gate checklist (sec 12) all-green

**Phase 7 - Pilot & monetization** *(only after Phase 6 passes)*
- Pilot: AURAK comms (free) -> case study
- Org plans: free/pro/enterprise; custom reports; media licensing of "UAE Pulse"
- **DoD:** signed pilot + first paid customer + public case study

## 12. Perfection Gate (binary - all must pass)

1. All Phase DoDs passed, in order, no skipped items.
2. Sentiment F1 >= 90% on eval v2 (expanded set); eval scores public.
3. Ingestion runs 30 consecutive days with zero unhandled failures; uptime of dashboard >= 99%.
4. A real (non-simulated) anomaly alert has fired and been delivered.
5. Tests pass in CI; docs complete (README, architecture, runbook, data sources, privacy policy).
6. Privacy audit green: authors hashed, no private data, robots.txt + ToS respected, UAE media-law compliant (aggregated trends only, no individual accusations).
7. No known bugs labeled "acceptable for now." **There is no acceptable-for-now.**

Only then does monetization begin (Phase 7). Before the gate: no charging, no pitching, no "good enough."

## 13. Status - where we are (checkpoint, 2026-08-16)

**Done:** package structure  -  adapter contract  -  Reddit Arctic adapter (verified live:
13 real posts+comments from r/dubai + r/UAE on 2026-08-16)  -  full schema.sql (269 lines).

**Critical finding this checkpoint:** PullPush blocks programmatic access ("paid
scraping" 429) -> replaced with Arctic Shift, verified working from the user's IP.

**Phase 0 COMPLETE (2026-08-16):** schema executed in Supabase; all 15 tables verified
live via the PostgREST API from the user's machine (doc_topics/doc_entities use
composite keys - no `id` column, verified via their real columns).

**Phase 1 COMPLETE (2026-08-16):** store + orchestrator + cron built and live-verified.
End-to-end run: 270 rows inserted from 4 data-producing sources (reddit_arctic 61,
news_rss 100, apple_reviews 100, youtube_comments 9; bluesky 0 matches in a 45s
window = genuine scarcity, live-feed layer is supplementary). Re-run: 0 inserted /
269 skipped - idempotent dedupe proven. Live testing caught + fixed: async
Supabase client has no `close()` (store now defensive); Khaleej Times / Gulf News /
WAM direct RSS are dead (404 / bad-param) -> replaced with site-scoped Google News
feeds (all 11 feeds now live, 30 items each).**Next:** Phase 2 - NLP v1 + eval.

**Phase 1 fully closed (2026-08-16):** schema re-run succeeded after the 42710
idempotency fix (policies now dropped before create); `pipeline_runs` verified
live with a real logged run. Run logging is end-to-end operational.

**Phase 2 (2026-08-16):** NLP layer built + live-verified (10 real docs
classified end-to-end). Live testing caught the single most important
constraint of the project so far - **Groq's free tier caps llama-3.3-70b-v at
100,000 tokens/day (~64 docs/day at our prompt size)** - recorded as **A5**.
The classifier is now budget-aware (stops honestly, docs stay unclassified for
the next run). The backfill of the remaining ~220 docs is bounded by the daily
budget: it drains over successive cron runs; the fine-tuned small model
(planned) is what removes the ceiling. Also fixed a real schema bug: missing
UNIQUE on classifications(raw_doc_id) let retried upserts duplicate rows
(**A6**) - cleaned live (43 clean rows) and the constraint is now in schema.sql.
Second build of the session: the **zero-cost lexicon fast path** (**A7**) - a
keyword classifier (en/ar/arz) that catches the clear-cut majority with ZERO
LLM tokens; anything ambiguous (sarcasm, conflicting signals, weak evidence)
scores low and falls back to the LLM. Live-verified on real docs: 4/12 routed
to the lexicon with zero tokens, the rest correctly deferred (the LLM's daily
budget was exhausted and it stopped honestly - docs stayed unclassified for
retry). Third build: **topics + entity geocoding** (**A8**) - 14-topic keyword
taxonomy and a UAE gazetteer (locations with lat/lng, companies, authorities,
universities) that enrich every doc with zero tokens. The eval set grew
77 -> 187 items (ar 74 / en 74 / arz 39) and the lexicon was re-measured on
it: signal acc 0.888 / F1 0.881 with zero false signal routes (every remaining
miss is a deliberate deferral the LLM catches); sentiment acc 0.834. Scores
persisted to eval_runs (lexicon-v1). All 310 raw docs enriched in Supabase.
Fourth build: the **eval set hit the 500-item DoD** (ar 185 / en 186 / arz
129, covering MSA + Gulf + Egyptian + Levantine, Arabizi variants, sarcasm,
and the filtering traps). Lexicon re-measured on the full set - the growth
surfaced real false routes (إقبالا/توقف/new matched too broadly, salary-rise
disambiguation) that were fixed at the root: signal acc 0.700 / macro-F1
0.776 / macro-P 0.860 with ZERO false signal alarms; sentiment 0.656 (forced
answers; the neutral traps defer). Production routing on 500: 240/500 (48%)
handled by the lexicon at 95.0% accuracy (signal) for free, 52% deferred to
the LLM. Scores persisted to eval_runs (lexicon-v1). Fifth build: **Phase 3 dashboard v1** (A9) - built clean and verified serving real
Supabase data. Sixth build: **model migration + live deploy** (A10) - Groq
retired llama-3.3-70b-versatile; the classifier was re-benchmarked to
openai/gpt-oss-120b and the dashboard was deployed live to Vercel. The full
LLM-path hybrid eval was restructured into single-pass combined scoring
(one LLM call per item scores both tasks, matching production) and is ready
to run once the gpt-oss-120b daily budget (200k tokens/day) resets.

## 14. Working rules

1. Move by this plan, in order. One phase at a time.
2. Test live before assuming anything works (PullPush proved why).
3. Every source failure degrades gracefully; the platform never dies with one source.
4. Quality over speed; "step by step even if it takes time" is the operating principle.
5. This plan changes only by explicit amendment, recorded here.
6. Plain ASCII everywhere: no em/en dashes, arrows, or other non-ASCII
   punctuation in code, docs, comments, or commit messages. Arabic text
   content is the only exception (it is data, not punctuation).

---

## 15. Amendments

**A6 (2026-08-16): classifications(raw_doc_id) must be UNIQUE.** Live cleanup
found 25 duplicated classification rows: retried upserts (lost response ->
retry re-inserts) multiplied rows because the table had no unique constraint
on raw_doc_id. Fixed three ways: (1) cleaned the live table (43 clean rows;
error-payload rows deleted so those docs get retried), (2) schema.sql now adds
the constraint idempotently via a guarded DO block (re-run the SQL editor),
(3) the store upserts classifications with on_conflict="raw_doc_id".

**A5 (2026-08-16): Groq free tier = 100k tokens/day on llama-3.3-70b-v - the
LLM-first backfill is budget-bounded.** Verified live: the free tier caps the
70b model at 100,000 tokens/day (the 429 message carries the exact counter:
"tokens per day (TPD): Limit 100000"). At ~1,550 tokens/doc that is ~64
classified docs/day - far below the ~220-doc Phase 1 backlog, and it explains
why burst pacing (2 workers x 8s ~ 23k tok/min) tripped the ~12k tok/min
window. Engineering response: (1) classifier is budget-aware - on the first
TPD 429 it parses the API's own counter and stops classifying immediately,
leaving the rest unclassified for the next run (no 429 hammering); (2) pacing
serialized (workers=1, 10s gap ~ 6 RPM ~ 9.3k tok/min, safely under the
window); (3) hard-failed docs are NOT written as zero-confidence rows, so they
stay unclassified and get retried; (4) PLAN sec 11 DoD revised accordingly. The
real unlock remains the fine-tuned Gulf-Arabic model for high-volume sentiment
(plan sec 4) - with it, the 70b is reserved for synthesis only.

**A4 (2026-08-16): fasttext lid.176 deferred - heuristic language ID for v1.**
fasttext has no Windows wheel (verified live: both `fasttext` and
`fasttext-wheel` fail to build without a compiler on this machine). v1 ships a
deterministic heuristic (Arabic-script ratio -> ar/arz via dialect markers;
Latin + Arabizi digit-letters/tokens -> arz; else en; both strong -> mixed),
live-tested against ar/arz/en/mixed cases including URL robustness. The
`FasttextLangID` wrapper stays in code so the Linux cron runner can opt in
(model file present -> automatic).

**A3 (2026-08-16): Phase 1 completion - pipeline_runs table + news feed fixes.** (1) Added
`pipeline_runs` operational table (run status, source counts, inserted/skipped, failures)
satisfying the Phase 1 DoD "cron produces a run log"; the store logs every run and degrades
gracefully if the table is missing. (2) Verified live that Khaleej Times (`/rss/uaenews.xml`)
and Gulf News (`/rss/`) direct RSS are dead (404) and WAM (`/feed/rss`) returns a bad-param
error -> replaced all three with site-scoped Google News feeds (`site:khaleejtimes.com`,
`site:gulfnews.com`, `site:wam.ae`), all verified 200 with 30 items. (3) Supabase async
client exposes no `close()`/`aclose()` in the pinned version -> store close is now defensive.

**A2 (2026-08-16): Google Places API replaced with Apple App Store reviews.** Google's
Places API requires a billing account (card on file), which the project rule forbids
(hard 0-AED cap, no card risk). Replaced with the official iTunes customer-reviews
RSS feed - free, keyless, no card, verified live (UAE PASS, DubaiNow, talabat, RTA
Dubai; Arabic + English reviews captured). YouTube Data API v3 does NOT require a
card (free 10,000 quota units/day per Google docs, 2026) - kept as source #4.

**A1 (2026-08-16): Reddit RSS adapter removed.** Verified live from the user's IP:
`old.reddit.com/r/dubai/new/.rss` now 302->login and `www.reddit.com` returns 403
Blocked. Keyless Reddit RSS is dead. Arctic Shift (already built, keyless) is the
single Reddit source - it covers posts + comments, freshness + depth. `feed_common.py`
is retained (news_rss uses it). No other change: news_rss is live-tested at 30 items/feed.

**A7 (2026-08-16): zero-cost lexicon fast path.** `basr/nlp/lexicon.py`
classifies the clear-cut docs with keyword evidence and zero tokens: sentiment,
emotion, v1 signal taxonomy, sector, known UAE entities. Confidence is
conservative by design - sarcasm, conflicting strong signals, weak evidence,
and questions all collapse confidence so the pipeline (or the hybrid eval
path) falls back to the LLM. Stamps `model_version=lexicon-v1`. Routing
threshold ROUTE_CONFIDENCE=0.55 in pipeline.py. Measured on the eval set
(lexicon-only forced answers): signal acc 0.888 / macro-F1 0.881 with
precision 1.0 on stress/closure/opportunity (zero false alarms); sentiment acc
0.834 - every neutral-label and sarcasm trap defers to the LLM in production.
Eval CLI gained `--path llm|lexicon|hybrid`. The store now degrades to a plain
insert when the A6 UNIQUE constraint is missing (42P10) instead of failing -
safe for the single-process cron; re-running schema.sql is still the permanent
fix and adds the constraint.

**A10 (2026-08-17): model migration to gpt-oss-120b + live deploy.** Groq
retired llama-3.3-70b-versatile (the A5-era default) from the account - the
model name 404'd. `basr/eval/benchmark.py` (new, permanent) re-benchmarked
the available free-tier models through the same harness used for published
scorecards: openai/gpt-oss-120b won (6/6 on the smoke sample);
qwen/qwen3.6-27b fails Groq's json_object mode entirely; allam-2-7b is weak;
gpt-oss-20b trails. Three engineering findings absorbed:
1. Groq's json_object response mode rejects gpt-oss output (json_validate_failed
   with an empty failed_generation), so it is NOT used - the prompt's strict
   JSON instruction plus the tolerant _extract_json parser carry the load.
2. The gpt-oss-120b free tier caps at 200k tokens/day (~260-275 calls). The
   eval harness was restructured to combined single-pass scoring: one LLM
   call per item returns all fields (exactly like production) and BOTH task
   labels are scored from it - the full 500-item hybrid eval now fits in
   ~154k tokens instead of ~308k. The old two-pass design could never finish
   the DoD in one day.
3. A baseline run exposed prompt-drift: gpt-oss read factual/entertainment
   content as positive sentiment, missed some sarcasm, and neutralized
   positive economic events. The sentiment block gained explicit rules:
   non-economic factuals (weather, movies, purchases, questions, vague
   statements) are neutral; economic announcements keep event direction
   (investments/openings/tax exemptions/fee cuts/price drops are positive);
   ironic praise is negative+sarcasm; universal cost complaints (Salik,
   fees, rent) are stress signals even without a named company. The lexicon
   gained three defer guards (irony patterns, weather mentions, personal
   purchases) so those cases reach the LLM instead of being decided wrong
   by keywords. Targeted retests: the failure classes from both baseline
   runs now pass. Dashboard deployed live to Vercel
   (dashboard-gamma-roan-31.vercel.app, root dir `dashboard`, env vars
   SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY set server-side - the key never
   reaches the browser), verified serving real data (346 docs, geocoded map,
   KPIs). One action for the user: after the daily budget resets, run
   `python -m basr.eval --path hybrid` BEFORE the cron's --nlp stage burns
   the day's tokens - it logs the canonical Phase 2 DoD scorecard.

**A9 (2026-08-16): public dashboard (Phase 3 v1).** `dashboard/` - Next.js 14
(App Router) + Tailwind + Leaflet + Recharts, deployed to Vercel (root dir
`dashboard`). Five views: Overview (KPIs, signal mix, top topics, 30-day
volume/sentiment, recent stress), Map (entity sentiment map, gazetteer
coords, OpenStreetMap tiles), Trends (daily volume + sentiment + stress by
topic), Topics (14-topic cards), Feed (latest classified docs with badges).
Data flows through one API route (`/api/data?view=...`) that aggregates the
small Supabase tables server-side with the service-role key - the key never
reaches the browser. Verified live: `npm run build` green, production server
serving real Supabase data (282 docs, 47 classified, geocoded map), data
layer smoke test (`scripts/smoke.ts`) against the live DB. Recharts/Leaflet
kept client-side; pages are thin shells so the build never needs the DB.

**A8 (2026-08-16): topics + entity geocoding, zero tokens.** `basr/nlp/topics.py`
assigns up to 3 of 14 topics per doc (rent-housing, jobs-labor, prices-inflation,
business-closures, transport, government-services, education, healthcare,
tech-digital, retail-consumer, finance-banking, tourism-hospitality,
utilities-infra, food-delivery) with weighted keyword rules into `doc_topics`.
`basr/nlp/entities.py` is a curated UAE gazetteer - locations with lat/lng,
companies, authorities, universities - extracted into `entities`/`doc_entities`
(role location_of/mentioned), feeding the Phase 3 map. Both run on the clean
text regardless of classifier, so they backfill every doc with zero tokens
(`python -m basr.nlp --enrich-only`). `raw_docs.enriched_at` (idempotent schema
addition) marks the pass so zero-topic docs are not refetched; the store falls
back to a doc_topics query when the column is missing. Word matching uses a
shared word-boundary helper (`textmatch.py`) so short tokens like ai/du/rta do
not fire inside dubai/daily/apart. Live: all 310 docs enriched (215 topic
links, 120 entity links, zero tokens).

---

*Last amended: 2026-08-17 - Phase 0 [x]  -  Phase 1 [x]  -  Phase 2 in progress (NLP layer + eval set 500 DoD + lexicon + topics + geocoding all live-verified; full hybrid eval ready to run after the daily budget reset) - Phase 3 in progress (dashboard v1 deployed live); Amendments A1-A10 recorded (A4 fasttext deferral, A5 Groq 100k/day budget, A6 classifications UNIQUE, A7 lexicon fast path, A8 topics + geocoding, A9 dashboard, A10 gpt-oss-120b migration + live deploy).*
