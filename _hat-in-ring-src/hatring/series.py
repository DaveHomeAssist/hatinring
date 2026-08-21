"""Momentum trajectory — accumulate daily snapshots and expose a compact public
`series` per candidate so the dashboard shows a trend, not just a snapshot.

Momentum has no historical record in signals.jsonl (those audit rows carry no
date or score), so we ACCUMULATE forward: one snapshot per candidate per
pipeline run, in data/momentum_snapshots.jsonl. Tier points are additionally
backfilled from each record's status `history` (dated tier transitions). Until
snapshots accumulate, slopes are 0 and the sparkline is the single current
point — a graceful empty state, not an error.

The series is DERIVED and attached at build time; it is never written into
candidates.json (keeps the persisted dataset clean and curated-field-safe).
"""
from __future__ import annotations
import gzip
import json
import logging
from datetime import date, timedelta
from pathlib import Path

from .scoring import momentum as _momentum, derive_status as _status

log = logging.getLogger("hatring.series")

RETAIN_DAYS = 180          # bound the committed snapshot file
MAX_POINTS = 16            # downsample the public series so the payload stays lean
ARCHIVE_DIRNAME = "archive"   # data/archive/momentum_<year>.jsonl.gz


# ---- full-cycle archive ----------------------------------------------------
# Pruning at RETAIN_DAYS used to DELETE the rows, which quietly discarded the
# only record of how the field moved. They are now moved to a per-year gzip
# JSONL first, so the 2028 cycle ends with a complete trail. At ~40 candidates a
# day this is a few KB/day; the whole cycle stays comfortably under ~5 MB.


def archive_path(data_dir: Path, year: str) -> Path:
    return Path(data_dir) / ARCHIVE_DIRNAME / f"momentum_{year}.jsonl.gz"


def _read_gz(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def _write_gz(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # mtime=0 so the gzip header carries no timestamp: identical rows produce
    # identical bytes, and an unchanged archive makes no commit.
    with gzip.GzipFile(filename="", mode="wb", fileobj=path.open("wb"),
                       mtime=0) as gz:
        gz.write("".join(json.dumps(r, sort_keys=True) + "\n"
                         for r in rows).encode("utf-8"))


def archive_rows(rows: list[dict], data_dir: Path) -> int:
    """Append pruned snapshot rows to their per-year archive.

    Idempotent on (date, id): re-archiving a row already present is a no-op, so
    a re-run — or a prune that overlaps a previous one — cannot duplicate
    history. Returns the number of genuinely new rows written.
    """
    by_year: dict[str, list[dict]] = {}
    for r in rows:
        d = str(r.get("d", ""))[:10]
        if len(d) < 4 or not r.get("id"):
            continue
        by_year.setdefault(d[:4], []).append(r)

    written = 0
    for year, fresh in sorted(by_year.items()):
        path = archive_path(data_dir, year)
        existing = _read_gz(path)
        have = {(r.get("d"), r.get("id")) for r in existing}
        added = [r for r in fresh if (r.get("d"), r.get("id")) not in have]
        if not added:
            continue
        merged = existing + added
        # Sorted so the file is stable regardless of the order rows were pruned.
        merged.sort(key=lambda r: (str(r.get("d", "")), str(r.get("id", ""))))
        _write_gz(path, merged)
        written += len(added)
    if written:
        log.info("series: archived %d pruned snapshot rows across %d year file(s)",
                 written, len(by_year))
    return written


def load_archived(data_dir: Path) -> list[dict]:
    """Every archived row, oldest first. Used by the prune round-trip test and
    available for any future full-cycle analysis."""
    d = Path(data_dir) / ARCHIVE_DIRNAME
    if not d.exists():
        return []
    rows: list[dict] = []
    for path in sorted(d.glob("momentum_*.jsonl.gz")):
        rows.extend(_read_gz(path))
    rows.sort(key=lambda r: (str(r.get("d", "")), str(r.get("id", ""))))
    return rows


def _today_point(rec: dict, today: date) -> dict:
    keys = rec.get("keys", [])
    return {"d": today.isoformat(),
            "s": _momentum(keys, rec.get("lastSignal", today.isoformat()), today),
            "t": _status(keys)[0]}


def load_snapshots(path: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        out.setdefault(row["id"], []).append(
            {"d": row["d"], "s": row.get("s"), "t": row.get("t")})
    return out


def record_snapshot(records: list[dict], today: date, path: Path) -> int:
    """Append today's {d,id,s,t} for each record, once per date; prune to
    RETAIN_DAYS so the committed file stays bounded. Returns rows written."""
    existing = load_snapshots(path)
    have_today = {cid for cid, pts in existing.items()
                  if any(p["d"] == today.isoformat() for p in pts)}
    new_rows = [{"d": p["d"], "id": r["id"], "s": p["s"], "t": p["t"]}
                for r in records
                if r["id"] not in have_today
                for p in [_today_point(r, today)]]
    cutoff = (today - timedelta(days=RETAIN_DAYS)).isoformat()
    kept: list[dict] = []
    pruned: list[dict] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            (kept if row.get("d", "") >= cutoff else pruned).append(row)
    # Move before dropping: pruning must bound the live file, not lose history.
    if pruned:
        archive_rows(pruned, path.parent)
    kept.extend(new_rows)
    path.write_text("".join(json.dumps(r) + "\n" for r in kept), encoding="utf-8")
    return len(new_rows)


def _history_points(rec: dict) -> list[dict]:
    pts = []
    for h in rec.get("history", []) or []:
        d = (h.get("date") or "")[:10]
        if d:
            pts.append({"d": d, "s": None, "t": h.get("to")})
    return pts


def _downsample(points: list[dict], n: int = MAX_POINTS) -> list[dict]:
    if len(points) <= n:
        return points
    step = (len(points) - 1) / (n - 1)
    idx = sorted(set([round(i * step) for i in range(n)] + [len(points) - 1]))
    return [points[i] for i in idx]


def _slope(points: list[dict], today: date, days: int) -> int:
    """score(now) − score(nearest scored point ≥ `days` old). 0 if insufficient."""
    scored = [p for p in points if isinstance(p.get("s"), (int, float))]
    if len(scored) < 2:
        return 0
    now = scored[-1]
    cutoff = (today - timedelta(days=days)).isoformat()
    past = [p for p in scored if p["d"] <= cutoff]
    base = past[-1] if past else scored[0]
    return int(now["s"] - base["s"])


def attach(records: list[dict], today: date, path: Path) -> None:
    """Set `series` (compact, downsampled), `slope7`, `slope30` on each record.

    Sources, merged by date (a scored snapshot wins over a tier-only history
    point on the same date): persisted snapshots + status-history tier points +
    a synthesized current point so a sparkline always has the latest value.
    """
    snaps = load_snapshots(path)
    for r in records:
        pts = list(snaps.get(r["id"], [])) + _history_points(r)
        tp = _today_point(r, today)
        if not any(p["d"] == tp["d"] and p.get("s") is not None for p in pts):
            pts.append(tp)
        bydate: dict[str, dict] = {}
        for p in sorted(pts, key=lambda x: (x["d"], x.get("s") is None)):
            cur = bydate.get(p["d"])
            if cur is None or (cur.get("s") is None and p.get("s") is not None):
                bydate[p["d"]] = p
        ordered = [bydate[d] for d in sorted(bydate)]
        r["series"] = _downsample(ordered)
        r["slope7"] = _slope(ordered, today, 7)
        r["slope30"] = _slope(ordered, today, 30)
