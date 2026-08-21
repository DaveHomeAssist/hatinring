"""Race timeline — every recorded tier change, as one dated event stream.

The board shows where the field stands today; this is how it got there. Two
sources, in priority order:

  1. **Recorded history.** `merge.py` appends a `{date, from, to, reason}` entry
     to a record's `history` whenever its tier moves. These are authoritative
     and carry the headline that caused the move.

  2. **Reconstructed history.** `momentum_snapshots.jsonl` stores a tier (`t`)
     per candidate per day, so a change in `t` between consecutive snapshots is
     a tier move that predates (or was never captured by) the history trail.
     These are marked `reconstructed: true` and carry no reason, so the UI can
     render them distinctly rather than implying an evidence trail that does not
     exist.

Pure and deterministic: same inputs -> same ordered list, so the artifact is
byte-stable and the daily commit is empty when nothing moved.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path

from .scoring import TIERS
from .series import load_snapshots

log = logging.getLogger("hatring.timeline")


def _event(rec: dict, date_: str, frm: int, to: int, reason: str,
           reconstructed: bool) -> dict:
    return {
        "id": rec["id"],
        "name": rec.get("name", rec["id"]),
        "party": rec.get("party", "Independent"),
        "date": date_,
        "from": frm,
        "to": to,
        "fromLabel": TIERS.get(frm, str(frm)),
        "toLabel": TIERS.get(to, str(to)),
        "direction": "up" if to > frm else "down",
        "reason": reason,
        "reconstructed": reconstructed,
    }


def _recorded(records: list[dict]) -> tuple[list[dict], set[tuple[str, str]]]:
    """Events from each record's authoritative status history."""
    out: list[dict] = []
    claimed: set[tuple[str, str]] = set()
    for r in records:
        for h in (r.get("history") or []):
            d = (h.get("date") or "")[:10]
            frm, to = h.get("from"), h.get("to")
            if not d or not isinstance(frm, int) or not isinstance(to, int) or frm == to:
                continue
            claimed.add((r["id"], d))
            out.append(_event(r, d, frm, to, (h.get("reason") or "").strip(), False))
    return out, claimed


def _reconstructed(records: list[dict], snapshots_path: Path,
                   claimed: set[tuple[str, str]]) -> list[dict]:
    """Tier moves visible in the daily snapshot trail but absent from history."""
    if not snapshots_path or not Path(snapshots_path).exists():
        return []
    by_id = {r["id"]: r for r in records}
    out: list[dict] = []
    for cid, points in load_snapshots(Path(snapshots_path)).items():
        rec = by_id.get(cid)
        if rec is None:
            continue                      # snapshot for a record no longer tracked
        prev = None
        for p in sorted(points, key=lambda x: x["d"]):
            tier = p.get("t")
            if not isinstance(tier, int):
                continue
            if prev is not None and tier != prev and (cid, p["d"]) not in claimed:
                out.append(_event(rec, p["d"], prev, tier, "", True))
            prev = tier
    return out


def build_timeline(records: list[dict], snapshots_path: Path | None = None) -> list[dict]:
    """All tier-change events, oldest first. Deterministic ordering."""
    recorded, claimed = _recorded(records)
    events = recorded + _reconstructed(records, snapshots_path, claimed)
    # Total order: date, then id, then target tier — never insertion order, so
    # the artifact is byte-stable across runs and processes.
    events.sort(key=lambda e: (e["date"], e["id"], e["to"]))
    log.info("timeline: %d events (%d recorded, %d reconstructed)",
             len(events), len(recorded), len(events) - len(recorded))
    return events


def write_timeline(events: list[dict], data_dir: Path) -> Path:
    p = Path(data_dir) / "timeline.json"
    p.write_text(json.dumps(events, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return p
