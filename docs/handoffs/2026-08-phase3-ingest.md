# Phase 3 ingest — interface contract (as built)

**Date:** 2026-08-21 · **Status:** implemented (not a pending handoff)
**Companion:** `docs/decisions/2026-08-ingest-feeds.md` (the availability audit)

The plan scheduled this as a Claude-writes-the-contract / Codex-implements
handoff. It was implemented directly instead, so this is the **as-built**
contract rather than a brief: the interfaces a future source has to satisfy, the
invariants that must not regress, and the procedure for adding an outlet.

---

## 1. Feed registry (`config.yaml`)

```yaml
feed_limit: 40        # max entries taken per direct feed per run
feed_timeout: 20      # seconds before a slow feed is abandoned
feeds:
  - {id: nhpr, name: NHPR, kind: direct, url: "https://www.nhpr.org/rss.xml", state: NH}
  - {id: apnews, name: AP News, kind: gnews_site, query: 'site:apnews.com 2028 president'}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Stable source identifier, stamped onto every item as `source_id` and written into `signals.jsonl`. Must be unique. Never reuse an id for a different outlet — the audit trail is keyed on it. |
| `name` | yes | Display name. **Must match a `news.RELIABILITY` key**, or every signal from this outlet silently caps at `Low`. A test fails on an ungraded outlet. |
| `kind` | yes | `direct` (the outlet's own RSS) or `gnews_site` (a site-scoped Google News query, for outlets with no usable feed). |
| `url` | if `direct` | HTTPS RSS/Atom URL. |
| `query` | if `gnews_site` | The Google News query string. |
| `state` | no | `IA` / `NH` / `SC` / `NV`. **Documentation only** — real state attribution comes from `geo.tag_states()` reading the headline, never from this field. |

## 2. Source adapter (`hatring/news.py`)

```python
fetch_feed(spec: dict, limit: int = 40, timeout: float = 20.0) -> list[NewsItem]
```

**Contract:**

- **Never raises.** A dead, slow, or malformed feed logs and returns `[]`. One
  bad outlet degrades the ingest; it must never fail the daily run.
- Stamps every item with `source_id=spec["id"]`.
- Sets `source` to the outlet's registry `name` for direct feeds (they carry no
  `<source>` element), so `RELIABILITY` can grade it.
- Sets `scoped=False` for direct feeds and `scoped=True` for anything routed
  through a Google News query.
- Strips HTML from both title and summary before constructing the item — the
  title becomes a rendered headline, so this is the stored-XSS boundary.

`NewsItem.source_id` and `NewsItem.scoped` both carry defaults, so existing
fixtures constructed as `NewsItem(**row)` keep working unchanged.

## 3. Relevance gate (`hatring/classify.py`)

An item with `scoped=False` must clear `is_cycle_relevant()` before it is
classified at all:

> name a tracked watchlist person, **or** match `RACE_RX` (2028, presidential
> race/campaign/bid/primary, white house run, first-in-the-nation, …).

**Why it is not optional.** A Google News item was constrained by its query; a
state outlet's feed is its entire news river. Ungated, a county-commission story
mentioning "PAC" trips the `donors` regex, produces a discovery item with a
garbage name, and floods the human review queue — the one part of the system
that costs Dave time directly.

## 4. Cross-source dedupe (`hatring/merge.py`)

Two keys; a hit on **either** is a duplicate.

| Key | Form | Catches |
|---|---|---|
| primary | `person\|keys\|url` | the same item re-ingested |
| cross-source | `person\|keys\|t:<sha1(normalized-title)[:12]>` within **72h** | the same story syndicated to several outlets at several URLs |

`normalize_title()` strips a trailing " - Outlet" attribution, NFKD-normalizes,
deletes apostrophes (so `won't` == `won’t` == `wont`), lowercases, drops
punctuation, and collapses whitespace. It deliberately does **not** stem or
reorder words: two genuinely different stories must not collide.

**Why it shipped with the feeds and not after.** More raw signals means more
momentum. Adding sources without dedupe would have inflated the product's core
metric — the change would have looked like the field moving.

Suppressed duplicates are still **written** to `signals.jsonl` with
`applied: false` and `dupe_of: "cross-source"`, so the suppression is auditable
and re-runs stay idempotent. Rows predating this feature carry no title key and
are inert — no migration was needed.

---

## Adding a new outlet

1. Fetch the URL and confirm it returns entries; then parse it with `feedparser`
   and confirm entries carry a title, a link, and a parseable date. Both checks
   — a 200 with zero items is a real failure mode (see the Des Moines Register
   in the audit memo).
2. Add the entry to `feeds:` in `config.yaml`.
3. Add its display name to `news.RELIABILITY`. State outlets are `Medium`:
   credible primary reporting on early-state activity, but not wire-grade on
   their own.
4. If it has no usable RSS, use `kind: gnews_site` with a `site:`-scoped query
   rather than dropping the outlet.
5. Run `pytest -q`. Record the result in `docs/decisions/2026-08-ingest-feeds.md`.

## Acceptance criteria (all currently met)

- [x] ≥ 5 independent sources beyond Google News — **9 direct feeds**.
- [x] Every early state (IA/NH/SC/NV) covered by at least one outlet.
- [x] Cross-source dedupe shipped in the same commit as the feeds.
- [x] One dead feed cannot fail the daily run.
- [x] Every registry outlet graded for confidence (test-enforced).
- [x] Guardrails 1–5 and scoring parity unchanged.
- [ ] **14-day observation (due ~2026-09-04):** confirm `geo.py` early-state
      tallies carry signals attributed to state-outlet `source_id`s. If a feed
      contributes zero usable signals, revisit its limit or retire it.
