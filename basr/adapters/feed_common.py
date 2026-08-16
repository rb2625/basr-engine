"""Shared parsing for RSS/Atom feeds (Reddit RSS + news RSS).

Both Reddit (Atom) and news sites (RSS 2.0) expose the same shape of data; this
module normalizes either format into the RawDoc contract.

Notes:
- Reddit serves Atom; news sites serve RSS 2.0. Both are handled here.
- `external_id` prefers the feed's stable id/guid, falling back to the link.
- `published_at` is parsed timezone-aware where possible.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from .base import RawDoc, hash_author

_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def clean_html(text: str | None) -> str:
    """Strip HTML tags and unescape common entities, collapsing whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    for entity, char in (
        ("&amp;", "&"),
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&quot;", '"'),
        ("&apos;", "'"),
        ("&nbsp;", " "),
    ):
        text = text.replace(entity, char)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_atom(content: bytes, source: str, feed_name: str, limit: int) -> list[RawDoc]:
    root = ET.fromstring(content)
    docs: list[RawDoc] = []
    for entry in root.findall(".//atom:entry", _ATOM_NS)[:limit]:
        title_el = entry.find("atom:title", _ATOM_NS)
        content_el = entry.find("atom:content", _ATOM_NS)
        if content_el is None:
            content_el = entry.find("atom:summary", _ATOM_NS)
        link_el = entry.find("atom:link", _ATOM_NS)
        id_el = entry.find("atom:id", _ATOM_NS)
        updated_el = entry.find("atom:updated", _ATOM_NS)
        published_el = entry.find("atom:published", _ATOM_NS)
        author_el = entry.find("atom:author/atom:name", _ATOM_NS)

        title = clean_html(title_el.text if title_el is not None else "")
        body = clean_html(content_el.text if content_el is not None else "")
        text = f"{title}\n{body}".strip()[:20000]
        if not text or text.strip().lower() in {"[removed]", "[deleted]"}:
            continue

        url = link_el.get("href", "") if link_el is not None else ""
        external_id = (id_el.text or "").strip() if id_el is not None else ""
        if not external_id:
            external_id = f"{feed_name}:{url}"

        published: datetime | None = None
        raw_pub = (published_el.text if published_el is not None else None) or (
            updated_el.text if updated_el is not None else None
        )
        if raw_pub:
            try:
                published = datetime.fromisoformat(raw_pub.replace("Z", "+00:00"))
            except ValueError:
                published = None

        docs.append(
            RawDoc(
                source=source,
                external_id=f"{feed_name}:{external_id}",
                text=text,
                url=url,
                title=title or None,
                author_hash=hash_author(author_el.text if author_el is not None else None),
                published_at=published,
                lang=None,
                meta={"feed": feed_name},
            )
        )
    return docs


def _parse_rss(content: bytes, source: str, feed_name: str, limit: int) -> list[RawDoc]:
    root = ET.fromstring(content)
    docs: list[RawDoc] = []
    for item in root.findall(".//item")[:limit]:
        title_el = item.find("title")
        desc_el = item.find("description")
        link_el = item.find("link")
        guid_el = item.find("guid")
        pub_el = item.find("pubDate")

        title = clean_html(title_el.text if title_el is not None else "")
        desc = clean_html(desc_el.text if desc_el is not None else "")
        text = f"{title}\n{desc}".strip()[:20000]
        if not text:
            continue

        url = (link_el.text or "").strip() if link_el is not None else ""
        external_id = (guid_el.text or "").strip() if guid_el is not None else ""
        if not external_id:
            external_id = f"{feed_name}:{url}"

        published: datetime | None = None
        if pub_el is not None and pub_el.text:
            try:
                published = parsedate_to_datetime(pub_el.text)
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                published = None

        docs.append(
            RawDoc(
                source=source,
                external_id=f"{feed_name}:{external_id}",
                text=text,
                url=url,
                title=title or None,
                published_at=published,
                lang=None,
                meta={"feed": feed_name},
            )
        )
    return docs


def parse_feed(content: bytes, source: str, feed_name: str, limit: int = 30) -> list[RawDoc]:
    """Parse feed bytes into RawDocs. Handles Atom (Reddit) and RSS 2.0 (news)."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return []
    if root.find(".//atom:entry", _ATOM_NS) is not None:
        return _parse_atom(content, source, feed_name, limit)
    return _parse_rss(content, source, feed_name, limit)
