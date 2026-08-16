"""YouTube comments for UAE news channels via the Data API v3 (free, no card).

Two-step design:
1. Video discovery via the keyless channel RSS feed (zero API cost):
       https://www.youtube.com/feeds/videos.xml?channel_id=<id>
2. Comments via YouTube Data API v3 (commentThreads.list) with YOUTUBE_API_KEY.
   Free tier: 10,000 quota units/day, NO billing account / card required
   (per Google's API docs, verified 2026).

Quota: commentThreads.list costs 1 unit per call (up to 100 threads) — the free
daily quota covers comment collection for many videos.

Config: `YOUTUBE_CHANNELS` in basr/config.py — (channel_id, display name) pairs,
resolved and pinned via the API's channel search.
"""

from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx

from .base import RawDoc, SourceAdapter, hash_author
from ..config import YOUTUBE_CHANNELS, get_settings

API_BASE = "https://www.googleapis.com/youtube/v3"
VIDEO_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

_YT_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    # NOTE: the feed declares "xml/schemas/2015" (no "xmlns") — verified live.
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

_TAG_RE = re.compile(r"<[^>]+>")


def _clean_html(text: str | None) -> str:
    return _TAG_RE.sub("", text or "").strip()


class YouTubeCommentsAdapter(SourceAdapter):
    name = "youtube_comments"

    def __init__(
        self,
        channels: list[tuple[str, str]] | None = None,
        *,
        videos_per_channel: int = 5,
        comments_per_video: int = 100,
        api_key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        user_agent: str | None = None,
    ) -> None:
        super().__init__(timeout=timeout, max_retries=max_retries, user_agent=user_agent)
        self.channels = channels if channels is not None else YOUTUBE_CHANNELS
        self.videos_per_channel = videos_per_channel
        self.comments_per_video = comments_per_video
        self.api_key = api_key or get_settings().youtube_api_key

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def fetch(self, since: datetime | None = None, limit: int = 100) -> list[RawDoc]:
        if not self.api_key:
            print("[-] youtube_comments: no YOUTUBE_API_KEY in env — skipping source")
            return []
        if not self.channels:
            print("[-] youtube_comments: no channels configured — skipping source")
            return []

        docs: list[RawDoc] = []
        try:
            for channel_id, name in self.channels:
                if len(docs) >= limit:
                    break
                docs.extend(
                    await self._fetch_channel(channel_id, name, limit - len(docs))
                )
        finally:
            await self.close()
        return docs

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _fetch_channel(self, channel_id: str, name: str, remaining: int) -> list[RawDoc]:
        """Discover recent videos (keyless RSS) then pull their comments (API)."""
        videos = await self._recent_videos(channel_id)
        if not videos:
            print(f"    [-] youtube_comments {name}: no videos via RSS")
            return []

        docs: list[RawDoc] = []
        for video_id, video_title in videos[: self.videos_per_channel]:
            if len(docs) >= remaining:
                break
            docs.extend(
                await self._fetch_video_comments(channel_id, name, video_id, video_title, remaining - len(docs))
            )
        print(f"    [+] youtube_comments {name}: {len(docs)} comments from {len(videos[: self.videos_per_channel])} videos")
        return docs

    async def _recent_videos(self, channel_id: str) -> list[tuple[str, str]]:
        """Keyless channel RSS → [(video_id, title)] for the latest uploads."""
        url = VIDEO_FEED.format(channel_id=channel_id)
        try:
            resp = await self.get_with_retry(url)
        except Exception as exc:
            print(f"    [-] youtube_comments rss {channel_id}: {exc.__class__.__name__}: {str(exc)[:80]}")
            return []

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError:
            return []

        videos: list[tuple[str, str]] = []
        for entry in root.findall(".//atom:entry", _YT_NS)[: self.videos_per_channel]:
            vid_el = entry.find("yt:videoId", _YT_NS)
            title_el = entry.find("atom:title", _YT_NS)
            if vid_el is None or not vid_el.text:
                continue
            videos.append((vid_el.text.strip(), (title_el.text or "").strip() if title_el is not None else ""))
        return videos

    async def _fetch_video_comments(
        self, channel_id: str, name: str, video_id: str, video_title: str, remaining: int
    ) -> list[RawDoc]:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": min(self.comments_per_video, 100),
            "order": "relevance",
            "key": self.api_key,
        }
        try:
            resp = await self.get_with_retry(f"{API_BASE}/commentThreads", params=params)
            data = resp.json()
        except httpx.HTTPStatusError as exc:
            # Distinguish quota exhaustion from other 403s (e.g. comments
            # disabled on the video — common on UAE gov media channels).
            reason = self._error_reason(exc)
            if reason == "quotaExceeded":
                print(f"    [-] youtube_comments {name}: daily quota exhausted — stopping source")
                raise QuotaExhausted from exc
            print(f"    [-] youtube_comments {name} (video {video_id}): HTTP {exc.response.status_code} reason={reason or exc}")
            return []
        except Exception as exc:
            print(f"    [-] youtube_comments {name} (video {video_id}): {exc.__class__.__name__}: {str(exc)[:100]}")
            return []

        docs: list[RawDoc] = []
        for item in (data.get("items") or [])[:remaining]:
            snippet = ((item.get("snippet") or {}).get("topLevelComment") or {}).get("snippet") or {}
            comment_id = (item.get("snippet") or {}).get("topLevelComment", {}).get("id")
            if not comment_id:
                continue

            text = _clean_html(snippet.get("textOriginal") or snippet.get("textDisplay") or "")
            if not text:
                continue

            author = snippet.get("authorDisplayName")
            published_raw = snippet.get("publishedAt")
            published: datetime | None = None
            if published_raw:
                try:
                    published = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
                except ValueError:
                    published = None

            docs.append(
                RawDoc(
                    source=self.name,
                    external_id=f"{video_id}:{comment_id}",
                    text=text[:20000],
                    url=f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}",
                    title=video_title or None,
                    author_hash=hash_author(author),
                    published_at=published,
                    lang=None,
                    location_hint=None,
                    meta={
                        "channel_id": channel_id,
                        "channel_name": name,
                        "video_id": video_id,
                        "like_count": snippet.get("likeCount"),
                    },
                )
            )
        return docs


    @staticmethod
    def _error_reason(exc: httpx.HTTPStatusError) -> str:
        try:
            body = exc.response.json()
            return ((body.get("error") or {}).get("errors") or [{}])[0].get("reason", "")
        except Exception:
            return ""


class QuotaExhausted(Exception):
    """Raised when the YouTube daily quota runs out — the pipeline should
    degrade gracefully and stop this source for the run."""


# ----------------------------------------------------------------------
# Standalone smoke test:  python -m basr.adapters.youtube_comments
# ----------------------------------------------------------------------
async def _smoke_test() -> None:
    adapter = YouTubeCommentsAdapter(videos_per_channel=2, comments_per_video=10)
    docs = await adapter.fetch(limit=20)
    print(f"[+] Collected {len(docs)} comments")
    for d in docs[:5]:
        print(f"  - [{d.meta.get('channel_name')}] {d.text[:70]!r}")


if __name__ == "__main__":
    try:
        asyncio.run(_smoke_test())
    except QuotaExhausted:
        print("[-] Quota exhausted — try again tomorrow (free tier resets daily)")
