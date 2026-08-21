"""Regression test: the rendered dashboard must actually populate on a first
visit (empty localStorage).

A JS throw during render (e.g. PREFS.party undefined when no saved prefs exist)
leaves the board, movement feed and status-tier legend blank while the stat
cards still show — a silent, ugly failure that unit-testing the Python side
can't catch. This renders the dashboard offline and runs it through a headless
Node smoke check.

Skipped automatically if Node isn't on PATH (it is on GitHub Actions runners).
"""
from __future__ import annotations
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest

from hatring.build import render

ROOT = Path(__file__).resolve().parent.parent
SMOKE = Path(__file__).resolve().parent / "dashboard_smoke.js"


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_dashboard_populates_on_first_visit(tmp_path):
    out = tmp_path / "index.html"
    render(ROOT / "data" / "seed.json", ROOT / "templates", out, built=date(2026, 6, 13))
    assert out.exists()

    res = subprocess.run(
        ["node", str(SMOKE), str(out)],
        capture_output=True, text=True, timeout=60,
    )
    assert res.returncode == 0, (
        "dashboard smoke check failed (board did not fully render on first visit):\n"
        f"STDOUT: {res.stdout}\nSTDERR: {res.stderr}"
    )
    assert "PASS" in res.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_dashboard_smoke_catches_a_broken_build(tmp_path):
    """Sanity: the smoke harness actually fails when render would throw.

    We corrupt the built HTML to remove PREFS defaults and confirm the smoke
    test reports failure — so a green run genuinely means something.
    """
    out = tmp_path / "index.html"
    render(ROOT / "data" / "seed.json", ROOT / "templates", out, built=date(2026, 6, 13))
    html = out.read_text(encoding="utf-8")
    # Corrupt the generated model in a way the harness must catch.
    broken, n = re.subn(
        r"filteredField\(\)\{",
        r"filteredField(){ throw new Error('forced smoke failure');",
        html, count=1,
    )
    assert n == 1, "expected to find filteredField() to corrupt"
    bad = tmp_path / "broken.html"
    bad.write_text(broken, encoding="utf-8")

    res = subprocess.run(
        ["node", str(SMOKE), str(bad)],
        capture_output=True, text=True, timeout=60,
    )
    assert res.returncode != 0, "smoke harness should FAIL on the known-broken build but passed"
    assert "FAIL" in res.stdout


# ---------------------------------------------------------------------------
# Staleness banner (Phase 1: operational hardening)
#
# A stalled pipeline cannot rebuild the page, so the served HTML must detect its
# own age client-side. These assert the markup + threshold constant survive a
# render; ux_check.js drives the actual date logic.
# ---------------------------------------------------------------------------
def _render_html(tmp_path, built=date(2026, 6, 13)):
    out = tmp_path / "index.html"
    render(ROOT / "data" / "seed.json", ROOT / "templates", out, built=built)
    return out.read_text(encoding="utf-8")


def test_staleness_banner_markup_present(tmp_path):
    html = _render_html(tmp_path)
    assert 'class="hir-stale"' in html, "staleness banner markup missing"
    # Announced to assistive tech without stealing focus.
    assert 'role="status"' in html, "staleness banner must be a live region"
    # Gated on the model flag, so a fresh build renders nothing.
    assert 'value="{{ isStale }}"' in html
    assert "{{ staleMessage }}" in html


def test_staleness_threshold_constant_is_48h(tmp_path):
    html = _render_html(tmp_path)
    assert "STALE_AFTER_DAYS = 2;" in html, "48-hour staleness threshold changed"
    # Whole-UTC-day differencing is what makes the banner immune to client clock
    # skew; a timestamp subtraction here would reintroduce false positives.
    assert "Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate())" in html


