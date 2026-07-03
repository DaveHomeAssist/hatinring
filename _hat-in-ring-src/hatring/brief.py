"""Daily briefing + share card — make the daily pipeline emit a shareable
"what moved" artifact.

Outputs:
  * data/briefing.json      — consumed by the dashboard "Today's Briefing" section
  * <out>/share.html        — a static, screenshot-ready share card
  * <out>/assets/share/latest.svg — a 1200x630 vector share image (for OG tags)

Raster PNG generation is intentionally NOT required: requirements.txt ships no
imaging library, so we emit SVG + HTML and document PNG as an opt-in follow-up
(mission task 2.6 / constraint 12). The OG image points at the SVG; if a future
build adds cairosvg/Pillow, rasterize latest.svg -> latest.png and repoint.
"""
from __future__ import annotations
import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from .scoring import enrich

log = logging.getLogger("hatring.brief")

_TIERLABEL = {5: "Declared", 4: "Exploratory", 3: "Considering",
              2: "Positioning", 1: "Floated", 0: "Inactive"}


def _esc(s: str) -> str:
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def build_briefing(records: list[dict], review_count: int, today: date) -> dict:
    enr = [enrich(r, today) for r in records]
    recent = (today - timedelta(days=14)).isoformat()
    wk = (today - timedelta(days=7)).isoformat()

    movers = sorted([r for r in enr if r.get("delta")],
                    key=lambda r: (abs(r["delta"]), r["score"]), reverse=True)[:6]
    new_filers = [r for r in enr
                  if r["tier"] >= 4 and (r.get("lastSignal", "") >= recent)]
    transitions = []
    for r in records:
        for h in r.get("history", []) or []:
            if (h.get("date") or "") >= wk and h.get("to") != h.get("from"):
                transitions.append({"name": r["name"], "from": h.get("from"),
                                    "to": h.get("to"), "date": h.get("date")})
    transitions.sort(key=lambda h: h["date"], reverse=True)

    return {
        "date": today.isoformat(),
        "movers": [{"id": r["id"], "name": r["name"], "party": r["party"],
                    "delta": r["delta"], "score": r["score"],
                    "tier": r["tier"], "statusLabel": r["statusLabel"]} for r in movers],
        "new_filers": [{"id": r["id"], "name": r["name"], "tier": r["tier"],
                        "statusLabel": r["statusLabel"]} for r in new_filers][:6],
        "transitions": transitions[:6],
        "review_count": review_count,
        "totals": {
            "tracked": len(enr),
            "formal": sum(1 for r in enr if r.get("bucket") == "formal"),
            "considering": sum(1 for r in enr if r["tier"] == 3),
        },
    }


