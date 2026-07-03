"""Per-candidate static page + sitemap tests (deterministic, offline)."""
from __future__ import annotations
import json
import re
from datetime import date
from pathlib import Path

from hatring import pages, series

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
BUILT = date(2026, 6, 13)
BASE = "https://hatinring.com/"


def _rec(rid, name="Test Person", **kw):
    r = {"id": rid, "name": name, "party": "Democrat", "role": "Governor",
         "bucket": "considering", "keys": ["consideringQuote", "earlyState"],
         "conf": "High", "delta": 2, "lastSignal": "2026-06-01",
         "headline": "weighs a run", "why": "w", "quote": "", "tags": ["x"]}
    r.update(kw)
    return r


def test_pages_generated_per_record(tmp_path):
    recs = [_rec("alpha"), _rec("bravo", name="Bravo B")]
    n = pages.render_candidate_pages(recs, TEMPLATES, tmp_path, BUILT, BASE, BASE + "og.png")
    assert n == 2
    for cid in ("alpha", "bravo"):
        h = (tmp_path / "c" / cid / "index.html").read_text(encoding="utf-8")
        assert 'class="tier"' in h and "Why this momentum score" in h
        assert f'canonical" href="{BASE}c/{cid}/"' in h
        ld = json.loads(re.search(r'application/ld\+json">(.*?)</script>', h, re.S).group(1))
        assert ld["@type"] == "Person" and ld["url"] == f"{BASE}c/{cid}/"


def test_page_escapes_hostile_name(tmp_path):
    pages.render_candidate_pages([_rec("evil", name="<img src=x onerror=alert(1)>")],
                                 TEMPLATES, tmp_path, BUILT, BASE, BASE + "og.png")
    h = (tmp_path / "c" / "evil" / "index.html").read_text(encoding="utf-8")
    assert "<img src=x onerror" not in h            # autoescaped, not a live tag
    assert "&lt;img src=x onerror" in h


def test_page_renders_dated_sourced_evidence(tmp_path):
    recs = [_rec("a", evidence=[{"date": "2026-05-01", "headline": "X said Y",
                                 "url": "https://ex.com/a",
                                 "keys": ["consideringQuote"], "conf": "High"}])]
    pages.render_candidate_pages(recs, TEMPLATES, tmp_path, BUILT, BASE, BASE + "og.png")
    h = (tmp_path / "c" / "a" / "index.html").read_text(encoding="utf-8")
    assert "X said Y" in h and 'href="https://ex.com/a"' in h and "2026-05-01" in h


def test_money_not_filed_state(tmp_path):
    pages.render_candidate_pages([_rec("a")], TEMPLATES, tmp_path, BUILT, BASE, BASE + "og.png")
    h = (tmp_path / "c" / "a" / "index.html").read_text(encoding="utf-8")
    assert "No FEC financial report on file" in h   # never $0 for a non-filer


def _snap_jsonl(path, rid, rows):
    """Fixture momentum_snapshots.jsonl rows, same shape series.record_snapshot writes."""
    path.write_text("".join(json.dumps({"d": d, "id": rid, "s": s, "t": 3}) + "\n"
                            for d, s in rows), encoding="utf-8")


ARIA_RE = re.compile(r'aria-label="(Momentum over the last \d+ days?: '
                     r'from [\d.]+ to [\d.]+, high [\d.]+, low [\d.]+\.)"')


