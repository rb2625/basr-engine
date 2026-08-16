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
# direct publisher feeds add authoritative sources.
NEWS_FEEDS: list[tuple[str, str]] = [
    ("Bloomberg Arabia", "https://feeds.bloomberg.com/bview/news.rss"),
    ("Google News UAE Biz", "https://news.google.com/rss/search?q=UAE+business+economy&hl=en-AE&gl=AE&ceid=AE:en"),
    ("Google News Dubai", "https://news.google.com/rss/search?q=Dubai+real+estate+economy&hl=en-AE&gl=AE&ceid=AE:en"),
    ("Google News UAE Jobs", "https://news.google.com/rss/search?q=UAE+layoffs+hiring+jobs&hl=en-AE&gl=AE&ceid=AE:en"),
    ("Google News UAE Retail", "https://news.google.com/rss/search?q=Dubai+retail+restaurant+closure&hl=en-AE&gl=AE&ceid=AE:en"),
    ("Google News UAE Banks", "https://news.google.com/rss/search?q=UAE+bank+finance+ADCB+Emirates+NBD&hl=en-AE&gl=AE&ceid=AE:en"),
    ("Google News UAE PropTech", "https://news.google.com/rss/search?q=Dubai+property+rent+landlord&hl=en-AE&gl=AE&ceid=AE:en"),
    ("Khaleej Times", "https://www.khaleejtimes.com/rss/uaenews.xml"),
    ("Gulf News", "https://gulfnews.com/rss/"),
    ("The National", "https://www.thenationalnews.com/arc/outboundfeeds/rss/?outputType=xml"),
    ("WAM", "https://wam.ae/en/feed/rss"),
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

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@dataclass
class Settings:
    """Resolved runtime settings. Secrets are read lazily from the environment."""

    groq_api_key: str | None = field(default=None)
    supabase_url: str | None = field(default=None)
    supabase_service_role_key: str | None = field(default=None)

    user_agent: str = field(
        default="BASR-Intelligence/2.0 (UAE public sentiment intelligence platform; contact: owner@basr.ae)"
    )


def get_settings() -> Settings:
    return Settings(
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        supabase_url=os.environ.get("SUPABASE_URL"),
        supabase_service_role_key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
    )
