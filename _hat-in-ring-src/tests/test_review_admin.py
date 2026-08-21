"""Local review admin surface (Phase 7).

Hand-editing `data/review_decisions.json` is the most error-prone step in the
human loop — the pipeline already carries a fail-safe for a corrupt hand edit,
which is evidence the failure happens. `review.html` replaces that edit with a
page that cannot emit a malformed file.

Two properties are load-bearing:
  1. it is structurally incapable of exporting an invalid decisions file, and it
     refuses a queue whose schema has drifted rather than mis-rendering it;
  2. it is NEVER published — it lives under `_hat-in-ring-src/`, which the Pages
     deploy explicitly excludes.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest
import yaml

from hatring.build import render
from hatring.merge import review_rid

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
REVIEW_HTML = ROOT / "review.html"
CHECK = Path(__file__).resolve().parent / "review_check.js"
DEPLOY_WF = REPO / ".github" / "workflows" / "deploy-pages.yml"


def test_review_page_exists_inside_the_pipeline_source_tree():
    assert REVIEW_HTML.exists(), "review.html is missing"
    assert REVIEW_HTML.parent.name == "_hat-in-ring-src", \
        "review.html must live inside _hat-in-ring-src/ to stay unpublished"


# ---- 1. it cannot emit a malformed decisions file -------------------------
@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_review_page_validation_and_export_gating():
    res = subprocess.run(["node", str(CHECK), str(REVIEW_HTML)],
                         capture_output=True, text=True, timeout=60)
    assert res.returncode == 0, f"review page check failed:\n{res.stdout}\n{res.stderr}"
    assert "PASS" in res.stdout


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_review_check_actually_fails_on_a_broken_page(tmp_path):
    """Sanity: a green run above must mean something."""
    broken = tmp_path / "review.html"
    html = REVIEW_HTML.read_text(encoding="utf-8")
    # Neuter the unknown-field rule; the harness must notice.
    patched, n = re.subn(r"if \(REQUIRED\.indexOf\(f\) < 0 && OPTIONAL\.indexOf\(f\) < 0\) \{",
                         "if (false) {", html, count=1)
    assert n == 1, "expected to find the unknown-field guard to corrupt"
    broken.write_text(patched, encoding="utf-8")
    res = subprocess.run(["node", str(CHECK), str(broken)],
                         capture_output=True, text=True, timeout=60)
    assert res.returncode != 0 and "FAIL" in res.stdout


def test_page_is_self_contained_and_makes_no_third_party_requests():
    """No build step, no CDN: it must work from a plain `python -m http.server`."""
    html = REVIEW_HTML.read_text(encoding="utf-8")
    assert "<script src=" not in html, "review.html must not load external scripts"
    assert "<link rel=\"stylesheet\"" not in html, "review.html must not load external CSS"
    for host in ("https://cdn", "http://cdn", "unpkg.com", "jsdelivr", "googleapis.com"):
        assert host not in html, f"review.html reaches out to {host}"
    # The only fetch it makes is the same-directory queue.
    fetches = re.findall(r"fetch\((.*?)[,)]", html)
    assert fetches == ['"./data/review_queue.json"'], f"unexpected fetch targets: {fetches}"
    assert 'name="robots" content="noindex,nofollow"' in html


def test_export_shape_matches_what_the_pipeline_consumes():
    """The page emits [{rid, action}] — the exact shape reconcile_review reads."""
    html = REVIEW_HTML.read_text(encoding="utf-8")
    assert '{ rid: rid, action: decisions[rid] }' in html
    assert 'download: "review_decisions.json"' in html


def test_page_understands_the_real_committed_queue():
    """Guards against the page and merge.py drifting apart: every field merge.py
    stamps must be one the page accepts."""
    qpath = ROOT / "data" / "review_queue.json"
    if not qpath.exists():
        pytest.skip("no committed review_queue.json")
    queue = json.loads(qpath.read_text(encoding="utf-8"))
    html = REVIEW_HTML.read_text(encoding="utf-8")
    required = set(json.loads(re.search(r'var REQUIRED = (\[.*?\]);', html).group(1)))
    optional = set(json.loads(re.search(r'var OPTIONAL = (\[.*?\]);', html).group(1)))
    known = required | optional
    for i, item in enumerate(queue):
        extra = set(item) - known
        assert not extra, f"review_queue[{i}] has fields review.html rejects: {extra}"
        missing = required - set(item)
        assert not missing, f"review_queue[{i}] missing fields review.html requires: {missing}"
        # rid must be the id the page keys decisions on
        assert item["rid"] == review_rid(item.get("name", ""), item.get("url", ""),
                                         item.get("keys")), \
            f"review_queue[{i}]: rid does not match merge.review_rid()"


# ---- 2. it is never published --------------------------------------------
def test_pages_deploy_excludes_the_pipeline_source_tree():
    wf = yaml.safe_load(DEPLOY_WF.read_text(encoding="utf-8"))
    stage = next(s for s in wf["jobs"]["deploy"]["steps"]
                 if "rsync" in str(s.get("run", "")))
    assert "--exclude '_hat-in-ring-src'" in stage["run"], \
        "the Pages artifact no longer excludes _hat-in-ring-src/ — review.html would be published"


def test_review_html_is_absent_from_a_built_site(tmp_path):
    """Belt and braces: the build stages nothing named review.html."""
    recs = [{"id": "alpha", "name": "Alpha", "party": "Democrat", "role": "Gov",
             "bucket": "soft", "keys": ["softConsidering"], "conf": "Low",
             "delta": 0, "lastSignal": "2026-06-01", "headline": "h",
             "why": "w", "quote": "", "tags": []}]
    src = tmp_path / "candidates.json"
    src.write_text(json.dumps(recs), encoding="utf-8")
    out_dir = tmp_path / "site"
    render(src, ROOT / "templates", out_dir / "index.html", built=date(2026, 6, 13))
    staged = [p.name for p in out_dir.rglob("*") if p.is_file()]
    assert "review.html" not in staged, f"review.html was staged into the site: {staged}"
