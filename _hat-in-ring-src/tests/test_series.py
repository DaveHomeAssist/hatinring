"""Momentum-trajectory tests: snapshot accumulation, series shape + bounding,
slope computation, retention pruning. Deterministic (pinned dates, tmp paths)."""
from __future__ import annotations
import json
from datetime import date, timedelta
from pathlib import Path

from hatring import series

TODAY = date(2026, 6, 15)


def _rec(rid, keys, last, history=None):
    r = {"id": rid, "keys": keys, "lastSignal": last}
    if history:
        r["history"] = history
    return r


def test_record_snapshot_idempotent_per_date(tmp_path):
    p = tmp_path / "snap.jsonl"
    recs = [_rec("a", ["consideringQuote"], "2026-06-10")]
    assert series.record_snapshot(recs, TODAY, p) == 1
    assert series.record_snapshot(recs, TODAY, p) == 0      # same date -> no dup
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) == 1 and rows[0]["id"] == "a" and rows[0]["d"] == TODAY.isoformat()
    assert isinstance(rows[0]["s"], int) and isinstance(rows[0]["t"], int)


def test_attach_series_shape_and_bounded(tmp_path):
    p = tmp_path / "snap.jsonl"
    recs = [_rec("a", ["consideringQuote", "earlyState"], "2026-06-12",
                 history=[{"date": "2026-05-01", "from": 1, "to": 3}])]
    series.attach(recs, TODAY, p)
    s = recs[0]["series"]
    assert isinstance(s, list) and 1 <= len(s) <= series.MAX_POINTS
    for pt in s:
        assert "d" in pt and set(pt) <= {"d", "s", "t"}
    assert isinstance(recs[0]["slope7"], int) and isinstance(recs[0]["slope30"], int)


def test_slope_zero_without_history(tmp_path):
    p = tmp_path / "snap.jsonl"
    recs = [_rec("a", ["donors"], "2026-06-14")]
    series.attach(recs, TODAY, p)
    assert recs[0]["slope7"] == 0 and recs[0]["slope30"] == 0   # single point


def test_slope_positive_when_momentum_rose(tmp_path):
    p = tmp_path / "snap.jsonl"
    p.write_text(json.dumps({"d": "2026-06-01", "id": "a", "s": 10, "t": 2}) + "\n", encoding="utf-8")
    recs = [_rec("a", ["consideringQuote", "earlyState", "donors", "staffing", "mediaBlitz"],
                 "2026-06-14")]
    series.attach(recs, TODAY, p)     # today's point ~60 vs the seeded 10
    assert recs[0]["slope7"] > 0 and recs[0]["slope30"] > 0


def test_no_payload_blowup_downsamples(tmp_path):
    p = tmp_path / "snap.jsonl"
    rows = [json.dumps({"d": (date(2026, 1, 1) + timedelta(days=i)).isoformat(),
                        "id": "a", "s": i % 100, "t": 2}) for i in range(120)]
    p.write_text("\n".join(rows) + "\n", encoding="utf-8")
    recs = [_rec("a", ["donors"], "2026-06-14")]
    series.attach(recs, TODAY, p)
    assert len(recs[0]["series"]) <= series.MAX_POINTS    # bounded regardless of input size


def test_record_snapshot_prunes_old_rows(tmp_path):
    p = tmp_path / "snap.jsonl"
    p.write_text(json.dumps({"d": "2025-01-01", "id": "a", "s": 5, "t": 1}) + "\n", encoding="utf-8")
    recs = [_rec("a", ["donors"], "2026-06-14")]
    series.record_snapshot(recs, TODAY, p)
    cutoff = (TODAY - timedelta(days=series.RETAIN_DAYS)).isoformat()
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert rows and all(r["d"] >= cutoff for r in rows)   # ancient row dropped


# ---------------------------------------------------------------------------
# Full-cycle archive (Phase 6)
#
# Pruning at RETAIN_DAYS used to DELETE rows, discarding the only record of how
# the field moved. It must now MOVE them. The property that matters is zero
# data loss: everything pruned must be recoverable.
# ---------------------------------------------------------------------------
def _old_rows(n, start=date(2025, 1, 1), cid="a"):
    return [{"d": (start + timedelta(days=i)).isoformat(), "id": cid,
             "s": i % 100, "t": i % 6} for i in range(n)]


def test_prune_archives_before_dropping_with_zero_data_loss(tmp_path):
    p = tmp_path / "snap.jsonl"
    old = _old_rows(40)                      # all far older than RETAIN_DAYS
    p.write_text("".join(json.dumps(r) + "\n" for r in old), encoding="utf-8")

    recs = [_rec("a", ["donors"], "2026-06-14")]
    series.record_snapshot(recs, TODAY, p)

    # live file is bounded...
    cutoff = (TODAY - timedelta(days=series.RETAIN_DAYS)).isoformat()
    live = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert all(r["d"] >= cutoff for r in live), "prune did not bound the live file"

    # ...and every pruned row round-trips out of the archive unchanged.
    archived = series.load_archived(tmp_path)
    assert {(r["d"], r["id"]) for r in archived} == {(r["d"], r["id"]) for r in old}
    by_key = {(r["d"], r["id"]): r for r in archived}
    for r in old:
        assert by_key[(r["d"], r["id"])] == r, "archived row differs from the pruned row"


def test_archive_is_idempotent_on_date_and_id(tmp_path):
    rows = _old_rows(5)
    assert series.archive_rows(rows, tmp_path) == 5
    assert series.archive_rows(rows, tmp_path) == 0, "re-archiving duplicated history"
    assert len(series.load_archived(tmp_path)) == 5


def test_archive_is_split_per_year(tmp_path):
    series.archive_rows(_old_rows(3, date(2025, 12, 30)), tmp_path)
    assert series.archive_path(tmp_path, "2025").exists()
    assert series.archive_path(tmp_path, "2026").exists()
    assert len(series.load_archived(tmp_path)) == 3


def test_archive_bytes_are_stable_so_an_unchanged_archive_makes_no_commit(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    rows = _old_rows(6)
    series.archive_rows(rows, a)
    series.archive_rows(list(reversed(rows)), b)   # same rows, different order
    assert series.archive_path(a, "2025").read_bytes() == \
           series.archive_path(b, "2025").read_bytes(), \
        "gzip output is not byte-stable (mtime header or unsorted rows?)"


def test_nothing_is_archived_when_nothing_is_pruned(tmp_path):
    p = tmp_path / "snap.jsonl"
    p.write_text(json.dumps({"d": TODAY.isoformat(), "id": "a", "s": 5, "t": 2}) + "\n",
                 encoding="utf-8")
    series.record_snapshot([_rec("a", ["donors"], "2026-06-14")], TODAY, p)
    assert series.load_archived(tmp_path) == []
    assert not (tmp_path / series.ARCHIVE_DIRNAME).exists()


def test_archive_skips_malformed_rows(tmp_path):
    assert series.archive_rows([{"d": "2025-01-01"}, {"id": "a"}, {}], tmp_path) == 0
