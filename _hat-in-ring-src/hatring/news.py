"""News ingestion — Google News RSS plus direct outlet feeds.

Two source kinds feed the classifier:

  * ``gnews``      — Google News RSS. One alias-scoped query per tracked person
                     plus the broad "who's running" discovery queries. The QUERY
                     constrains the topic, so every returned item is already
                     on-subject.
  * ``direct``     — an outlet's own RSS (The Hill, Politico, and the IA/NH/SC/NV
                     state outlets). These carry the outlet's WHOLE news river,
                     not a 2028-scoped slice, so items are stamped
                     ``scoped=False`` and classify.py applies a relevance gate
                     before anything reaches the review queue.

Diversifying past Google News removes a single point of failure and is the only
way early-state (IA/NH/SC/NV) activity gets picked up from the outlets that
actually cover it. See config.yaml ``feeds:`` for the registry and
docs/decisions/2026-08-ingest-feeds.md for the availability audit.

All endpoints are public and unauthenticated. Be polite: the pipeline throttles
between requests, bounds each feed with a timeout, and caches by URL via the
signals audit log.
"""
from __future__ import annotations
import contextlib
import logging
import re
import socket
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
import feedparser

_TAGS = re.compile(r"<[^>]+>")

log = logging.getLogger("hatring.news")
RSS = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
UA = "hat-in-ring-radar/1.0 (+https://hatinring.com)"

# Source reliability -> base confidence ceiling for a derived signal.
# Keys are the DISPLAY names; a direct feed stamps its registry `name` here, so
# adding a feed to config.yaml without adding it below leaves it at the default
# Low ceiling (safe, but it will never produce a High-confidence signal).
RELIABILITY = {
    "Associated Press": "Very high", "AP News": "Very high", "Reuters": "Very high",
    "The Wall Street Journal": "High", "The Washington Post": "High",
    "The New York Times": "High", "Politico": "High", "NBC News": "High",
    "ABC News": "High", "CBS News": "High", "CNN": "High", "Axios": "High",
    "The Hill": "Medium", "Time": "Medium", "C-SPAN": "Medium",
    # Early-state outlets. Rated Medium — credible primary reporting on
    # IA/NH/SC/NV activity (the signal they exist to catch), without letting a
    # single local story alone certify a national-tier claim.
    "Iowa Capital Dispatch": "Medium", "Des Moines Register": "Medium",
    "New Hampshire Bulletin": "Medium", "NHPR": "Medium",
    "SC Daily Gazette": "Medium", "The Post and Courier": "Medium",
    "Nevada Current": "Medium", "The Nevada Independent": "Medium",
    "Vanity Fair": "Low", "New York Post": "Low",
}
DEFAULT_CONFIDENCE = "Low"   # unknown / local / blog outlets


@dataclass
class NewsItem:
    title: str
    summary: str
    url: str
    source: str
    published: str          # ISO date (YYYY-MM-DD)
    query: str
    # Registry id of the feed this came from ("gnews" for Google News). Stamped
    # onto the audit log so a source can be attributed or retired later.
    source_id: str = "gnews"
    # True when the QUERY already constrained the topic (Google News). False for
    # an outlet's full river, which classify.py must relevance-gate.
    scoped: bool = True

    @property
    def confidence_ceiling(self) -> str:
        return RELIABILITY.get(self.source, DEFAULT_CONFIDENCE)


def _published_iso(entry) -> str:
    t = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if t:
        return datetime(*t[:6], tzinfo=timezone.utc).date().isoformat()
    return datetime.now(timezone.utc).date().isoformat()


def _entry_source(entry, title: str, fallback: str) -> tuple[str, str]:
    """Return (title, source). Google News titles end with " - Source"; direct
    feeds carry no source element, so the registry name is used instead."""
    src_obj = entry.get("source")
    if src_obj and getattr(src_obj, "title", None):
        return title, src_obj.title
    if " - " in title:
        head, tail = title.rsplit(" - ", 1)
        if fallback:
            # A direct feed's own headline may legitimately contain " - "; only
            # strip it when it is not already attributed to the known outlet.
            return (head, tail) if tail.strip() == fallback else (title, fallback)
        return head, tail
    return title, fallback


