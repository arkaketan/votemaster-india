"""
Indian Election News Scraper
Pulls election-related headlines from RSS feeds of major Indian news outlets.
Uses feedparser — works without any browser or JS rendering.
"""

import logging
import time
import feedparser
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# RSS feed registry
# -----------------------------------------------------------------------
FEEDS = [
    {
        "source": "NDTV",
        "url":    "https://feeds.feedburner.com/ndtvnews-india-news",
        "colour": "#E53935",
    },
    {
        "source": "NDTV Politics",
        "url":    "https://feeds.feedburner.com/ndtvnews-politics-news",
        "colour": "#E53935",
    },
    {
        "source": "The Hindu",
        "url":    "https://www.thehindu.com/news/national/feeder/default.rss",
        "colour": "#1565C0",
    },
    {
        "source": "The Hindu Elections",
        "url":    "https://www.thehindu.com/elections/feeder/default.rss",
        "colour": "#1565C0",
    },
    {
        "source": "Times of India",
        "url":    "https://timesofindia.indiatimes.com/rss/4719148.cms",
        "colour": "#FF6D00",
    },
    {
        "source": "TOI Politics",
        "url":    "https://timesofindia.indiatimes.com/rss/4719158.cms",
        "colour": "#FF6D00",
    },
    {
        "source": "Hindustan Times",
        "url":    "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
        "colour": "#6A1B9A",
    },
    {
        "source": "India TV News",
        "url":    "https://www.indiatvnews.com/rssnews/nation.xml",
        "colour": "#00838F",
    },
    {
        "source": "The Quint",
        "url":    "https://feeds.thequint.com/thequint/india",
        "colour": "#37474F",
    },
]

# Keywords to filter election-relevant articles
ELECTION_KEYWORDS = [
    "election", "vote", "voting", "poll", "ballot", "constituency",
    "candidate", "seat", "assembly", "lok sabha", "rajya sabha",
    "bjp", "inc", "congress", "aap", "tmc", "trinamool",
    "dmk", "aiadmk", "cpm", "cpi", "ncp", "shiv sena",
    "west bengal", "kerala", "tamil nadu", "assam", "puducherry",
    "modi", "rahul", "mamata", "kejriwal", "mcc", "eci",
    "election commission", "results", "counting", "winning",
    "leading", "trailing", "margin", "majority", "coalition",
    "alliance", "manifesto", "campaign", "rally",
]


