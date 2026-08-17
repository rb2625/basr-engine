# BASR data sources

Every source follows the same adapter contract (`basr/adapters/`) and fails
gracefully. Volumes are honest: this is a small, public, UAE-scoped corpus,
not a firehose.

| Source | Adapter | Access | Notes |
|---|---|---|---|
| Reddit posts + comments (r/dubai, r/UAE, ...) | `reddit_arctic` | Arctic Shift public API (keyless) | Replaced keyless RSS (A1) and PullPush (A2): both block programmatic access. |
| News | `news` (11 feeds) | RSS/Atom + site-scoped Google News feeds | Dead RSS (Khaleej Times, Gulf News, WAM) replaced with Google News site queries (A10). |
| YouTube comments | `youtube` | YouTube Data API (YOUTUBE_API_KEY) | Skips when the key is absent; per-video search for UAE economic channels/topics. |
| Apple App Store reviews | `apple_reviews` | Official iTunes RSS (keyless) | UAE gov + delivery apps; Arabic + English. Replaced Google Places (no card needed, A2). |
| Bluesky firehose | `bluesky_firehose` | Public firehose (websockets) | Live feed, filtered for UAE terms. |

## Volume reality (2026-08-17)

- `raw_docs`: ~395 docs since the 2.0 pipeline started (bulk ingestion ramp
  on 2026-08-15/16, then the cron's twice-daily cadence).
- Classified: 47 docs (the LLM budget gates the backlog drain; ~30-60 docs
  fit in a day's free-tier window).
- The anomaly baseline needs ~28 days of daily history before STL engages
  and flags mean real-world surges rather than the ingestion ramp.

## Terms and robots

- All sources are public surfaces with no login wall; no LinkedIn scraping
  (ToS + fragile, out of scope by design).
- Reddit access via Arctic Shift's public endpoint; rates are kept modest
  (the platform never hammers a source - one failure is a skip, not a
  retry storm).
- YouTube uses an official API key; the adapter skips when unset.
- Authors are hashed before storage; no DMs, no private groups, no personal
  data targeting.
