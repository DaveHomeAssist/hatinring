"""Race timeline artifact (Phase 6).

Two sources feed it, and the distinction is the point: `history` entries are
authoritative and carry the headline that caused a tier move; snapshot-derived
entries are RECONSTRUCTED and carry none. Conflating them would imply an
evidence trail that does not exist.

Offline and deterministic — inline records, pinned dates, tmp paths.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from hatring.timeline import build_timeline, write_timeline

TODAY = date(2026, 6, 15)


def _rec(rid, name="X", party="Democrat", history=None):
    r = {"id": rid, "name": name, "party": party, "keys": ["donors"],
         "lastSignal": "2026-06-01", "bucket": "soft", "role": "r",
         "conf": "Medium", "delta": 0, "headline": "h", "why": "w",
         "quote": "", "tags": []}
    if history is not None:
        r["history"] = history
    return r


def _snaps(tmp_path, rows):
    p = tmp_path / "momentum_snapshots.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p


# ---- recorded history -----------------------------------------------------
def test_history_entries_become_events_with_their_reason():
    recs = [_rec("a", "Alpha", history=[
        {"date": "2026-03-01", "from": 1, "to": 3, "reason": "Alpha says he's in"}])]
    ev = build_timeline(recs)
    assert len(ev) == 1
    e = ev[0]
    assert (e["id"], e["date"], e["from"], e["to"]) == ("a", "2026-03-01", 1, 3)
    assert e["reason"] == "Alpha says he's in"
    assert e["reconstructed"] is False
    assert e["direction"] == "up"
    assert e["fromLabel"] == "Floated" and e["toLabel"] == "Considering"


def test_downgrades_are_marked_as_such():
    recs = [_rec("a", history=[{"date": "2026-03-01", "from": 5, "to": 0,
                                "reason": "ruled out"}])]
    assert build_timeline(recs)[0]["direction"] == "down"


def test_malformed_or_no_op_history_entries_are_skipped():
    recs = [_rec("a", history=[
        {"date": "", "from": 1, "to": 3},                 # no date
        {"date": "2026-03-01", "from": 2, "to": 2},       # not a change
        {"date": "2026-03-02", "to": 3},                  # no from
        {"date": "2026-03-03", "from": None, "to": 3},    # null from
    ])]
    assert build_timeline(recs) == []


def test_records_without_history_contribute_nothing():
    assert build_timeline([_rec("a")]) == []


# ---- reconstruction from the snapshot trail -------------------------------
def test_tier_changes_in_snapshots_are_reconstructed(tmp_path):
    p = _snaps(tmp_path, [
        {"d": "2026-05-01", "id": "a", "s": 20, "t": 2},
        {"d": "2026-05-02", "id": "a", "s": 20, "t": 2},   # no change
        {"d": "2026-05-03", "id": "a", "s": 40, "t": 3},   # change -> event
    ])
    ev = build_timeline([_rec("a", "Alpha")], p)
    assert len(ev) == 1
    assert ev[0]["date"] == "2026-05-03" and ev[0]["from"] == 2 and ev[0]["to"] == 3
    assert ev[0]["reconstructed"] is True
    assert ev[0]["reason"] == "", "a reconstructed event must not invent a reason"


def test_recorded_history_wins_over_reconstruction_on_the_same_day(tmp_path):
    """Both sources see the same move; it must appear once, with its evidence."""
    p = _snaps(tmp_path, [
        {"d": "2026-05-01", "id": "a", "s": 20, "t": 2},
        {"d": "2026-05-03", "id": "a", "s": 40, "t": 3},
    ])
    recs = [_rec("a", "Alpha", history=[
        {"date": "2026-05-03", "from": 2, "to": 3, "reason": "the headline"}])]
    ev = build_timeline(recs, p)
    assert len(ev) == 1, "the same move was recorded twice"
    assert ev[0]["reconstructed"] is False and ev[0]["reason"] == "the headline"


def test_snapshots_for_untracked_records_are_ignored(tmp_path):
    p = _snaps(tmp_path, [
        {"d": "2026-05-01", "id": "ghost", "s": 20, "t": 2},
        {"d": "2026-05-02", "id": "ghost", "s": 40, "t": 4},
    ])
    assert build_timeline([_rec("a")], p) == []


def test_first_snapshot_is_not_an_event(tmp_path):
    """A candidate appearing in the trail has not "moved" to its first tier."""
    p = _snaps(tmp_path, [{"d": "2026-05-01", "id": "a", "s": 20, "t": 2}])
    assert build_timeline([_rec("a")], p) == []


def test_missing_snapshot_file_is_not_an_error(tmp_path):
    assert build_timeline([_rec("a")], tmp_path / "nope.jsonl") == []


# ---- ordering + artifact --------------------------------------------------
def test_events_are_ordered_oldest_first_and_deterministic(tmp_path):
    recs = [
        _rec("b", "Bravo", history=[{"date": "2026-03-01", "from": 1, "to": 2, "reason": ""}]),
        _rec("a", "Alpha", history=[{"date": "2026-03-01", "from": 2, "to": 3, "reason": ""},
                                    {"date": "2026-01-05", "from": 0, "to": 2, "reason": ""}]),
    ]
    ev = build_timeline(recs)
    assert [(e["date"], e["id"]) for e in ev] == [
        ("2026-01-05", "a"), ("2026-03-01", "a"), ("2026-03-01", "b")]
    # same inputs in a different order -> identical output
    assert build_timeline(list(reversed(recs))) == ev


def test_write_timeline_is_byte_stable(tmp_path):
    recs = [_rec("a", history=[{"date": "2026-03-01", "from": 1, "to": 3, "reason": "r"}])]
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(); b.mkdir()
    write_timeline(build_timeline(recs), a)
    write_timeline(build_timeline(recs), b)
    assert (a / "timeline.json").read_bytes() == (b / "timeline.json").read_bytes()


def test_written_artifact_round_trips(tmp_path):
    recs = [_rec("a", "Alpha", history=[
        {"date": "2026-03-01", "from": 1, "to": 3, "reason": "r"}])]
    ev = build_timeline(recs)
    p = write_timeline(ev, tmp_path)
    assert json.loads(p.read_text(encoding="utf-8")) == ev
