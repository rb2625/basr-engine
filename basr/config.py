"""Shared configuration for the BASR Intelligence Engine.

Centralizes environment loading and every tunable in one place so the pipeline
is configurable without code changes. Never logs secret values.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the repository root (one level above this package).
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# ---------------------------------------------------------------------------
# Source configuration
# ---------------------------------------------------------------------------

# UAE communities tracked by the Reddit adapters (RSS + pullpush archive).
# Subreddit names are case-insensitive on Reddit.
REDDIT_SUBREDDITS: list[str] = [
    "dubai",
    "UAE",
    "DubaiCentral",
    "UAETeenagers",
    "dubairealestate",
    "DubaiJobs",
    "abudhabi",
    "Emiratis",
    "dubaiexpats",
    "sharjah",
]

# News feeds: (name, url). Google News topic queries give UAE-specific coverage;
# site-scoped Google News feeds stand in for publishers that removed direct RSS
# (verified live 2026-08-16: Khaleej Times + Gulf News RSS are 404, WAM feed
# returns an error — see PLAN.md Amendment A3).
NEWS_FEEDS: list[tuple[str, str]] = [
    ("Bloomberg Arabia", "https://feeds.bloomberg.com/bview/news.rss"),
    ("Google News UAE Biz", "https://news.google.com/rss/search?q=UAE+business+economy&hl=en-AE&gl=AE&ceid=AE:en"),
    ("Google News Dubai", "https://news.google.com/rss/search?q=Dubai+real+estate+economy&hl=en-AE&gl=AE&ceid=AE:en"),
    ("Google News UAE Jobs", "https://news.google.com/rss/search?q=UAE+layoffs+hiring+jobs&hl=en-AE&gl=AE&ceid=AE:en"),
    ("Google News UAE Retail", "https://news.google.com/rss/search?q=Dubai+retail+restaurant+closure&hl=en-AE&gl=AE&ceid=AE:en"),
    ("Google News UAE Banks", "https://news.google.com/rss/search?q=UAE+bank+finance+ADCB+Emirates+NBD&hl=en-AE&gl=AE&ceid=AE:en"),
    ("Google News UAE PropTech", "https://news.google.com/rss/search?q=Dubai+property+rent+landlord&hl=en-AE&gl=AE&ceid=AE:en"),
    ("Khaleej Times", "https://news.google.com/rss/search?q=site:khaleejtimes.com&hl=en-AE&gl=AE&ceid=AE:en"),
    ("Gulf News", "https://news.google.com/rss/search?q=site:gulfnews.com&hl=en-AE&gl=AE&ceid=AE:en"),
    ("The National", "https://www.thenationalnews.com/arc/outboundfeeds/rss/?outputType=xml"),
    ("WAM", "https://news.google.com/rss/search?q=site:wam.ae&hl=en-AE&gl=AE&ceid=AE:en"),
]

# Default fetch limits per source run.
DEFAULT_FETCH_LIMIT: int = 100          # per adapter call
DEFAULT_PAGE_SIZE: int = 100            # pullpush page size (API max)
DEFAULT_SINCE_HOURS: int = 48           # lookback when no cursor is supplied

# ---------------------------------------------------------------------------
# Pipeline knobs
# ---------------------------------------------------------------------------

# Signals processed per run through the expensive LLM classifier. Tune to your
# budget — this is the main cost control.
MAX_LLM_PROCESS: int = 60

# YouTube — UAE news channels as (channel_id, display name).
# Channel ids are stable; resolved and pinned from the API's channel search.
# Keep this list small: each channel costs 1 quota unit per video per run.
YOUTUBE_CHANNELS: list[tuple[str, str]] = [
    # (channel_id, display name) — resolved live via the API channel search (2026-08-16)
    ("UCXTuTQZarVcFR_fgQXvsLpw", "Gulf News"),
    ("UCaeG9NIqdx-xcZGt7ETfkpA", "Khaleej Times"),
    ("UCGYf0VFdlSTzcJghW9z1DAA", "The National News"),
    ("UCJ-AxG2x-5kgN_MMfBYa2Cg", "Dubai Media Office"),
    ("UCByZP-y-7yWrnN7P9ADeyqg", "ARN News Live"),
]

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@dataclass
class Settings:
    """Resolved runtime settings. Secrets are read lazily from the environment."""

    groq_api_key: str | None = field(default=None)
    supabase_url: str | None = field(default=None)
    supabase_service_role_key: str | None = field(default=None)
    youtube_api_key: str | None = field(default=None)

    user_agent: str = field(
        default="BASR-Intelligence/2.0 (UAE public sentiment intelligence platform; contact: owner@basr.ae)"
    )


def get_settings() -> Settings:
    return Settings(
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        supabase_url=os.environ.get("SUPABASE_URL"),
        supabase_service_role_key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
        youtube_api_key=os.environ.get("YOUTUBE_API_KEY")
        or os.environ.get("GOOGLE_YOUTUBE_API_KEY"),
    )