def _is_election_related(title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    return any(kw in text for kw in ELECTION_KEYWORDS)


def _parse_entry_time(entry) -> str:
    """Return ISO timestamp from a feedparser entry, falling back to now."""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                dt = datetime(*t[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except Exception:
                pass
    return datetime.utcnow().isoformat()


def _parse_entry_time_display(entry) -> str:
    """Return a human-readable time string."""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                dt = datetime(*t[:6], tzinfo=timezone.utc)
                return dt.strftime("%d %b %Y, %H:%M UTC")
            except Exception:
                pass
    return "Just now"


class NewsScraper:
    def __init__(self, max_per_feed: int = 15, timeout: int = 10):
        self.max_per_feed = max_per_feed
        self.timeout = timeout
        # feedparser uses urllib internally; set socket timeout globally
        import socket
        socket.setdefaulttimeout(timeout)

    def get_election_news(self, filter_keywords: bool = True) -> list[dict]:
        """
        Fetch and return election-related news articles from all registered feeds.
        Articles are sorted newest-first. Falls back to demo data if all feeds fail.
        """
        articles = []

        for feed_cfg in FEEDS:
            try:
                feed = feedparser.parse(feed_cfg["url"])
                count = 0
                for entry in feed.entries:
                    if count >= self.max_per_feed:
                        break
                    title   = getattr(entry, "title",   "") or ""
                    summary = getattr(entry, "summary", "") or ""
                    link    = getattr(entry, "link",    "") or ""

                    if filter_keywords and not _is_election_related(title, summary):
                        continue

                    # Strip HTML tags from summary
                    clean_summary = _strip_tags(summary)[:300]

                    articles.append({
                        "source":     feed_cfg["source"],
                        "colour":     feed_cfg["colour"],
                        "title":      title,
                        "summary":    clean_summary,
                        "url":        link,
                        "timestamp":  _parse_entry_time(entry),
                        "display_ts": _parse_entry_time_display(entry),
                    })
                    count += 1

            except Exception as exc:
                logger.warning("Feed %s failed: %s", feed_cfg["source"], exc)
                continue

        # Sort newest first
        articles.sort(key=lambda a: a["timestamp"], reverse=True)

        if not articles:
            logger.info("All feeds failed — returning demo news")
            return _demo_news()

        return articles


def _strip_tags(html: str) -> str:
    """Very lightweight HTML tag stripper."""
    import re
    clean = re.sub(r"<[^>]+>", "", html)
    clean = clean.replace("&nbsp;", " ").replace("&amp;", "&") \
                 .replace("&lt;", "<").replace("&gt;", ">") \
                 .replace("&quot;", '"').replace("&#39;", "'")
    return " ".join(clean.split())


# -----------------------------------------------------------------------
# Demo / fallback news data
# -----------------------------------------------------------------------
def _demo_news() -> list[dict]:
    now = datetime.utcnow()
    items = [
        ("NDTV",            "#E53935", "West Bengal: TMC leads in early trends, counting underway in 294 seats",
         "Early trends from the Election Commission show the Trinamool Congress holding a comfortable lead across a majority of constituencies in West Bengal as counting continues."),
        ("Times of India",  "#FF6D00", "Kerala LDF vs UDF: Too close to call in several seats as vote-counting progresses",
         "The Left Democratic Front and United Democratic Front are neck-and-neck in several key constituencies in Kerala, with leads changing multiple times."),
        ("The Hindu",       "#1565C0", "Tamil Nadu: DMK alliance sweeps urban seats, AIADMK holds ground in south",
         "The DMK-led alliance is performing strongly in urban constituencies while the AIADMK appears to be retaining its base in southern Tamil Nadu."),
        ("Hindustan Times", "#6A1B9A", "ECI activates central observers across all five poll-bound states",
         "The Election Commission of India has deployed 300+ central observers to ensure free and fair counting on May 4."),
        ("NDTV",            "#E53935", "Assam: BJP retains lead in majority of constituencies, Congress closes gap",
         "BJP-led alliance continues to perform well in Assam while Congress makes inroads in tea garden constituencies in the Brahmaputra valley."),
        ("The Quint",       "#37474F", "Opinion: What the 2026 assembly results mean for the 2029 Lok Sabha battle",
         "Political analysts see the five-state results as a crucial barometer ahead of the 2029 general election, with implications for both the NDA and INDIA bloc."),
        ("India TV News",   "#00838F", "EVM controversies resurface as opposition demands VVPAT slip recount",
         "Several opposition parties have filed complaints with the Election Commission demanding enhanced VVPAT slip verification in select constituencies."),
        ("Times of India",  "#FF6D00", "Voter turnout hits 78% across five states — highest in a decade",
         "An exceptionally high voter turnout of 78% was recorded across the five election-bound states, surpassing 2021 figures by nearly 6 percentage points."),
        ("The Hindu",       "#1565C0", "Puducherry: Congress-DMK alliance on track for majority, AINRC trails",
         "The ruling Congress-DMK alliance looks set to return to power in Puducherry, according to early counting trends."),
        ("NDTV",            "#E53935", "How social media shaped the 2026 state election campaigns",
         "From X (Twitter) to Instagram Reels, candidates and parties leaned heavily on digital platforms in what experts are calling India's most 'digital election' yet."),
    ]
    results = []
    for i, (source, colour, title, summary) in enumerate(items):
        ts = datetime(now.year, now.month, now.day,
                      max(0, now.hour - i), 0, 0, tzinfo=timezone.utc)
        results.append({
            "source":     source,
            "colour":     colour,
            "title":      title,
            "summary":    summary,
            "url":        "#",
            "timestamp":  ts.isoformat(),
            "display_ts": ts.strftime("%d %b %Y, %H:%M UTC"),
            "demo":       True,
        })
    return results
