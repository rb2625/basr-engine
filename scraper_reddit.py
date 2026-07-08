import asyncio
import httpx
import xml.etree.ElementTree as ET
import re


# ── Reddit RSS feeds ──────────────────────────────────────────────
REDDIT_FEEDS = [
    ("reddit", "r/dubai",       "https://old.reddit.com/r/dubai/new/.rss"),
    ("reddit", "r/uae",         "https://old.reddit.com/r/uae/new/.rss"),
    ("reddit", "r/DubaiJobs",   "https://old.reddit.com/r/DubaiJobs/new/.rss"),
    ("reddit", "r/dubaiexpats", "https://old.reddit.com/r/dubaiexpats/new/.rss"),
    ("reddit", "r/abudhabi",    "https://old.reddit.com/r/abudhabi/new/.rss"),
]

NEWS_FEEDS = [
    ("news", "Bloomberg Arabia",       "https://feeds.bloomberg.com/bview/news.rss"),
    ("news", "Google News UAE Biz",    "https://news.google.com/rss/search?q=UAE+business+economy&hl=en-AE&gl=AE&ceid=AE:en"),
    ("news", "Google News Dubai",      "https://news.google.com/rss/search?q=Dubai+real+estate+economy&hl=en-AE&gl=AE&ceid=AE:en"),
    ("news", "Google News UAE Jobs",   "https://news.google.com/rss/search?q=UAE+layoffs+hiring+jobs&hl=en-AE&gl=AE&ceid=AE:en"),
    ("news", "Google News UAE Retail", "https://news.google.com/rss/search?q=Dubai+retail+restaurant+closure&hl=en-AE&gl=AE&ceid=AE:en"),
    ("news", "Google News UAE Banks",  "https://news.google.com/rss/search?q=UAE+bank+finance+ADCB+Emirates+NBD&hl=en-AE&gl=AE&ceid=AE:en"),
    ("news", "Google News UAE PropTech","https://news.google.com/rss/search?q=Dubai+property+rent+landlord&hl=en-AE&gl=AE&ceid=AE:en"),
]


def clean_html(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&amp;",  "&", text)
    text = re.sub(r"&lt;",   "<", text)
    text = re.sub(r"&gt;",   ">", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&#\d+;", "",  text)
    text = re.sub(r"\s+",    " ", text)
    return text.strip()


async def fetch_one_feed(
    client: httpx.AsyncClient,
    source_type: str,
    name: str,
    url: str
) -> list:
    signals: list = []
    try:
        response = await client.get(url)

        if response.status_code == 429:
            print(f"[-] {name}: rate limited — will retry next run")
            return signals
        if response.status_code not in (200, 301, 302):
            print(f"[-] {name}: status {response.status_code}")
            return signals

        root = ET.fromstring(response.content)

        # Atom format (Reddit uses this)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall(".//atom:entry", ns)

        if entries:
            for entry in entries[:30]:
                title_el   = entry.find("atom:title",   ns)
                content_el = entry.find("atom:content", ns)
                if content_el is None:
                    content_el = entry.find("atom:summary", ns)
                link_el    = entry.find("atom:link",    ns)

                title_text   = clean_html(title_el.text   if title_el   is not None else "")
                content_text = clean_html(content_el.text if content_el is not None else "")
                link_url     = link_el.get("href", "")   if link_el    is not None else ""

                combined = f"{title_text}\n{content_text}".strip()[:2000]
                if combined and combined not in ("[removed]", "[deleted]"):
                    signals.append({
                        "source_platform": source_type,
                        "source_url":      link_url or f"{url}#{len(signals)}",
                        "raw_text":        combined,
                    })

        else:
            # RSS 2.0 format (news sites)
            items = root.findall(".//item")
            for item in items[:30]:
                title_el = item.find("title")
                desc_el  = item.find("description")
                link_el  = item.find("link")

                title_text = clean_html(title_el.text if title_el is not None else "")
                desc_text  = clean_html(desc_el.text  if desc_el  is not None else "")
                link_url   = link_el.text              if link_el  is not None else ""

                combined = f"{title_text}\n{desc_text}".strip()[:2000]
                if combined:
                    signals.append({
                        "source_platform": source_type,
                        "source_url":      link_url or f"{url}#{len(signals)}",
                        "raw_text":        combined,
                    })

        print(f"[+] {name}: {len(signals)} signals")

    except ET.ParseError:
        print(f"[-] {name}: XML parse error — blocked or invalid feed")
    except Exception as e:
        print(f"[-] {name}: {str(e)[:80]}")

    return signals


async def fetch_reddit_signals() -> list:
    all_signals: list = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }

    async with httpx.AsyncClient(
        headers=headers,
        timeout=30.0,
        follow_redirects=True
    ) as client:

        # Fetch Reddit feeds one at a time with delay — avoids rate limiting
        print("[*] Fetching Reddit feeds (with delays to avoid rate limits)...")
        for source_type, name, url in REDDIT_FEEDS:
            result = await fetch_one_feed(client, source_type, name, url)
            all_signals.extend(result)
            if result:  # Only delay if we got data — if blocked, no point waiting
                await asyncio.sleep(3)  # 3 second gap between Reddit requests

        # Fetch news feeds all at once — they don't rate limit
        print("[*] Fetching news feeds simultaneously...")
        news_tasks = [
            fetch_one_feed(client, s, n, u)
            for s, n, u in NEWS_FEEDS
        ]
        news_results = await asyncio.gather(*news_tasks)
        for r in news_results:
            all_signals.extend(r)

    print(f"\n[+] Grand total: {len(all_signals)} signals from all sources")
    return all_signals


if __name__ == "__main__":
    signals = asyncio.run(fetch_reddit_signals())
    if signals:
        print(f"\nSample:\n{signals[0]['raw_text'][:300]}")
    else:
        print("No signals — check internet connection")