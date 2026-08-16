"""Apple App Store reviews via the official iTunes RSS feed - keyless, no card.

Replaces the Google Places API plan (which requires a billing account/card) with
an official, free, keyless source: Apple publishes every app's recent reviews as
RSS/JSON at itunes.apple.com. UAE government services and delivery apps have
rich, honest review sentiment (e.g. UAE PASS at ~3.4 stars is genuine complaint
gold for the intelligence layer).

Verified live (2026-08-16): both the search API and the review feed respond
without any key from a UAE IP.

Endpoints:
    Search:   https://itunes.apple.com/{cc}/search?term=...&entity=software
    Reviews:  https://itunes.apple.com/{cc}/rss/customerreviews/id={appId}/sortBy=mostRecent/json
"""

from __future__ import annotations

import asyncio
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import quote

from .base import RawDoc, SourceAdapter, hash_author

# (name, Apple app id) - UAE apps with real user sentiment.
# App ids are stable; searchable at any time via the Search endpoint above.
APP_REVIEW_TARGETS: tuple[tuple[str, int], ...] = (
    ("UAE PASS", 1377158818),
    ("DubaiNow", 619712783),
    ("talabat", 451001072),
    ("RTA Dubai", 426109507),
    ("Careem", 552863731),
    ("Deliveroo", 1090890782),
    ("UAE Exchange", 459961305),
    ("Etisalat e&", 466926524),
)

_ITUNES_NS = {"im": "http://itunes.apple.com/rss"}


def _clean(value: str | None) -> str:
    return (value or "").strip()


class AppleReviewsAdapter(SourceAdapter):
    name = "apple_reviews"

    def __init__(
        self,
        apps: list[tuple[str, int]] | None = None,
        *,
        country: str = "ae",
        timeout: float = 30.0,
        max_retries: int = 3,
        user_agent: str | None = None,
    ) -> None:
        super().__init__(timeout=timeout, max_retries=max_retries, user_agent=user_agent)
        self.apps = apps or list(APP_REVIEW_TARGETS)
        self.country = country

    async def fetch(self, since: datetime | None = None, limit: int = 100) -> list[RawDoc]:
        docs: list[RawDoc] = []
        try:
            for name, app_id in self.apps:
                if len(docs) >= limit:
                    break
                docs.extend(await self._fetch_one(name, app_id, limit - len(docs)))
        finally:
            await self.close()
        return docs

    async def _fetch_one(self, name: str, app_id: int, remaining: int) -> list[RawDoc]:
        url = (
            f"https://itunes.apple.com/{self.country}/rss/customerreviews/"
            f"id={app_id}/sortBy=mostRecent/json"
        )
        try:
            resp = await self.get_with_retry(url)
            data = resp.json()
        except Exception as exc:
            print(f"    [-] apple_reviews {name}: {exc.__class__.__name__}: {str(exc)[:80]}")
            return []

        feed = data.get("feed") or {}
        entries = feed.get("entry") or []
        if isinstance(entries, dict):
            entries = [entries]  # single review is returned as a dict, not a list

        docs: list[RawDoc] = []
        for entry in entries[:remaining]:
            entry = entry or {}
            labels = lambda key: ((entry.get(key) or {}).get("label") or "")  # noqa: E731
            author = ((entry.get("author") or {}).get("name") or {}).get("label") or ""
            rating_raw = ((entry.get("im:rating") or {}).get("label")) or (
                (entry.get("rating") or {}).get("label") or ""
            )
            review_id = ((entry.get("id") or {}).get("label")) or ""
            updated = labels("updated")
            link = ((entry.get("link") or [{}])[0].get("attributes") or {}).get("href") if isinstance(entry.get("link"), list) else None

            text = _clean(labels("content"))
            title = _clean(labels("title"))
            if not text:
                continue

            published: datetime | None = None
            if updated:
                try:
                    published = datetime.fromisoformat(updated)
                    if published.tzinfo is None:
                        published = published.replace(tzinfo=timezone.utc)
                except ValueError:
                    published = None

            try:
                rating = int(float(rating_raw))
            except (TypeError, ValueError):
                rating = None

            docs.append(
                RawDoc(
                    source=self.name,
                    external_id=f"{app_id}:{review_id}",
                    text=text[:20000],
                    url=link or f"https://apps.apple.com/{self.country}/app/id{app_id}",
                    title=title or None,
                    author_hash=hash_author(author),
                    published_at=published,
                    lang=None,
                    location_hint=None,
                    meta={"app_id": app_id, "app_name": name, "rating": rating},
                )
            )

        print(f"    [+] apple_reviews {name}: {len(docs)} reviews")
        return docs


# ----------------------------------------------------------------------
# Standalone smoke test:  python -m basr.adapters.apple_reviews
# ----------------------------------------------------------------------
async def _smoke_test() -> None:
    adapter = AppleReviewsAdapter(apps=[("UAE PASS", 1377158818), ("DubaiNow", 619712783)])
    docs = await adapter.fetch(limit=10)
    print(f"[+] Collected {len(docs)} reviews")
    for d in docs[:5]:
        rating = d.meta.get("rating")
        print(f"  - {rating}* {d.text[:70]!r}")


if __name__ == "__main__":
    asyncio.run(_smoke_test())
