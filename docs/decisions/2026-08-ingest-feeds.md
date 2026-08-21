# Ingest diversification — feed availability audit

**Date:** 2026-08-21 · **Phase:** 3 (ingest diversification) · **Status:** implemented
**Decision owner:** Dave · **Audited by:** Claude

## Why

Every news signal in the product came from one upstream: Google News RSS. That
is a single point of failure for the whole ingest path, and — because Google
News is queried by name — it structurally under-reports early-state activity,
which is reported by IA/NH/SC/NV outlets that a name query rarely surfaces.

## Method

Each candidate outlet was fetched live on 2026-08-21 over HTTPS with a normal
browser UA, then re-fetched through `feedparser` to confirm it yields entries
with usable titles, links, and parseable dates. An outlet counts as usable only
if both checks pass.

## Results

### Adopted — direct RSS (`kind: direct`)

| id | Outlet | State | Entries | Notes |
|----|--------|-------|---------|-------|
| `thehill` | The Hill | — | 15 | Campaign sub-feed, not homenews: better signal density |
| `politico` | Politico | — | 30 | `rss.politico.com` works; `www.politico.com/rss/*` returns 403 |
| `iowacapital` | Iowa Capital Dispatch | IA | 100 | States Newsroom |
| `nhbulletin` | New Hampshire Bulletin | NH | 100 | States Newsroom |
| `nhpr` | NHPR | NH | 10 | `/rss.xml` only — `/rss` and `/index.rss` 404 |
| `scdailygazette` | SC Daily Gazette | SC | 100 | States Newsroom |
| `postandcourier` | The Post and Courier | SC | 50 | Search-backed RSS endpoint |
| `nevadacurrent` | Nevada Current | NV | 100 | States Newsroom |
| `nevadaindependent` | The Nevada Independent | NV | 100 | |

Nine direct feeds; **all four early states covered by at least one outlet**,
three of them by two. This clears the phase's ">= 5 independent sources" bar.

### No usable public RSS — fell back to `kind: gnews_site`

| Outlet | What happened | Fallback |
|--------|---------------|----------|
| AP | `apnews.com/hub/ap-top-news.rss` → 404; `feeds.apnews.com` → connection failure | `site:apnews.com 2028 president` |
| Reuters | `reutersagency.com/feed/` → 404 (public feeds retired) | `site:reuters.com 2028 president` |
| C-SPAN | `/rss/` and `/rss/?type=all` → 403 | `site:c-span.org 2028 president` |
| Des Moines Register | Gannett endpoints return 200 with **zero items** | `site:desmoinesregister.com 2028 president OR caucuses` |

The plan anticipated AP/Reuters being unavailable; this is that fallback path,
so the phase did not stall. NPR (`feeds.npr.org` → 403) and Axios
(`api.axios.com/feed/` → 403) were probed and not adopted — neither is needed
for early-state coverage and both are already reachable via Google News.

## Consequences that required code

1. **Relevance gate (`classify.RACE_RX`).** A Google News item is constrained by
   its query; a state outlet's feed is its *whole* news river. Without a gate, a
   county-commission story mentioning "PAC" would manufacture a discovery item
   with a garbage name and flood the human review queue. Unscoped items must now
   either name a tracked person or visibly concern the presidential race.

2. **Cross-source dedupe (`merge._title_sid`).** The existing dedupe key is
   `person|keys|url`, which counts one syndicated story once per outlet. More
   raw signals means more momentum, so adding sources without dedupe would have
   inflated the product's core metric. A matching normalized headline for the
   same person and keys inside 72h is now treated as the same story. **This
   shipped in the same commit as the feeds, never separately.**

3. **Per-feed timeout + isolation.** `fetch_feed` bounds each fetch and swallows
   its own failures, so one dead outlet degrades the ingest rather than failing
   the daily run.

## Confidence grading

State outlets are graded **Medium** in `news.RELIABILITY` — credible primary
reporting on the early-state activity they exist to catch, without letting a
single local story certify a wire-grade claim. A test fails if a registry outlet
has no grade at all, since an ungraded outlet silently caps at Low.

## Follow-up

- **14-day check (due ~2026-09-04):** confirm `geo.py` early-state tallies carry
  signals attributed to state-outlet `source_id`s. If any feed contributes zero
  usable signals, reconsider its `feed_limit` or retire it.
- Feed URLs rot. A feed that starts returning zero entries is logged, not
  alerted — if that proves too quiet, promote it to a Phase 1 style alert.
