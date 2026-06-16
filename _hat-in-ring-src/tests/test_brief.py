"""Daily-briefing tests: empty / minimal / normal datasets + share-asset output."""
from __future__ import annotations
import json
from datetime import date

import pytest

from hatring import brief

TODAY = date(2026, 6, 15)


def test_feed_records_idempotent_and_renders(tmp_path):
    b = brief.build_briefing([_rec("a", ["consideringQuote"], "2026-06-14",
                                   delta=12, name="Alpha")], 0, TODAY)
    brief.record_feed_item(b, tmp_path)
    brief.record_feed_item(b, tmp_path)                 # same date -> no dup
    items = json.loads((tmp_path / "feed_items.json").read_text())
    assert len(items) == 1 and items[0]["date"] == TODAY.isoformat()
    brief.write_feed(tmp_path, tmp_path)
    feed = (tmp_path / "feed.xml").read_text()
    assert feed.startswith("<?xml") and 'rss version="2.0"' in feed
    assert "Alpha" in feed and "What moved" in feed and "<pubDate>" in feed


def test_share_png_is_1200x630(tmp_path):
    """The PNG is the real og:image (social can't render SVG); verify size + magic."""
    pytest.importorskip("PIL")
    from PIL import Image
    b = brief.build_briefing([_rec("a", ["donors"], "2026-06-14", delta=4)], 0, TODAY)
    brief.write_share_assets(b, tmp_path)
    png = tmp_path / "assets" / "share" / "latest.png"
    assert png.exists() and png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert Image.open(png).size == (1200, 630)


def _rec(rid, keys, last, delta=0, history=None, name=None):
    r = {"id": rid, "name": name or rid.title(), "party": "Democrat", "role": "r",
         "bucket": "considering", "keys": keys, "conf": "High", "delta": delta,
         "lastSignal": last, "headline": "h", "why": "w", "quote": "", "tags": []}
    if history:
        r["history"] = history
    return r


def test_briefing_empty_dataset():
    b = brief.build_briefing([], 0, TODAY)
    assert b["movers"] == [] and b["new_filers"] == [] and b["transitions"] == []
    assert b["totals"]["tracked"] == 0 and b["date"] == TODAY.isoformat()


def test_briefing_minimal():
    b = brief.build_briefing([_rec("a", ["donors"], "2026-06-14")], 0, TODAY)
    assert b["totals"]["tracked"] == 1 and isinstance(b["movers"], list)


def test_briefing_normal_movers_filers_transitions():
    recs = [
        _rec("a", ["consideringQuote"], "2026-06-14", delta=12),
        _rec("b", ["declared"], "2026-06-10", delta=0),
        _rec("c", ["softConsidering"], "2026-06-13", delta=-5,
             history=[{"date": "2026-06-13", "from": 0, "to": 1}]),
    ]
    b = brief.build_briefing(recs, 2, TODAY)
    assert "a" in [m["id"] for m in b["movers"]]            # carries a delta
    assert any(f["id"] == "b" for f in b["new_filers"])     # declared + recent
    assert any(t["name"] == "C" for t in b["transitions"])  # status change within 7d
    assert b["review_count"] == 2


def test_share_assets_written(tmp_path):
    b = brief.build_briefing([_rec("a", ["donors"], "2026-06-14", delta=4)], 0, TODAY)
    brief.write_share_assets(b, tmp_path)
    assert (tmp_path / "share.html").exists()
    svg = (tmp_path / "assets" / "share" / "latest.svg").read_text()
    assert svg.lstrip().startswith("<svg") and "1200" in svg and "630" in svg


def test_share_svg_escapes_hostile_name():
    b = brief.build_briefing([_rec("x", ["donors"], "2026-06-14", delta=4,
                                   name="<script>alert(1)</script>")], 0, TODAY)
    svg = brief.render_share_svg(b)
    assert "<script>" not in svg and "&lt;script&gt;" in svg
