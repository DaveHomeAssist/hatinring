"""Unknown/extra curated fields (e.g. links.wikipedia) survive the daily merge.

The daily job (pipeline.run) loads data/candidates.json, mutates the records
in place via merge.Dataset.update / apply_review_item, then rewrites the file
with json.dumps(ds.records) (pipeline.py). Nothing may drop fields automation
doesn't know about — the sameAs enrichment (`links`) rides on exactly that
guarantee. All offline and date-pinned; no network.
"""
from __future__ import annotations
import copy
import json
from datetime import date

from hatring.merge import Dataset
from hatring.classify import Classified
from hatring.fec import FecSignal

TODAY = date(2026, 6, 12)

LINKS = {"wikipedia": "https://en.wikipedia.org/wiki/Ruben_Gallego"}


def base():
    return [
        {"id": "gallego", "name": "Ruben Gallego", "party": "Democrat",
         "role": "Senator", "bucket": "considering", "keys": ["softConsidering"],
         "conf": "Medium", "delta": 0, "lastSignal": "2026-04-06",
         "headline": "old", "why": "w", "quote": "", "tags": [],
         "links": copy.deepcopy(LINKS)},
    ]


def news(pid, keys, headline, date_="2026-06-10"):
    return Classified(person_id=pid, name_guess=pid, keys=keys, confidence="High",
                      headline=headline, url="http://x/" + headline, source="AP News",
                      date=date_, discovery=False)


def test_links_survive_news_merge_and_rewrite(tmp_path):
    ds = Dataset(base(), today=TODAY)
    ds.update([news("gallego", ["consideringQuote"], "Gallego now considering")],
              [], tmp_path / "sig.jsonl")
    rec = ds.by_id["gallego"]
    assert "consideringQuote" in rec["keys"]          # merge did apply the signal
    assert rec["links"] == LINKS                       # extra field untouched
    # ...and survives the pipeline's write-back serialization (pipeline.py writes
    # json.dumps(ds.records, indent=2, ensure_ascii=False) over candidates.json).
    rewritten = json.loads(json.dumps(ds.records, indent=2, ensure_ascii=False))
    assert rewritten[0]["links"] == LINKS


def test_links_survive_fec_merge(tmp_path):
    records = base()
    records[0]["fec_ids"] = ["P80000001"]
    ds = Dataset(records, today=TODAY)
    sig = FecSignal(fec_id="P80000001", name="GALLEGO, RUBEN", party="Democrat",
                    key="declared", confidence="Very high",
                    headline="Filed FEC Statement of Candidacy (Form 2)",
                    filing_date="2026-06-05", committee_id="C001")
    ds.update([], [sig], tmp_path / "sig.jsonl")
    rec = ds.by_id["gallego"]
    assert "declared" in rec["keys"]
    assert rec["links"] == LINKS


def test_links_survive_confirmed_review_item():
    ds = Dataset(base(), today=TODAY)
    changed = ds.apply_review_item({"name": "Ruben Gallego",
                                    "keys": ["consideringQuote"],
                                    "date": "2026-06-11",
                                    "headline": "confirmed by a human"})
    assert changed is True
    assert ds.by_id["gallego"]["links"] == LINKS
