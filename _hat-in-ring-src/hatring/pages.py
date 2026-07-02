"""Per-candidate static pages + sitemap.

One indexable HTML page per candidate at ``/c/<id>/`` — status (defined to an
evidentiary standard), the evidence trail (every signal, dated and sourced),
momentum + its math, status history, early-state activity, and money — plus
``Person`` JSON-LD. This is the SEO surface and the "send a candidate their own
page" artifact. Rendered at build time from the full in-memory record (the
``evidence``/``history`` that stay OUT of the dashboard SEED power these pages).

HTML autoescaping is ON here (candidate names/headlines are untrusted), so every
field is escaped; only the pre-serialized JSON-LD is marked safe.
"""
from __future__ import annotations
import json
import re
import urllib.parse
from datetime import date, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .scoring import enrich, breakdown as _breakdown, TIERS
from . import geo

REPO_ISSUES = "https://github.com/DaveHomeAssist/hatinring/issues/new"

TIER_COLOR = {5: "var(--t5)", 4: "var(--t4)", 3: "var(--t3)",
              2: "var(--t2)", 1: "var(--t1)", 0: "var(--t0)"}
PARTY_COLOR = {"Democrat": "var(--dem)", "Republican": "var(--rep)",
               "Libertarian": "var(--lib)", "Independent": "var(--ind)"}
# Tier definitions tightened to evidentiary standards (a campaign couldn't fairly
# dispute a badge): the page states exactly what evidence the tier requires.
STATUS_DEF = {
    5: 'an FEC Statement of Candidacy (Form 2) or an on-the-record campaign launch',
    4: 'a registered exploratory / testing-the-waters committee',
    3: 'a direct, on-the-record "I’m considering it" statement',
    2: 'campaign-style activity — early-state travel, donors, staffing, or media — with no on-record quote yet',
    1: 'a soft, hedged signal ("not ruling it out")',
    0: 'ruled out, constitutionally ineligible, or dormant',
}


def _safe_url(u) -> str:
    return u if isinstance(u, str) and re.match(r"^https?://", u) else ""


def _money(v) -> str:
    if v is None:
        return "—"
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    a = abs(v)
    if a >= 1e9:
        return f"${v/1e9:.1f}B"
    if a >= 1e6:
        return f"${v/1e6:.1f}M"
    if a >= 1e3:
        return f"${v/1e3:.0f}K"
    return f"${v:.0f}"