def test_sparkline_rendered_with_series_history(tmp_path):
    p = tmp_path / "snap.jsonl"
    _snap_jsonl(p, "a", [("2026-05-20", 50), ("2026-06-01", 55), ("2026-06-08", 52)])
    recs = [_rec("a")]
    series.attach(recs, BUILT, p)   # same attach build.render runs before rendering pages
    pages.render_candidate_pages(recs, TEMPLATES, tmp_path, BUILT, BASE, BASE + "og.png")
    h = (tmp_path / "c" / "a" / "index.html").read_text(encoding="utf-8")
    assert '<svg viewBox="0 0 240 48"' in h and 'role="img"' in h
    m = ARIA_RE.search(h)
    assert m, "aria sentence missing"
    assert h.count(m.group(1)) == 3            # aria-label + <title> + hidden figcaption
    assert 'style="stroke:var(--dem)"' in h    # line wears the party (entity) color
    assert '<circle' in h and 'r="4"' in h     # end-dot on the latest point


def test_sparkline_omitted_below_two_points(tmp_path):
    # attach with no snapshot file leaves only today's synthesized point (<2)
    recs = [_rec("solo")]
    series.attach(recs, BUILT, tmp_path / "missing.jsonl")
    assert sum(1 for pt in recs[0]["series"] if pt.get("s") is not None) == 1
    pages.render_candidate_pages(recs, TEMPLATES, tmp_path, BUILT, BASE, BASE + "og.png")
    h = (tmp_path / "c" / "solo" / "index.html").read_text(encoding="utf-8")
    assert "<svg" not in h                              # no broken/empty sparkline
    assert 'class="spark"' in h and "Why this momentum score" in h   # tile + page intact

    # a record that never went through attach (no `series` key) must also build clean
    pages.render_candidate_pages([_rec("bare")], TEMPLATES, tmp_path, BUILT, BASE, BASE + "og.png")
    h2 = (tmp_path / "c" / "bare" / "index.html").read_text(encoding="utf-8")
    assert "<svg" not in h2 and 'class="spark"' in h2


def test_sparkline_markup_deterministic(tmp_path):
    p = tmp_path / "snap.jsonl"
    _snap_jsonl(p, "a", [("2026-05-20", 50), ("2026-06-05", 57)])
    recs = [_rec("a")]
    series.attach(recs, BUILT, p)
    out1, out2 = tmp_path / "one", tmp_path / "two"
    pages.render_candidate_pages(recs, TEMPLATES, out1, BUILT, BASE, BASE + "og.png")
    pages.render_candidate_pages(recs, TEMPLATES, out2, BUILT, BASE, BASE + "og.png")
    h1 = (out1 / "c" / "a" / "index.html").read_text(encoding="utf-8")
    h2 = (out2 / "c" / "a" / "index.html").read_text(encoding="utf-8")
    fig = re.compile(r'<figure class="spark">.*?</figure>', re.S)
    assert fig.search(h1).group(0) == fig.search(h2).group(0)   # identical sparkline markup
    assert h1 == h2                     # whole page byte-stable for unchanged data


def test_sitemap_covers_home_about_and_pages(tmp_path):
    pages.build_sitemap([_rec("alpha"), _rec("bravo")], tmp_path, BASE)
    sm = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert sm.count("<loc>") == 4
    for loc in (BASE, BASE + "about.html", BASE + "c/alpha/", BASE + "c/bravo/"):
        assert f"<loc>{loc}</loc>" in sm


def test_person_jsonld_same_as_from_links(tmp_path):
    recs = [_rec("a", links={"wikipedia": "https://en.wikipedia.org/wiki/Test_Person"}),
            _rec("b")]
    pages.render_candidate_pages(recs, TEMPLATES, tmp_path, BUILT, BASE, BASE + "og.png")
    ha = (tmp_path / "c" / "a" / "index.html").read_text(encoding="utf-8")
    la = json.loads(re.search(r'application/ld\+json">(.*?)</script>', ha, re.S).group(1))
    assert la["sameAs"] == ["https://en.wikipedia.org/wiki/Test_Person"]
    hb = (tmp_path / "c" / "b" / "index.html").read_text(encoding="utf-8")
    lb = json.loads(re.search(r'application/ld\+json">(.*?)</script>', hb, re.S).group(1))
    assert "sameAs" not in lb                       # no links field -> no sameAs key
