import asyncio
import httpx
import xml.etree.ElementTree as ET
import re

REDDIT_FEEDS = [
    ("reddit", "r/dubai",           "https://www.reddit.com/r/dubai/new/.rss"),
    ("reddit", "r/uae",             "https://www.reddit.com/r/uae/new/.rss"),
    ("reddit", "r/DubaiJobs",       "https://www.reddit.com/r/DubaiJobs/new/.rss"),
    ("reddit", "r/dubaiexpats",     "https://www.reddit.com/r/dubaiexpats/new/.rss"),
]

NEWS_FEEDS = [
    ("news", "Gulf Business",       "https://gulfbusiness.com/feed/"),
    ("news", "Arabian Business",    "https://www.arabianbusiness.com/rss"),
    ("news", "Wam UAE",             "https://wam.ae/rss.xml"),
    ("news", "Zawya",               "https://www.zawya.com/rss/uae-business.xml"),
    ("news", "Khaleej Times",       "https://www.khaleejtimes.com/feed"),
    ("news", "The National",        "https://www.thenationalnews.com/feed"),
    ("news", "Bloomberg Arabia",    "https://feeds.bloomberg.com/bview/news.rss"),
]


def clean_html(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


async def fetch_one_feed(client, source_type, name, url):
    signals = []
    try:
        response = await client.get(url)

        if response.status_code == 429:
            print(f"[-] {name}: rate limited (429) — will retry next run")
            return signals
        if response.status_code != 200:
            print(f"[-] {name}: status {response.status_code}")
            return signals

        root = ET.fromstring(response.content)

        # Try Atom format (Reddit uses this)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('.//atom:entry', ns)

        if entries:
            for entry in entries[:30]:
                title   = entry.find('atom:title', ns)
                content = entry.find('atom:content', ns)
                if content is None:
                    content = entry.find('atom:summary', ns)
                link    = entry.find('atom:link', ns)

                title_text   = clean_html(title.text   if title   is not None else "")
                content_text = clean_html(content.text if content is not None else "")
                link_url     = link.get('href', '')    if link    is not None else ""

                combined = f"{title_text}\n{content_text}".strip()[:2000]
                if combined and combined not in ["[removed]", "[deleted]"]:
                    signals.append({
                        "source_platform": source_type,
                        "source_url":      link_url or f"{url}#{len(signals)}",
                        "raw_text":        combined,
                    })
        else:
            # RSS 2.0 format
            items = root.findall('.//item')
            for item in items[:30]:
                title = item.find('title')
                desc  = item.find('description')
                link  = item.find('link')

                title_text = clean_html(title.text if title is not None else "")
                desc_text  = clean_html(desc.text  if desc  is not None else "")
                link_url   = link.text             if link  is not None else ""

                combined = f"{title_text}\n{desc_text}".strip()[:2000]
                if combined:
                    signals.append({
                        "source_platform": source_type,
                        "source_url":      link_url or f"{url}#{len(signals)}",
                        "raw_text":        combined,
                    })

        print(f"[+] {name}: {len(signals)} signals")

    except ET.ParseError:
        print(f"[-] {name}: XML parse error — site may be blocking bots")
    except Exception as e:
        print(f"[-] {name}: {str(e)[:80]}")

    return signals


async def fetch_reddit_signals():
    all_signals = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }

    all_feeds = REDDIT_FEEDS + NEWS_FEEDS

    async with httpx.AsyncClient(
        headers=headers,
        timeout=30.0,
        follow_redirects=True
    ) as client:
        tasks   = [fetch_one_feed(client, s, n, u) for s, n, u in all_feeds]
        results = await asyncio.gather(*tasks)
        for r in results:
            all_signals.extend(r)

    print(f"\n[+] Grand total: {len(all_signals)} signals from all sources")
    return all_signals


if __name__ == "__main__":
    signals = asyncio.run(fetch_reddit_signals())
    if signals:
        print(f"\nSample:\n{signals[0]['raw_text'][:300]}")