def _to_date(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except (ValueError, TypeError):
        return None


def _meta_desc(name: str, status_label: str, headline: str, limit: int = 158) -> str:
    """Search-snippet description: lead with the candidate's name + the query
    people actually type, cap at ~158 chars (Google's display width) without
    cutting mid-word."""
    text = f"Is {name} running for president in 2028? Current status: {status_label}."
    if headline:
        text = f"{text} {headline}"
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,;:·.-") + "…"


def _days_ago_human(days) -> str:
    """'1 day ago' / 'n days ago' / 'today' — pre-pluralized for the template."""
    if days is None:
        return ""
    if days == 0:
        return "today"
    return f"{days} day{'s' if days != 1 else ''} ago"


def _related(e: dict, enriched: list[dict], k: int = 4) -> list[dict]:
    """3-5 internal links per page: same party first, then nearest momentum
    score, excluding self. Deterministic (name tiebreak) so rebuilds are stable."""
    pool = sorted(
        (o for o in enriched if o["id"] != e["id"]),
        key=lambda o: (0 if o.get("party") == e.get("party") else 1,
                       abs(o["score"] - e["score"]), o["name"]))
    return [{"id": o["id"], "name": o["name"], "statusLabel": o["statusLabel"]}
            for o in pool[:k]]


def render_candidate_pages(records: list[dict], template_dir: Path, out_dir: Path,
                           built: date, canonical_base: str, og_default: str) -> int:
    env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    tmpl = env.get_template("candidate.html.j2")
    as_of = built.strftime("%B %-d, %Y")
    n = 0
    enriched_pairs = [(r, enrich(r, built)) for r in records]   # tier, statusLabel, score
    all_enriched = [e for _, e in enriched_pairs]
    for r, e in enriched_pairs:
        cid = e["id"]
        canonical = f"{canonical_base}c/{cid}/"
        bd = [{"label": lbl, "w": w} for lbl, w in _breakdown(r.get("keys", []), r["lastSignal"], built)]
        ls = _to_date(r.get("lastSignal"))
        days = (built - ls).days if ls else None
        money = r.get("money") or {}
        money_fmt = {k: _money(money.get(k)) for k in ("receipts", "disbursements", "cash_on_hand", "debts")}
        early = r.get("early_states") or {}
        early_list = sorted(
            ({"name": geo.STATE_NAME.get(s, s), "n": early[s]} for s in early),
            key=lambda x: x["n"], reverse=True)
        headline = (r.get("headline") or "").strip()
        meta = _meta_desc(r["name"], e["statusLabel"], headline)
        # Person entity stays factual (name/url/image/jobTitle) — the scored,
        # editorial status/momentum line does NOT belong in structured data.
        person = {
            "@context": "https://schema.org", "@type": "Person",
            "name": r["name"], "url": canonical,
        }
        if r.get("role"):
            person["jobTitle"] = r["role"]
        if r.get("img"):
            person["image"] = canonical_base + r["img"]
        person_jsonld = json.dumps(person, ensure_ascii=False).replace("<", "\\u003c")
        breadcrumbs = {
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home",
                 "item": canonical_base},
                {"@type": "ListItem", "position": 2, "name": "Candidates",
                 "item": canonical_base},
                {"@type": "ListItem", "position": 3, "name": r["name"],
                 "item": canonical},
            ],
        }
        breadcrumbs_jsonld = json.dumps(breadcrumbs, ensure_ascii=False).replace("<", "\\u003c")
        corrections_url = (REPO_ISSUES + "?" + urllib.parse.urlencode({
            "title": f"Correction: {r['name']}",
            "body": f"Page: {canonical}\nWhat's wrong:\nSource link:\n",
        }))
        html = tmpl.render(
            c=e, breakdown=bd, tiers=TIERS, tier_color=TIER_COLOR.get(e["tier"], "var(--t0)"),
            party_color=PARTY_COLOR.get(r.get("party"), "#7a7a7a"),
            status_def=STATUS_DEF.get(e["tier"], ""),
            source_url=_safe_url(r.get("sourceUrl")),
            last_signal_human=(ls.strftime("%B %-d, %Y") if ls else (r.get("lastSignal") or "")),
            days_ago=_days_ago_human(days),
            meta_desc=meta, canonical=canonical,
            og_image=(canonical_base + r["img"]) if r.get("img") else og_default,
            person_jsonld=person_jsonld, breadcrumbs_jsonld=breadcrumbs_jsonld,
            related=_related(e, all_enriched),
            evidence=r.get("evidence") or [],
            early_list=early_list, money_fmt=money_fmt,
            corrections_url=corrections_url, as_of=as_of,
        )
        page_dir = out_dir / "c" / cid
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(html)
        n += 1
    return n


def build_sitemap(records: list[dict], out_dir: Path, canonical_base: str,
                  built: date | None = None) -> None:
    # <lastmod> in W3C date form: build date for the daily-rebuilt home/about,
    # each record's lastSignal (fallback: build date) for its /c/<id>/ page.
    build_day = (built or date.today()).isoformat()
    rows = [(canonical_base, "daily", "1.0", build_day),
            (canonical_base + "about.html", "monthly", "0.7", build_day)]
    for r in records:
        ls = _to_date(r.get("lastSignal"))
        rows.append((f"{canonical_base}c/{r['id']}/", "weekly", "0.8",
                     ls.isoformat() if ls else build_day))
    body = "\n".join(
        f'  <url><loc>{loc}</loc><lastmod>{lm}</lastmod>'
        f'<changefreq>{cf}</changefreq><priority>{pr}</priority></url>'
        for loc, cf, pr, lm in rows)
    (out_dir / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n")
