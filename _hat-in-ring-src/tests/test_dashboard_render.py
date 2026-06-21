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
    html = out.read_text()
    # Corrupt the generated model in a way the harness must catch.
    broken, n = re.subn(
        r"filteredField\(\)\{",
        r"filteredField(){ throw new Error('forced smoke failure');",
        html, count=1,
    )
    assert n == 1, "expected to find filteredField() to corrupt"
    bad = tmp_path / "broken.html"
    bad.write_text(broken)

    res = subprocess.run(
        ["node", str(SMOKE), str(bad)],
        capture_output=True, text=True, timeout=60,
    )
    assert res.returncode != 0, "smoke harness should FAIL on the known-broken build but passed"
    assert "FAIL" in res.stdout
