"""Public data contract: /data/latest.json (schema `hatinring.v1`).

External consumers — the iOS app, embeds, estate tooling — read this artifact
instead of scraping index.html, so it is a published interface and not an
implementation detail. These tests pin the three properties that make it safe
to depend on:

  1. it validates against the committed JSON Schema;
  2. it is DETERMINISTIC (identical inputs -> byte-identical bytes), so the
     daily commit is empty on a no-change day rather than churning the repo;
  3. it publishes ONLY allowlisted fields, so a curated / internal / review-queue
     field added to a record later cannot silently start being published.

Fully offline: a pinned build date and a synthetic dataset, no network.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from hatring import build as buildmod
from hatring.build import render

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
SCHEMA_PATH = ROOT / "schemas" / "latest.v1.schema.json"
BUILT = date(2026, 6, 13)   # pinned: never depends on today's date

# Sentinels for fields that must NEVER reach the public feed.
_SECRET_FIELDS = {
    "history": [{"date": "2026-01-01", "from": 1, "to": 3, "secret": "HIST_SENTINEL"}],
    "fec_ids": ["FEC_SENTINEL_P00"],
    # `keys` is required on a real evidence row (merge.py always writes it);
    # candidate.html.j2 iterates e['keys'] and would otherwise resolve the dict's
    # own .keys method.
    "evidence": [{"date": "2026-05-01", "headline": "EVID_SENTINEL",
                  "url": "https://example.invalid/e", "keys": ["donors"],
                  "conf": "Low"}],
    "internal_note": "INTERNAL_SENTINEL",      # a field nobody remembered to deny
    "review_rid": "RID_SENTINEL",
}


def _dataset() -> list[dict]:
    recs = [
        {
            "id": "alpha", "name": "Alpha Candidate", "party": "Democrat",
            "role": "Governor", "bucket": "considering",
            "keys": ["consideringQuote", "earlyState"], "conf": "High",
            "delta": 3, "lastSignal": "2026-05-15", "headline": "Alpha weighs a run",
            "why": "Strong early-state ties", "quote": "I'm thinking about it",
            "tags": ["midwest"], "pollLead": "",
        },
        {
            "id": "bravo", "name": "Bravo Candidate", "party": "Republican",
            "role": "Senator", "bucket": "formal", "keys": ["declared"],
            "conf": "Very high", "delta": -1, "lastSignal": "2026-06-01",
            "headline": "Bravo files FEC Form 2", "why": "Formal launch",
            "quote": "", "tags": [],
        },
    ]
    for r in recs:
        r.update({k: v for k, v in _SECRET_FIELDS.items()})
    return recs


def _build(tmp_path, recs=None, name="site") -> Path:
    """Render into an isolated site dir; return the emitted latest.json path."""
    recs = _dataset() if recs is None else recs
    src = tmp_path / f"{name}-candidates.json"
    src.write_text(json.dumps(recs, ensure_ascii=False), encoding="utf-8")
    out_dir = tmp_path / name
    render(src, TEMPLATES, out_dir / "index.html", built=BUILT)
    return out_dir / "data" / "latest.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# ---- 1. schema ------------------------------------------------------------
def test_schema_file_is_itself_a_valid_json_schema(schema):
    Draft202012Validator.check_schema(schema)


def test_latest_json_is_emitted_at_the_public_path(tmp_path):
    p = _build(tmp_path)
    assert p.exists(), "build did not emit data/latest.json next to index.html"
    # The Pages artifact excludes _hat-in-ring-src/, so the feed MUST be staged
    # at the site root to be reachable at hatinring.com/data/latest.json.
    assert p.relative_to(tmp_path / "site") == Path("data/latest.json")


def test_latest_json_validates_against_schema(tmp_path, schema):
    payload = json.loads(_build(tmp_path).read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(payload),
                    key=lambda e: list(e.path))
    assert not errors, "latest.json violates hatinring.v1:\n" + "\n".join(
        f"  {list(e.path)}: {e.message}" for e in errors)


def test_envelope_fields(tmp_path):
    payload = json.loads(_build(tmp_path).read_text(encoding="utf-8"))
    assert payload["schema"] == "hatinring.v1"
    assert payload["as_of"] == BUILT.isoformat(), "as_of must be the build date"
    assert {r["id"] for r in payload["candidates"]} == {"alpha", "bravo"}
    assert payload["briefing"]["date"] == BUILT.isoformat()


def test_candidates_are_ranked_by_momentum(tmp_path):
    """Consumers rely on the published order; bravo (declared) outranks alpha."""
    payload = json.loads(_build(tmp_path).read_text(encoding="utf-8"))
    scores = [c["score"] for c in payload["candidates"]]
    assert scores == sorted(scores, reverse=True)
    assert payload["candidates"][0]["id"] == "bravo"


# ---- 2. determinism -------------------------------------------------------
def test_two_builds_are_byte_identical(tmp_path):
    """No timestamps, no set iteration order, no dict-insertion drift.

    The daily Action commits this file; non-determinism would produce a diff
    (and a push) on days when nothing actually changed.
    """
    a = _build(tmp_path, name="a").read_bytes()
    b = _build(tmp_path, name="b").read_bytes()
    assert a == b, "latest.json is not byte-stable across identical builds"


def test_key_order_is_sorted_not_insertion_ordered(tmp_path):
    payload = json.loads(_build(tmp_path).read_text(encoding="utf-8"))
    assert list(payload) == sorted(payload), "envelope keys must be sorted"
    for c in payload["candidates"]:
        assert list(c) == sorted(c), f"{c['id']}: candidate keys must be sorted"


# ---- 3. field allowlist ---------------------------------------------------
def test_only_allowlisted_candidate_fields_are_published(tmp_path):
    payload = json.loads(_build(tmp_path).read_text(encoding="utf-8"))
    allowed = set(buildmod._LATEST_CANDIDATE_FIELDS)
    for c in payload["candidates"]:
        extra = set(c) - allowed
        assert not extra, f"{c['id']}: non-allowlisted field(s) published: {extra}"


def test_internal_fields_and_their_payloads_never_leak(tmp_path):
    """Belt and braces: neither the field names nor the sentinel values appear
    anywhere in the emitted bytes."""
    raw = _build(tmp_path).read_text(encoding="utf-8")
    payload = json.loads(raw)
    for r in payload["candidates"]:
        for f in _SECRET_FIELDS:
            assert f not in r, f"{r['id']}: internal field {f!r} leaked"
    for sentinel in ("HIST_SENTINEL", "FEC_SENTINEL", "EVID_SENTINEL",
                     "INTERNAL_SENTINEL", "RID_SENTINEL"):
        assert sentinel not in raw, f"{sentinel} leaked into latest.json"


def test_allowlist_is_a_closed_set_against_the_schema(tmp_path, schema):
    """The schema and the emitter must not drift: every allowlisted field has a
    schema property, and the schema forbids anything else."""
    props = set(schema["$defs"]["candidate"]["properties"])
    allow = set(buildmod._LATEST_CANDIDATE_FIELDS)
    assert allow == props, (
        "emitter allowlist and schema disagree; "
        f"emitter-only={allow - props}, schema-only={props - allow}")
    assert schema["$defs"]["candidate"]["additionalProperties"] is False
    assert schema["additionalProperties"] is False


# ---- money stays a separate axis -----------------------------------------
def test_money_is_published_as_its_own_block_not_folded_into_candidates(tmp_path):
    """Guardrail 4: money is a separate axis. It must appear under `financials`,
    keyed by id — never as a scoring input, and never duplicated per candidate."""
    recs = _dataset()
    src = tmp_path / "c.json"
    src.write_text(json.dumps(recs), encoding="utf-8")
    fin = {"alpha": {"receipts": 1234, "cash_on_hand": 99, "cycle": 2028}}
    (tmp_path / "financials.json").write_text(json.dumps(fin), encoding="utf-8")

    out_dir = tmp_path / "site-money"
    render(src, TEMPLATES, out_dir / "index.html", built=BUILT)
    payload = json.loads((out_dir / "data" / "latest.json").read_text(encoding="utf-8"))

    assert payload["financials"] == fin, "financials block not published from the artifact"
    for c in payload["candidates"]:
        assert "money" not in c, "money duplicated onto the candidate record"
    # and the momentum score is unaffected by its presence
    no_money_dir = tmp_path / "site-nomoney"
    (tmp_path / "financials.json").unlink()
    render(src, TEMPLATES, no_money_dir / "index.html", built=BUILT)
    bare = json.loads((no_money_dir / "data" / "latest.json").read_text(encoding="utf-8"))
    assert [c["score"] for c in bare["candidates"]] == \
           [c["score"] for c in payload["candidates"]], \
        "momentum changed when financials.json was present — money leaked into scoring"
    assert bare["financials"] == {}