def test_staleness_banner_meets_wcag_aa_contrast(tmp_path):
    """Banner text (#13294B) on its amber ground (#F6E7C3) must clear AA 4.5:1."""
    html = _render_html(tmp_path)
    assert "background:#F6E7C3" in html and "color:#13294B" in html

    def channel(v: int) -> float:
        srgb = v / 255
        return srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4

    def lum(rgb) -> float:
        return 0.2126 * channel(rgb[0]) + 0.7152 * channel(rgb[1]) + 0.0722 * channel(rgb[2])

    fg, bg = lum((0x13, 0x29, 0x4B)), lum((0xF6, 0xE7, 0xC3))
    contrast = (max(fg, bg) + 0.05) / (min(fg, bg) + 0.05)
    assert contrast >= 4.5, f"staleness banner contrast {contrast:.2f} below WCAG AA"


def test_staleness_banner_sits_above_the_sticky_header(tmp_path):
    """In-flow above the sticky header — a position:fixed bar would overlap it."""
    html = _render_html(tmp_path)
    assert html.index('class="hir-stale"') < html.index('class="hir-header"')
    banner = html[html.index('class="hir-stale"'):]
    banner = banner[:banner.index("</div>")]
    assert "position:fixed" not in banner


# ---------------------------------------------------------------------------
# Timeline view (Phase 6)
# ---------------------------------------------------------------------------
def _with_history(tmp_path):
    """A dataset that definitely produces timeline events, so the assertions do
    not depend on whatever happens to be in the committed snapshot trail."""
    recs = [
        {"id": "alpha", "name": "Alpha Candidate", "party": "Democrat",
         "role": "Governor", "bucket": "considering", "keys": ["consideringQuote"],
         "conf": "High", "delta": 0, "lastSignal": "2026-05-15",
         "headline": "Alpha weighs a run", "why": "w", "quote": "", "tags": [],
         "history": [{"date": "2026-03-01", "from": 1, "to": 3,
                      "reason": "Alpha says he is considering it"}]},
        {"id": "bravo", "name": "Bravo Candidate", "party": "Republican",
         "role": "Senator", "bucket": "out", "keys": ["ruledOut"],
         "conf": "High", "delta": 0, "lastSignal": "2026-04-02",
         "headline": "Bravo rules it out", "why": "w", "quote": "", "tags": [],
         "history": [{"date": "2026-04-02", "from": 4, "to": 0,
                      "reason": "Bravo rules out a 2028 run"}]},
    ]
    src = tmp_path / "candidates.json"
    src.write_text(json.dumps(recs), encoding="utf-8")
    out = tmp_path / "index.html"
    render(src, ROOT / "templates", out, built=date(2026, 6, 13))
    return out.read_text(encoding="utf-8")


def test_timeline_view_markup_present(tmp_path):
    html = _render_html(tmp_path)
    assert 'value="{{ isTimeline }}"' in html, "Timeline view block missing"
    assert 'class="hir-tl-track"' in html, "timeline track missing"
    assert "['timeline','Timeline']" in html, "Timeline nav tab missing"
    # The list rows are real buttons, so they are focusable and keyboard-operable
    # without re-implementing button semantics on a div.
    assert '<button type="button" onClick="{{ e.open }}" aria-label="{{ e.label }}"' in html


def test_timeline_events_are_injected_with_their_evidence(tmp_path):
    html = _with_history(tmp_path)
    m = re.search(r"\n\s*TIMELINE\s*=\s*(.*?);\n", html, re.S)
    assert m, "TIMELINE constant not injected"
    events = json.loads(m.group(1).replace("\\u003c", "<"))
    assert len(events) == 2, f"expected 2 timeline events, got {len(events)}"
    by_id = {e["id"]: e for e in events}
    assert by_id["alpha"]["direction"] == "up"
    assert by_id["bravo"]["direction"] == "down"
    assert by_id["alpha"]["reason"] == "Alpha says he is considering it"
    assert all(e["reconstructed"] is False for e in events)
    # oldest first in the artifact
    assert [e["date"] for e in events] == ["2026-03-01", "2026-04-02"]


def test_timeline_hash_route_is_recognised(tmp_path):
    html = _render_html(tmp_path)
    assert "field|dossiers|wire|timeline" in html, "#/timeline route not registered"
