"""Head-to-head /vs/ page tests (deterministic, offline)."""
from __future__ import annotations
import json
from datetime import date
from pathlib import Path

from hatring import pages, series, versus

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
BUILT = date(2026, 6, 13)
BASE = "https://hatinring.com/"
OG = BASE + "og.png"


def _rec(rid, name="Test Person", **kw):
    r = {"id": rid, "name": name, "party": "Democrat", "role": "Governor",
         "bucket": "considering", "keys": ["consideringQuote", "earlyState"],
         "conf": "High", "delta": 2, "lastSignal": "2026-06-01",
         "headline": "weighs a run", "why": "w", "quote": "", "tags": ["x"]}
    r.update(kw)
    return r


def _marquee_recs():
    return [
        _rec("newsom", name="Gavin Newsom"),
        _rec("harris", name="Kamala Harris", lastSignal="2026-06-05"),
        _rec("vance", name="JD Vance", party="Republican", role="Vice President"),
    ]


def test_pairs_built_only_when_both_ids_present(tmp_path):
    got = versus.render_vs_pages(_marquee_recs(), TEMPLATES, tmp_path, BUILT, BASE, OG)
    slugs = {p["slug"] for p in got}
    assert slugs == {"harris-vs-newsom", "newsom-vs-vance", "harris-vs-vance"}
    assert len(got) == 3
    on_disk = {d.name for d in (tmp_path / "vs").iterdir() if d.is_dir()}
    assert on_disk == slugs                       # nothing extra written
    for p in got:
        assert (tmp_path / "vs" / p["slug"] / "index.html").exists()
        assert p["url"] == f"{BASE}vs/{p['slug']}/"
    by_slug = {p["slug"]: p for p in got}
    hn = by_slug["harris-vs-newsom"]
    assert (hn["a_id"], hn["b_id"]) == ("harris", "newsom")   # slug order = a/b order
    assert (hn["a_name"], hn["b_name"]) == ("Kamala Harris", "Gavin Newsom")
    assert hn["lastmod"] == "2026-06-05"          # max(lastSignal of both)


def test_slug_alphabetical_and_head_metadata(tmp_path):
    versus.render_vs_pages(_marquee_recs(), TEMPLATES, tmp_path, BUILT, BASE, OG)
    assert not (tmp_path / "vs" / "newsom-vs-harris").exists()   # only sorted slug
    h = (tmp_path / "vs" / "harris-vs-newsom" / "index.html").read_text(encoding="utf-8")
    assert f'canonical" href="{BASE}vs/harris-vs-newsom/"' in h
    assert ("<title>Kamala Harris vs Gavin Newsom — 2028 head-to-head: "
            "status, momentum, money · Hat-in-Ring Radar</title>") in h
    assert 'content="index,follow"' in h and f'content="{OG}"' in h
    assert "Tale of the tape" in h and "data as of June 13, 2026" in h
    assert 'href="/c/harris/"' in h and 'href="/c/newsom/"' in h
    bc = json.loads(h.split('application/ld+json">', 1)[1].split("</script>", 1)[0])
    assert bc["@type"] == "BreadcrumbList"
    assert [i["name"] for i in bc["itemListElement"]] == \
        ["Home", "Head-to-head", "Kamala Harris vs Gavin Newsom"]


def test_vs_page_escapes_hostile_name(tmp_path):
    recs = [_rec("newsom", name="<img src=x onerror=alert(1)>"),
            _rec("harris", name="Kamala Harris")]
    versus.render_vs_pages(recs, TEMPLATES, tmp_path, BUILT, BASE, OG)
    h = (tmp_path / "vs" / "harris-vs-newsom" / "index.html").read_text(encoding="utf-8")
    assert "<img src=x onerror" not in h           # autoescaped, not a live tag
    assert "&lt;img src=x onerror" in h
    assert "</script><script>" not in h            # JSON-LD keeps < form


