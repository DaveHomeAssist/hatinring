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
