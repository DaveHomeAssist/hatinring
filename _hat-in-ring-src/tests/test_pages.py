"""Per-candidate static page + sitemap tests (deterministic, offline)."""
from __future__ import annotations
import json
import re
from datetime import date
from pathlib import Path

from hatring import pages

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
        h = (tmp_path / "c" / cid / "index.html").read_text()
        assert 'class="tier"' in h and "Why this momentum score" in h
        assert f'canonical" href="{BASE}c/{cid}/"' in h
        ld = json.loads(re.search(r'application/ld\+json">(.*?)</script>', h, re.S).group(1))
        assert ld["@type"] == "Person" and ld["url"] == f"{BASE}c/{cid}/"


def test_page_escapes_hostile_name(tmp_path):
    pages.render_candidate_pages([_rec("evil", name="<img src=x onerror=alert(1)>")],
                                 TEMPLATES, tmp_path, BUILT, BASE, BASE + "og.png")
    h = (tmp_path / "c" / "evil" / "index.html").read_text()
    assert "<img src=x onerror" not in h            # autoescaped, not a live tag
    assert "&lt;img src=x onerror" in h


def test_page_renders_dated_sourced_evidence(tmp_path):
    recs = [_rec("a", evidence=[{"date": "2026-05-01", "headline": "X said Y",
                                 "url": "https://ex.com/a",
                                 "keys": ["consideringQuote"], "conf": "High"}])]
    pages.render_candidate_pages(recs, TEMPLATES, tmp_path, BUILT, BASE, BASE + "og.png")
    h = (tmp_path / "c" / "a" / "index.html").read_text()
    assert "X said Y" in h and 'href="https://ex.com/a"' in h and "2026-05-01" in h


def test_money_not_filed_state(tmp_path):
    pages.render_candidate_pages([_rec("a")], TEMPLATES, tmp_path, BUILT, BASE, BASE + "og.png")
    h = (tmp_path / "c" / "a" / "index.html").read_text()
    assert "No FEC financial report on file" in h   # never $0 for a non-filer


def test_sitemap_covers_home_about_and_pages(tmp_path):
    pages.build_sitemap([_rec("alpha"), _rec("bravo")], tmp_path, BASE)
    sm = (tmp_path / "sitemap.xml").read_text()
    assert sm.count("<loc>") == 4
    for loc in (BASE, BASE + "about.html", BASE + "c/alpha/", BASE + "c/bravo/"):
        assert f"<loc>{loc}</loc>" in sm
