"""Phase 3: ingest diversification — feed registry, relevance gate, dedupe.

Google News was a single upstream and a single point of failure, and it never
surfaced the IA/NH/SC/NV outlets that actually cover early-state activity. This
suite pins the three things that make adding those outlets safe:

  1. the config.yaml `feeds:` registry is well-formed and its display names are
     graded by classify.RELIABILITY (an ungraded outlet silently caps at Low);
  2. an outlet's WHOLE news river is relevance-gated before it can reach the
     human review queue;
  3. the same story syndicated to several outlets is counted ONCE — without
     this, adding sources inflates raw signal counts and therefore momentum,
     which is the product's core metric.

Fully offline: fixtures only, no network.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
import yaml

from hatring import classify as clf
from hatring import merge as mergemod
from hatring import news as newsmod
from hatring.merge import Dataset, normalize_title

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
TODAY = date(2026, 6, 12)

WATCHLIST = [
    {"id": "alpha", "name": "Alpha Candidate", "aliases": ["Alpha Candidate", "Alpha"]},
    {"id": "bravo", "name": "Bravo Candidate", "aliases": ["Bravo Candidate", "Bravo"]},
]


@pytest.fixture(scope="module")
def cfg() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def _item(**kw) -> newsmod.NewsItem:
    base = dict(title="", summary="", url="https://example.invalid/x",
                source="Iowa Capital Dispatch", published="2026-06-10",
                query="feed:iowacapital", source_id="iowacapital", scoped=False)
    base.update(kw)
    return newsmod.NewsItem(**base)


# ---- 1. the registry ------------------------------------------------------
def test_registry_is_well_formed(cfg):
    feeds = cfg["feeds"]
    assert len(feeds) >= 5, "the point of this phase is >=5 independent sources"
    ids = [f["id"] for f in feeds]
    assert len(ids) == len(set(ids)), f"duplicate feed id in registry: {ids}"
    for f in feeds:
        assert f["kind"] in {"direct", "gnews_site"}, f"{f['id']}: bad kind"
        assert f.get("name"), f"{f['id']}: missing display name"
        if f["kind"] == "direct":
            assert f.get("url", "").startswith("https://"), f"{f['id']}: bad url"
        else:
            assert f.get("query"), f"{f['id']}: gnews_site needs a query"


def test_registry_covers_every_early_state(cfg):
    """The measurable outcome of this phase: IA/NH/SC/NV each have an outlet."""
    covered = {f["state"] for f in cfg["feeds"] if f.get("state")}
    assert covered == {"IA", "NH", "SC", "NV"}, f"early states not covered: {covered}"


def test_every_registry_outlet_is_graded_for_confidence(cfg):
    """A feed whose display name is absent from RELIABILITY silently caps every
    signal it produces at Low. That is safe but useless — catch it here."""
    ungraded = [f["id"] for f in cfg["feeds"]
                if f["name"] not in newsmod.RELIABILITY]
    assert not ungraded, f"registry outlets missing a RELIABILITY grade: {ungraded}"


def test_state_outlets_are_credible_but_not_wire_grade(cfg):
    """Early-state outlets rank as credible primary reporting (Medium), without
    letting one local story certify a wire-grade (Very high) claim."""
    for f in cfg["feeds"]:
        if f.get("state"):
            grade = newsmod.RELIABILITY[f["name"]]
            assert grade in {"Medium", "High"}, f"{f['id']} graded {grade}"


def test_registry_feeds_are_parsed_without_network(cfg, monkeypatch):
    """fetch_feed maps a parsed feed onto NewsItems with the right stamps."""
    spec = next(f for f in cfg["feeds"] if f["kind"] == "direct")

    class _E(dict):
        def get(self, k, d=None):
            return super().get(k, d)

    parsed = type("F", (), {
        "entries": [_E(title="Alpha weighs a 2028 run", summary="", link="https://o/1")],
        "bozo": 0,
    })()
    monkeypatch.setattr(newsmod.feedparser, "parse", lambda *a, **k: parsed)
    items = newsmod.fetch_feed(spec, limit=10, timeout=5)
    assert len(items) == 1
    it = items[0]
    assert it.source_id == spec["id"], "item not stamped with its source id"
    assert it.source == spec["name"], "direct feed item not attributed to its outlet"
    assert it.scoped is False, "an outlet's full river must be marked unscoped"


def test_a_dead_feed_degrades_the_run_instead_of_failing_it(cfg, monkeypatch):
    def _boom(*a, **k):
        raise OSError("connection reset")
    monkeypatch.setattr(newsmod.feedparser, "parse", _boom)
    spec = next(f for f in cfg["feeds"] if f["kind"] == "direct")
    assert newsmod.fetch_feed(spec) == [], "a dead feed must return [], not raise"


def test_google_news_items_stay_scoped():
    """Regression: Google News items must NOT be relevance-gated — their query
    already constrained the topic."""
    assert newsmod.NewsItem(title="t", summary="", url="u", source="Politico",
                            published="2026-06-10", query="q").scoped is True


# ---- 2. the relevance gate ------------------------------------------------
def test_unscoped_local_news_is_dropped_before_the_review_queue():
    """A county story mentioning "PAC" must not manufacture a discovery item."""
    it = _item(title="Charleston peninsula housing complex wins historic designation",
               summary="Council approved it after debate about the PAC-funded campaign.")
    assert clf.classify_item(it, WATCHLIST) is None


def test_unscoped_item_naming_a_tracked_person_passes_the_gate():
    it = _item(title="Gov. Alpha Candidate to headline Iowa Democratic Party fundraiser",
               summary="The governor travels to Des Moines next month.")
    c = clf.classify_item(it, WATCHLIST)
    assert c is not None and c.person_id == "alpha"
    assert "earlyState" in c.keys and c.states == ["IA"]


def test_unscoped_item_about_the_race_passes_the_gate_as_discovery():
    it = _item(title="Charlie Delta is weighing a 2028 presidential run, allies say",
               summary="The senator has not ruled it out.")
    c = clf.classify_item(it, WATCHLIST)
    assert c is not None and c.discovery is True, "unknown name should reach review"


def test_the_gate_does_not_apply_to_scoped_google_news_items():
    it = _item(scoped=True, source="Politico", source_id="gnews",
               title="Alpha Candidate is eyeing a run", summary="")
    assert clf.classify_item(it, WATCHLIST) is not None


def test_gate_drops_the_noise_but_keeps_the_signal_in_the_fixture_feed():
    raw = json.loads((FIXTURES / "feed_items.json").read_text(encoding="utf-8"))
    items = [newsmod.NewsItem(**r) for r in raw]
    assert all(i.scoped is False for i in items)
    out = clf.classify_batch(items, WATCHLIST)
    kept = {c.headline for c in out}
    assert any("Iowa Democratic Party fundraiser" in h for h in kept)
    assert not any("water rates" in h for h in kept)
    assert not any("housing complex" in h for h in kept)


# ---- 3. cross-source dedupe ----------------------------------------------
def test_normalize_title_folds_attribution_and_punctuation():
    a = normalize_title("Alpha won't rule out a 2028 run - Politico")
    b = normalize_title("Alpha won’t rule out a 2028 run — The Hill")
    assert a == b == "alpha wont rule out a 2028 run"


def test_normalize_title_keeps_genuinely_different_headlines_apart():
    assert normalize_title("Alpha weighs a 2028 run") != \
           normalize_title("Bravo weighs a 2028 run")
    assert normalize_title("Alpha rules out a 2028 run") != \
           normalize_title("Alpha weighs a 2028 run")


def _records():
    return [
        {"id": "alpha", "name": "Alpha Candidate", "party": "Democrat",
         "role": "Governor", "bucket": "soft", "keys": ["softConsidering"],
         "conf": "Medium", "delta": 0, "lastSignal": "2026-06-01",
         "headline": "h", "why": "w", "quote": "", "tags": []},
    ]


def _classified(url, headline, date_="2026-06-10", keys=("consideringQuote",)):
    return clf.Classified(person_id="alpha", name_guess="Alpha Candidate",
                          keys=list(keys), confidence="High", headline=headline,
                          url=url, source="Politico", date=date_)


def test_same_story_at_three_urls_is_counted_once(tmp_path):
    """The syndication case this phase exists to handle."""
    audit = tmp_path / "signals.jsonl"
    headline = "Alpha Candidate is seriously considering a 2028 run"
    batch = [
        _classified("https://politico.com/a", headline + " - Politico"),
        _classified("https://thehill.com/b", headline + " - The Hill"),
        _classified("https://apnews.com/c", headline + " — AP News"),
    ]
    ds = Dataset(_records(), today=TODAY).update(batch, [], audit)

    rows = [json.loads(l) for l in audit.read_text().splitlines() if l.strip()]
    assert len(rows) == 3, "every item must be audited, applied or not"
    applied = [r for r in rows if r["applied"]]
    assert len(applied) == 1, f"story applied {len(applied)} times, expected once"
    dupes = [r for r in rows if r.get("dupe_of") == "cross-source"]
    assert len(dupes) == 2, "suppressions must be recorded, not silent"
    # evidence trail carries the story once, not three times
    assert len(ds.records[0]["evidence"]) == 1


def test_distinct_stories_about_the_same_person_are_not_merged(tmp_path):
    audit = tmp_path / "signals.jsonl"
    batch = [
        _classified("https://politico.com/a", "Alpha Candidate hires a campaign manager",
                    keys=("staffing",)),
        _classified("https://thehill.com/b", "Alpha Candidate to headline an Iowa dinner",
                    keys=("earlyState",)),
    ]
    Dataset(_records(), today=TODAY).update(batch, [], audit)
    rows = [json.loads(l) for l in audit.read_text().splitlines() if l.strip()]
    assert all(r["applied"] for r in rows), "distinct stories were wrongly deduped"


def test_same_headline_outside_the_72h_window_is_a_new_story(tmp_path):
    audit = tmp_path / "signals.jsonl"
    headline = "Alpha Candidate is seriously considering a 2028 run"
    Dataset(_records(), today=TODAY).update(
        [_classified("https://politico.com/a", headline, "2026-06-01")], [], audit)
    Dataset(_records(), today=TODAY).update(
        [_classified("https://politico.com/z", headline, "2026-06-20")], [], audit)
    rows = [json.loads(l) for l in audit.read_text().splitlines() if l.strip()]
    assert sum(1 for r in rows if r["applied"]) == 2, \
        "a re-reported story 19 days later should count again"


def test_window_boundary_is_inclusive_at_72h():
    dates = ["2026-06-10"]
    assert mergemod._within_window(dates, "2026-06-13") is True    # exactly 72h
    assert mergemod._within_window(dates, "2026-06-14") is False   # 96h
    assert mergemod._within_window(dates, "2026-06-07") is True    # 72h earlier
    assert mergemod._within_window([], "2026-06-10") is False


def test_dedupe_survives_a_legacy_audit_log_without_tsids(tmp_path):
    """Rows written before this feature carry no tsid; they must not crash the
    loader or block new ingest."""
    audit = tmp_path / "signals.jsonl"
    audit.write_text(json.dumps({"sid": "old|k|u", "type": "news", "url": "u",
                                 "person": "alpha", "keys": ["donors"],
                                 "applied": True}) + "\n", encoding="utf-8")
    seen, titles = mergemod._load_audit(audit)
    assert seen == {"old|k|u"} and titles == {}
    Dataset(_records(), today=TODAY).update(
        [_classified("https://politico.com/new", "Alpha Candidate weighs a run")],
        [], audit)
    rows = [json.loads(l) for l in audit.read_text().splitlines() if l.strip()]
    assert any(r.get("applied") and r.get("tsid") for r in rows)


def test_reingesting_an_identical_batch_is_still_idempotent(tmp_path):
    audit = tmp_path / "signals.jsonl"
    batch = [_classified("https://politico.com/a", "Alpha Candidate weighs a run")]
    Dataset(_records(), today=TODAY).update(batch, [], audit)
    ds2 = Dataset(_records(), today=TODAY).update(batch, [], audit)
    rows = [json.loads(l) for l in audit.read_text().splitlines() if l.strip()]
    assert len(rows) == 1, "a re-run must add no audit rows"
    assert not ds2.records[0].get("evidence")


def test_dedupe_cannot_suppress_across_different_people(tmp_path):
    """The key is person-scoped: two people in one headline template must not
    collapse into one signal."""
    audit = tmp_path / "signals.jsonl"
    recs = _records() + [dict(_records()[0], id="bravo", name="Bravo Candidate")]
    a = _classified("https://x/a", "Candidate is seriously considering a 2028 run")
    b = clf.Classified(person_id="bravo", name_guess="Bravo Candidate",
                       keys=["consideringQuote"], confidence="High",
                       headline="Candidate is seriously considering a 2028 run",
                       url="https://x/b", source="Politico", date="2026-06-10")
    Dataset(recs, today=TODAY).update([a, b], [], audit)
    rows = [json.loads(l) for l in audit.read_text().splitlines() if l.strip()]
    assert sum(1 for r in rows if r["applied"]) == 2
