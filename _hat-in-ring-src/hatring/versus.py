"""Head-to-head compare pages at ``/vs/<a>-vs-<b>/`` for marquee 2028 pairings.

A fixed editorial pair list (every cross-party marquee matchup plus the primary
rivalries people actually search) rendered as static, indexable pages: each side's
status tier, momentum + 30-day sparkline, cash on hand, and latest signal, then a
"Tale of the tape" table. Reuses the helpers in :mod:`hatring.pages` (sparkline,
money/date formatting, colors) so a vs page is a visual sibling of ``/c/<id>/``.

Pairs whose ids aren't in the dataset are skipped (logged, never fatal), so the
list can name people who churn out of candidates.json. ``out_dir/vs`` is created
even when zero pages render — the CI ``git add`` path list includes ``vs`` and
must never fail. HTML autoescaping is ON (names/headlines are untrusted).
"""
from __future__ import annotations
import json
import logging
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .scoring import enrich
from . import pages

log = logging.getLogger("hatring.versus")

# Marquee names per party (dataset ids). Cross-party grid = every (D, R) pairing.
MARQUEE_D = ["newsom", "harris", "buttigieg", "shapiro", "pritzker", "whitmer"]
MARQUEE_R = ["vance", "desantis", "rubio", "cruz", "trump"]
# The primary matchups worth a page of their own (same-party rivalries).
SAME_PARTY_PAIRS = [
    ("newsom", "harris"), ("newsom", "buttigieg"), ("harris", "buttigieg"),
    ("shapiro", "pritzker"), ("vance", "desantis"), ("vance", "rubio"),
    ("desantis", "cruz"), ("trump", "vance"), ("trump", "desantis"),
]


def marquee_pairs() -> list[tuple[str, str]]:
    """Full tracked pair set, each pair slug-ordered (a < b lexicographically),
    deduped, in stable declaration order: cross-party grid, then same-party."""
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for d in MARQUEE_D:
        for r in MARQUEE_R:
            pair = tuple(sorted((d, r)))
            if pair not in seen:
                seen.add(pair)
                out.append(pair)
    for x, y in SAME_PARTY_PAIRS:
        pair = tuple(sorted((x, y)))
        if pair not in seen:
            seen.add(pair)
            out.append(pair)
    return out


def _meta_desc(a_name: str, b_name: str, limit: int = 158) -> str:
    """Search-snippet description, capped at ~158 chars (Google's display
    width) without cutting mid-word — same tail logic as pages._meta_desc."""
    text = (f"{a_name} vs {b_name} for 2028: compare declared status, momentum "
            "trend, fundraising, and the latest signals — updated daily.")
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,;:·.-") + "…"


def _side(r: dict, built: date) -> dict:
    """One comparison column, fully precomputed (the template only interpolates)."""
    e = enrich(r, built)   # tier / statusLabel / score
    ls = pages._to_date(r.get("lastSignal"))
    days = (built - ls).days if ls else None
    return {
        "id": e["id"], "name": e["name"], "role": r.get("role") or "",
        "party": r.get("party") or "", "img": r.get("img"),
        "statusLabel": e["statusLabel"], "score": e["score"],
        "tier_color": pages.TIER_COLOR.get(e["tier"], "var(--t0)"),
        "party_color": pages.PARTY_COLOR.get(r.get("party"), "#7a7a7a"),
        "spark": pages._sparkline(r.get("series"), built),
        "cash": pages._money((r.get("money") or {}).get("cash_on_hand")),
        "headline": (r.get("headline") or "").strip(),
        # f-string day: strftime("%-d") is glibc-only and crashes on Windows
        "last_signal_human": (f"{ls:%B} {ls.day}, {ls.year}" if ls
                              else (r.get("lastSignal") or "")),
        "days_ago": pages._days_ago_human(days),
        "source_url": pages._safe_url(r.get("sourceUrl")),
    }


def render_vs_pages(records: list[dict], template_dir: Path, out_dir: Path,
                    built: date, canonical_base: str, og_default: str) -> list[dict]:
    """Write ``out_dir/vs/<slug>/index.html`` per renderable pair.

    Returns ``[{slug, url, lastmod, a_id, b_id, a_name, b_name}]`` for the
    sitemap and the candidate pages' head-to-head nav; ``lastmod`` is the later
    of the two lastSignal dates (fallback: build date) as YYYY-MM-DD.
    """
    out_dir = Path(out_dir)
    vs_root = out_dir / "vs"
    vs_root.mkdir(parents=True, exist_ok=True)   # CI `git add vs` must never fail
    by_id = {r.get("id"): r for r in records}
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    tmpl = env.get_template("vs.html.j2")
    as_of = f"{built:%B} {built.day}, {built.year}"  # %-d is glibc-only
    rendered: list[dict] = []
    for a_id, b_id in marquee_pairs():
        ra, rb = by_id.get(a_id), by_id.get(b_id)
        if ra is None or rb is None:
            missing = ", ".join(i for i, r in ((a_id, ra), (b_id, rb)) if r is None)
            log.info("versus: skip %s-vs-%s (not in dataset: %s)", a_id, b_id, missing)
            continue
        slug = f"{a_id}-vs-{b_id}"
        canonical = f"{canonical_base}vs/{slug}/"
        a, b = _side(ra, built), _side(rb, built)
        pair_name = f"{a['name']} vs {b['name']}"
        breadcrumbs = {
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home",
                 "item": canonical_base},
                {"@type": "ListItem", "position": 2, "name": "Head-to-head",
                 "item": canonical_base},
                {"@type": "ListItem", "position": 3, "name": pair_name,
                 "item": canonical},
            ],
        }
        breadcrumbs_jsonld = json.dumps(
            breadcrumbs, ensure_ascii=False).replace("<", "\\u003c")
        html = tmpl.render(
            a=a, b=b, pair_name=pair_name,
            meta_desc=_meta_desc(a["name"], b["name"]),
            canonical=canonical, og_image=og_default,
            breadcrumbs_jsonld=breadcrumbs_jsonld, as_of=as_of,
        )
        page_dir = vs_root / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(html, encoding="utf-8")
        sig_dates = [d for d in (pages._to_date(ra.get("lastSignal")),
                                 pages._to_date(rb.get("lastSignal"))) if d]
        rendered.append({
            "slug": slug, "url": canonical,
            "lastmod": (max(sig_dates).isoformat() if sig_dates
                        else built.isoformat()),
            "a_id": a_id, "b_id": b_id,
            "a_name": a["name"], "b_name": b["name"],
        })
    return rendered