def write_briefing(brief: dict, data_dir: Path) -> Path:
    p = data_dir / "briefing.json"
    p.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def render_share_svg(brief: dict) -> str:
    movers = brief.get("movers", [])[:3]
    rows = []
    y = 300
    for m in movers:
        d = m["delta"]
        arrow = "▲" if d > 0 else ("▼" if d < 0 else "–")
        col = "#1f9d55" if d > 0 else ("#c0392b" if d < 0 else "#9a9a9a")
        sign = "+" if d > 0 else ""
        rows.append(
            f'<text x="80" y="{y}" font-size="40" fill="#f4efe7" '
            f'font-family="Georgia,serif">{_esc(m["name"])}</text>'
            f'<text x="1120" y="{y}" font-size="40" fill="{col}" text-anchor="end" '
            f'font-family="Georgia,serif">{arrow} {sign}{d}</text>')
        y += 78
    body = "".join(rows) or ('<text x="80" y="320" font-size="38" fill="#9a9a9a" '
                             'font-family="Georgia,serif">No movement today.</text>')
    tot = brief.get("totals", {})
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="Hat-in-Ring Radar daily briefing">
<rect width="1200" height="630" fill="#0f1115"/>
<rect width="1200" height="8" fill="#d23b3b"/>
<text x="80" y="120" font-size="58" fill="#f4efe7" font-family="Georgia,serif">Hat-in-Ring Radar</text>
<text x="80" y="170" font-size="28" fill="#8b929c" font-family="-apple-system,Arial,sans-serif">2028 presidential signal tracker · {_esc(brief.get("date",""))}</text>
<text x="80" y="245" font-size="30" fill="#d23b3b" font-family="-apple-system,Arial,sans-serif" letter-spacing="2">TOP MOVERS THIS WEEK</text>
{body}
<text x="80" y="585" font-size="26" fill="#8b929c" font-family="-apple-system,Arial,sans-serif">{tot.get("tracked",0)} tracked · {tot.get("formal",0)} formal · {tot.get("considering",0)} considering · hatinring.com</text>
</svg>'''


def render_share_html(brief: dict) -> str:
    desc = "Daily Hat-in-Ring Radar briefing for 2028 presidential campaign signal movement."
    title = f'Hat-in-Ring Radar — {_esc(brief.get("date",""))} briefing'
    items = "".join(
        f'<li><span>{_esc(m["name"])}</span>'
        f'<b class="{"up" if m["delta"]>0 else "dn" if m["delta"]<0 else "fl"}">'
        f'{"▲ +" if m["delta"]>0 else "▼ " if m["delta"]<0 else "– "}{m["delta"]}</b></li>'
        for m in brief.get("movers", [])[:6]) or "<li>No movement today.</li>"
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://hatinring.com/share.html">
<meta name="robots" content="noindex">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Hat-in-Ring Radar">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://hatinring.com/share.html">
<meta property="og:image" content="https://hatinring.com/assets/share/latest.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="https://hatinring.com/assets/share/latest.png">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<style>body{{margin:0;background:#0f1115;color:#f4efe7;font-family:-apple-system,Segoe UI,Arial,sans-serif;display:grid;place-items:center;min-height:100vh}}
.card{{width:min(640px,92vw);border:1px solid #2a2d33;border-radius:16px;padding:28px;background:#15171c}}
h1{{font-family:Georgia,serif;margin:0 0 4px;font-size:26px}}.sub{{color:#8b929c;margin-bottom:18px}}
ul{{list-style:none;padding:0;margin:0}}li{{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #23262d;font-size:17px}}
b.up{{color:#1f9d55}}b.dn{{color:#ff6b6b}}b.fl{{color:#8b929c}}a{{color:#6aa3ff}}</style></head>
<body><div class="card"><h1>Hat-in-Ring Radar</h1>
<div class="sub">Top movers · {_esc(brief.get("date",""))}</div>
<ul>{items}</ul>
<p class="sub" style="margin-top:18px">Live board → <a href="https://hatinring.com/">hatinring.com</a></p>
</div></body></html>'''


def _share_font(size: int, bold: bool = False):
    from PIL import ImageFont
    paths = ([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",   # GitHub Ubuntu runner
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ] if bold else [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]) + ["/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_share_png(brief: dict, out_path: Path) -> None:
    """1200x630 raster share card (Pillow). Social platforms (Facebook, X,
    LinkedIn, iMessage) don't render SVG previews, so this PNG is the real
    og:image; the SVG is kept as a lightweight fallback."""
    from PIL import Image, ImageDraw
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (15, 17, 21))            # #0f1115
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=(210, 59, 59))           # red top bar
    cream, muted, red, green = (244, 239, 231), (139, 146, 156), (210, 59, 59), (31, 157, 85)
    d.text((80, 64), "Hat-in-Ring Radar", font=_share_font(66, bold=True), fill=cream)
    d.text((80, 150), "2028 presidential signal tracker · " + str(brief.get("date", "")),
           font=_share_font(30), fill=muted)
    d.text((80, 224), "TOP MOVERS THIS WEEK", font=_share_font(30, bold=True), fill=red)
    rowf = _share_font(44)
    y, movers = 300, brief.get("movers", [])[:3]
    if movers:
        for m in movers:
            dl = m["delta"]
            arrow = "▲" if dl > 0 else "▼" if dl < 0 else "–"
            col = green if dl > 0 else red if dl < 0 else muted
            txt = f"{arrow} {'+' if dl > 0 else ''}{dl}"
            d.text((80, y), str(m["name"]), font=rowf, fill=cream)
            d.text((W - 80 - d.textlength(txt, font=rowf), y), txt, font=rowf, fill=col)
            y += 80
    else:
        d.text((80, 300), "No movement today.", font=rowf, fill=muted)
    t = brief.get("totals", {})
    d.text((80, 560),
           f'{t.get("tracked", 0)} tracked · {t.get("formal", 0)} formal · '
           f'{t.get("considering", 0)} considering · hatinring.com',
           font=_share_font(26), fill=muted)
    img.save(out_path, "PNG")