def test_zero_overlap_still_creates_vs_dir(tmp_path):
    got = versus.render_vs_pages([_rec("zeta"), _rec("omega")],
                                 TEMPLATES, tmp_path, BUILT, BASE, OG)
    assert got == []
    assert (tmp_path / "vs").is_dir()              # CI `git add vs` must not fail
    assert list((tmp_path / "vs").rglob("index.html")) == []


def test_sitemap_extra_urls_appended_with_lastmod(tmp_path):
    extra = [(BASE + "vs/harris-vs-newsom/", "2026-06-05")]
    pages.build_sitemap([_rec("alpha")], tmp_path, BASE, extra_urls=extra)
    sm = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert (f"<loc>{BASE}vs/harris-vs-newsom/</loc>"
            "<lastmod>2026-06-05</lastmod>") in sm
    assert sm.count("<loc>") == 4                  # home + about + 1 page + 1 vs
    assert f"<loc>{BASE}c/alpha/</loc>" in sm      # existing rows untouched


def test_candidate_page_head_to_head_nav_and_wikipedia_link(tmp_path):
    wiki = "https://en.wikipedia.org/wiki/Test_Person"
    recs = [_rec("a", links={"wikipedia": wiki}), _rec("b")]
    vs_links = {"a": [{"slug": "a-vs-b", "other_name": "Bee Person"}]}
    pages.render_candidate_pages(recs, TEMPLATES, tmp_path, BUILT, BASE, OG,
                                 vs_links=vs_links)
    ha = (tmp_path / "c" / "a" / "index.html").read_text(encoding="utf-8")
    assert "Head-to-head" in ha and 'href="/vs/a-vs-b/"' in ha and "vs Bee Person" in ha
    assert f'<a href="{wiki}" target="_blank" rel="noopener"' in ha
    assert "Wikipedia ↗" in ha
    hb = (tmp_path / "c" / "b" / "index.html").read_text(encoding="utf-8")
    assert "Head-to-head" not in hb                # no pairs -> no nav
    assert "Wikipedia" not in hb                   # no links.wikipedia -> no link

    # legacy call without vs_links still renders (and shows neither block)
    pages.render_candidate_pages([_rec("c")], TEMPLATES, tmp_path, BUILT, BASE, OG)
    hc = (tmp_path / "c" / "c" / "index.html").read_text(encoding="utf-8")
    assert "Head-to-head" not in hc and "Wikipedia" not in hc


def _snap_jsonl(path, rows_by_id):
    path.write_text("".join(json.dumps({"d": d, "id": rid, "s": s, "t": 3}) + "\n"
                            for rid, rows in rows_by_id.items()
                            for d, s in rows), encoding="utf-8")


def test_vs_pages_byte_identical_across_renders(tmp_path):
    p = tmp_path / "snap.jsonl"
    _snap_jsonl(p, {"newsom": [("2026-05-20", 50), ("2026-06-08", 57)],
                    "vance": [("2026-05-22", 30), ("2026-06-05", 28)]})
    recs = _marquee_recs()
    series.attach(recs, BUILT, p)   # same attach build.render runs before rendering
    recs[0]["money"] = {"cash_on_hand": 1234567.0}
    out1, out2 = tmp_path / "one", tmp_path / "two"
    versus.render_vs_pages(recs, TEMPLATES, out1, BUILT, BASE, OG)
    versus.render_vs_pages(recs, TEMPLATES, out2, BUILT, BASE, OG)
    for slug in ("harris-vs-newsom", "newsom-vs-vance", "harris-vs-vance"):
        h1 = (out1 / "vs" / slug / "index.html").read_text(encoding="utf-8")
        h2 = (out2 / "vs" / slug / "index.html").read_text(encoding="utf-8")
        assert h1 == h2                            # byte-stable for unchanged data
    h = (out1 / "vs" / "newsom-vs-vance" / "index.html").read_text(encoding="utf-8")
    assert h.count("<svg") == 2                    # both sides drew a sparkline
    assert "$1.2M" in h                            # cash on hand via pages._money