def _to_items(entries, *, limit: int, query: str, source_id: str,
              scoped: bool, fallback_source: str) -> list[NewsItem]:
    items: list[NewsItem] = []
    for e in entries[:limit]:
        title, source = _entry_source(e, e.get("title", ""), fallback_source)
        # Strip any HTML from BOTH title and summary. Title becomes the candidate
        # headline rendered into the dashboard, so an un-stripped tag here is the
        # realistic stored-XSS delivery vector (defense-in-depth with render escaping).
        title = _TAGS.sub(" ", title)
        summary = _TAGS.sub(" ", e.get("summary", "")).strip()
        items.append(NewsItem(
            title=title.strip(),
            summary=summary,
            url=e.get("link", ""),
            source=source.strip(),
            published=_published_iso(e),
            query=query,
            source_id=source_id,
            scoped=scoped,
        ))
    return items


@contextlib.contextmanager
def _socket_timeout(seconds: float | None):
    """Bound a feedparser fetch. feedparser has no timeout argument, so the
    socket default is set for the duration — a single dead outlet must degrade
    the run, never hang it."""
    if not seconds:
        yield
        return
    prev = socket.getdefaulttimeout()
    socket.setdefaulttimeout(seconds)
    try:
        yield
    finally:
        socket.setdefaulttimeout(prev)


def fetch_query(query: str, limit: int = 25, source_id: str = "gnews") -> list[NewsItem]:
    url = RSS.format(q=urllib.parse.quote(query))
    feed = feedparser.parse(url)
    items = _to_items(feed.entries, limit=limit, query=query, source_id=source_id,
                      scoped=True, fallback_source="")
    log.info("news: %-48s -> %d items", query[:48], len(items))
    return items


def fetch_feed(spec: dict, limit: int = 40, timeout: float = 20.0) -> list[NewsItem]:
    """Fetch one registry entry. Never raises: a dead or malformed feed logs and
    returns [] so one bad outlet degrades the ingest instead of failing it."""
    fid = spec.get("id") or "?"
    name = spec.get("name") or fid
    kind = spec.get("kind", "direct")
    try:
        if kind == "gnews_site":
            q = spec.get("query")
            if not q:
                log.warning("news: feed %s is gnews_site with no query; skipped", fid)
                return []
            # Routed through Google News, but attributed to the real outlet so
            # RELIABILITY grades it as that outlet and the audit log can show it.
            items = fetch_query(q, limit=limit, source_id=fid)
            for it in items:
                if not it.source:
                    it.source = name
            return items
        url = spec.get("url")
        if not url:
            log.warning("news: feed %s has no url; skipped", fid)
            return []
        with _socket_timeout(timeout):
            feed = feedparser.parse(url, agent=UA)
        if getattr(feed, "bozo", 0) and not feed.entries:
            log.warning("news: feed %s did not parse (%s); skipped", fid,
                        getattr(feed, "bozo_exception", "unknown"))
            return []
        items = _to_items(feed.entries, limit=limit, query=f"feed:{fid}",
                          source_id=fid, scoped=False, fallback_source=name)
        log.info("news: %-24s -> %d items", fid, len(items))
        return items
    except Exception as e:                                   # noqa: BLE001
        log.error("news: feed %s failed (%s: %s)", fid, type(e).__name__, e)
        return []


def fetch_all(watchlist: list[dict], broad_queries: list[str],
              throttle: float = 1.0, per_person_limit: int = 12,
              feeds: list[dict] | None = None, feed_limit: int = 40,
              feed_timeout: float = 20.0) -> list[NewsItem]:
    """Google News (one scoped query per tracked person + broad discovery
    queries), then every registry feed. Deduped by URL across all sources."""
    seen: set[str] = set()
    out: list[NewsItem] = []
    queries: list[str] = []
    for person in watchlist:
        alias = (person.get("aliases") or [person["name"]])[0]
        queries.append(f'"{alias}" 2028 president')
    queries.extend(broad_queries)

    def _absorb(items):
        for item in items:
            if item.url and item.url not in seen:
                seen.add(item.url)
                out.append(item)

    for q in queries:
        _absorb(fetch_query(q, limit=per_person_limit))
        time.sleep(throttle)

    for spec in (feeds or []):
        _absorb(fetch_feed(spec, limit=feed_limit, timeout=feed_timeout))
        time.sleep(throttle)

    by_source: dict[str, int] = {}
    for it in out:
        by_source[it.source_id] = by_source.get(it.source_id, 0) + 1
    log.info("news: %d unique items across %d queries + %d feeds (%s)",
             len(out), len(queries), len(feeds or []),
             ", ".join(f"{k}={v}" for k, v in sorted(by_source.items())))
    return out