def write_share_assets(brief: dict, out_dir: Path) -> None:
    # Stable filenames (no per-date copies) so the committed repo doesn't grow a
    # share image per day. og:image points at the PNG (social can't render SVG).
    share = out_dir / "assets" / "share"
    share.mkdir(parents=True, exist_ok=True)
    (out_dir / "share.html").write_text(render_share_html(brief), encoding="utf-8")
    share.joinpath("latest.svg").write_text(render_share_svg(brief), encoding="utf-8")
    try:
        render_share_png(brief, share / "latest.png")
    except Exception as e:                                  # noqa: BLE001 - PNG is best-effort
        log.warning("share PNG skipped (%s)", e)


# ---- RSS daily-brief feed -------------------------------------------------
def _rfc822(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%a, %d %b %Y 12:00:00 +0000")
    except (ValueError, TypeError):
        return ""


def feed_item(brief: dict) -> dict:
    """A single 'what moved today' entry distilled from a briefing."""
    d = brief.get("date", "")
    parts = []
    mv = brief.get("movers", [])[:5]
    if mv:
        parts.append("Top movers: " + ", ".join(
            f'{m["name"]} {"+" if m["delta"] > 0 else ""}{m["delta"]}' for m in mv))
    nf = brief.get("new_filers", [])[:5]
    if nf:
        parts.append("Formal/new: " + ", ".join(f["name"] for f in nf))
    tr = brief.get("transitions", [])[:5]
    if tr:
        parts.append("Status changes: " + ", ".join(t["name"] for t in tr))
    # Deep-link the item to the top mover's own page so clicking a "what moved"
    # entry lands on the thing that moved; homepage when nothing moved.
    link = (f"https://hatinring.com/c/{mv[0]['id']}/"
            if mv and mv[0].get("id") else "https://hatinring.com/")
    return {"date": d, "guid": f"hatinring-{d}", "link": link,
            "title": f"What moved on the 2028 board — {d}",
            "desc": " · ".join(parts) or "No notable movement."}


def record_feed_item(brief: dict, data_dir: Path) -> list[dict]:
    """Append today's entry to data/feed_items.json (idempotent per date; last 30)."""
    path = data_dir / "feed_items.json"
    items = []
    if path.exists():
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            items = []
    it = feed_item(brief)
    items = [i for i in items if i.get("date") != it["date"]] + [it]
    items = sorted(items, key=lambda i: i.get("date", ""))[-30:]
    path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    return items


def render_feed(items: list[dict],
                self_url: str = "https://hatinring.com/feed.xml") -> str:
    rows = "".join(
        f"<item><title>{_esc(i['title'])}</title>"
        f"<link>{_esc(i.get('link') or 'https://hatinring.com/')}</link>"
        f'<guid isPermaLink="false">{_esc(i["guid"])}</guid>'
        f"<pubDate>{_rfc822(i.get('date', ''))}</pubDate>"
        f"<description>{_esc(i['desc'])}</description></item>"
        for i in reversed(items))             # newest first
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>\n'
            "<title>Hat-in-Ring Radar — daily movement</title>\n"
            "<link>https://hatinring.com/</link>\n"
            f'<atom:link href="{_esc(self_url)}" rel="self" type="application/rss+xml"/>\n'
            "<description>What moved on the 2028 presidential signal tracker, rebuilt daily. "
            "Status is not support.</description>\n"
            "<language>en-us</language>\n"
            f"{rows}\n</channel></rss>\n")


def write_feed(data_dir: Path, out_dir: Path) -> None:
    # Both filenames are kept on purpose: the daily CI workflow commits rss.xml
    # by literal path, and feed.xml is the advertised URL. Each carries its own
    # correct <atom:link rel="self">.
    path = data_dir / "feed_items.json"
    items = []
    if path.exists():
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            items = []
    (out_dir / "feed.xml").write_text(
        render_feed(items, "https://hatinring.com/feed.xml"), encoding="utf-8")
    (out_dir / "rss.xml").write_text(
        render_feed(items, "https://hatinring.com/rss.xml"), encoding="utf-8")
