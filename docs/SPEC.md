# Hat-in-Ring Radar — Technical Spec (internal / maintainer)

> Architecture, data model, scoring, pipeline, guardrails, and CI for the
> dashboard at **hatinring.com**. For end-user help see [GUIDE.md](GUIDE.md).

## Purpose
A 2028 U.S. presidential **campaign-signal tracker**. Grades ~40 potential
candidates on two independent axes — **status tier** (furthest verifiable step)
and **momentum** (weighted activity + recency) — rebuilt daily from FEC filings
and news. Thesis: a *defensible, sourced* signal board, not a rumor list.
**Status ≠ support.**

## Architecture
- **Fully static, no live backend.** A Python pipeline bakes everything into a
  single self-contained `index.html` (inline `SEED` JSON), served by **GitHub
  Pages** at `hatinring.com` (apex, free auto-SSL, HTTPS enforced).
- **Repo:** `DaveHomeAssist/hatinring` (public). Pipeline source in
  `_hat-in-ring-src/`; the built dashboard is the repo-root `index.html`;
  `CNAME=hatinring.com`; `favicon.svg`; daily workflow under `.github/workflows/`.
- **Hosting / redirects:** `hatinring.com` is canonical. `systembydave.com/hat-in-ring`
  301-redirects to it; the archived `DaveHomeAssist/hat-in-ring` repo also
  redirects (retired). No cross-repo tokens — the pipeline lives with the site
  (`GITHUB_TOKEN` only).

## Repo layout
```
/                         built site (GitHub Pages root)
  index.html              the dashboard (generated)
  c/<id>/                  per-candidate pages, momentum sparkline + JSON-LD (generated)
  vs/<a>-vs-<b>/           head-to-head compare pages, fixed marquee pairs (generated)
  assets/candidates/...    candidate lead portraits (generated copy)
  assets/share/latest.svg  daily share image (generated)
  share.html               static share card (generated)
  favicon.svg  CNAME  .nojekyll  404.html  robots.txt  sitemap.xml
  docs/                    this documentation
  _hat-in-ring-src/        the pipeline (source of truth; excluded from the
                           deployed Pages artifact)
    hatring/               fec, news, classify, merge, scoring, series,
                           money, geo, brief, build, pages, versus, pipeline
    templates/dashboard.html.j2  candidate.html.j2  vs.html.j2
    data/                  seed.json, candidates.json, signals.jsonl,
                           review_*.json, momentum_snapshots.jsonl,
                           financials.json, briefing.json
    tests/                 180 tests + JS harnesses
    config.yaml  requirements.txt  run.sh
  .github/workflows/hat-in-ring.yml
```

## Data model (`_hat-in-ring-src/data/`)
| File | Role |
| --- | --- |
| `seed.json` | hand-curated source of truth (40 candidates) |
| `candidates.json` | live, automation-merged dataset |
| `signals.jsonl` | append-only idempotency audit log (dedup key `person|keys|url`) |
| `review_queue.json` | discoveries + ambiguous denials awaiting a human |
| `review_decisions.json` | human confirm/dismiss inbox (consumed each run) |
| `momentum_snapshots.jsonl` | daily momentum snapshots (trajectory; pruned to 180d) |
| `financials.json` | FEC money totals, keyed by candidate id |
| `briefing.json` | daily "what moved" summary |

**Record:** `id, name, party, role, bucket, keys[], conf, delta, lastSignal,
headline, why, quote, tags[]` (+ optional `pollLead, fec_ids, history,
early_states, img, links` — `links.wikipedia` is a verified same-entity URL,
surfaced as Person `sameAs` JSON-LD and a visible link on candidate pages).
**Derived at build, not persisted:** `series, slope7, slope30, money`.
`history` and `fec_ids` are dropped from the public payload.

## Scoring model (two axes — `scoring.py` ⇄ mirrored in template JS)
- **Status tier** (categorical, highest declarative signal wins, *no stacking*):
  Declared 5 · Exploratory 4 · Considering 3 · Positioning 2 · Floated 1 ·
  Inactive/Ineligible 0.
- **Momentum** (0–100, capped): `declared +40, exploratory +30,
  consideringQuote +20, softConsidering +12, earlyState +10, donors +10,
  staffing +10, mediaBlitz +5`; penalties `endorsedOther −20, ruledOut −40,
  barred −100`; continuous recency `+5 (≤30d) / 0 / −10 (>90d)`.
- **Parity is a hard invariant**, asserted by tests: **Newsom 60, Vance 30,
  Trump 0, Greaney 30**. The Python engine and the embedded JS engine must agree.

## Pipeline (`_hat-in-ring-src/hatring/`)
```
FEC + News ─▶ classify ─▶ merge ─▶ (series / money / geo / brief) ─▶ build ─▶ index.html
```
- **`fec.py`** — OpenFEC: F2 / principal committee → `declared`, registered →
  `exploratory`; 429 back-off; `candidate_totals()` for money.
- **`news.py`** — two source kinds. Google News RSS (per-person + broad
  discovery queries, `scoped=True`), plus the `config.yaml` **`feeds:` registry**
  of direct outlet feeds — The Hill, Politico, and the IA/NH/SC/NV state outlets
  (`scoped=False`). Outlets with no usable public RSS (AP, Reuters, C-SPAN, Des
  Moines Register) are covered by `kind: gnews_site` site-scoped queries. Every
  item is stamped with its `source_id`; each feed is bounded by a timeout and
  swallows its own failures, so one dead outlet degrades the ingest instead of
  failing the run. Availability audit: `docs/decisions/2026-08-ingest-feeds.md`.
- **`classify.py`** — deterministic regex → signal keys; person-match with a
  surname-collision guard; confidence gated by source × signal strength;
  satire → Noise/review; hedged "considering" demoted to soft; **early-state
  IA/NH/SC/NV tagging**; **cycle-relevance gate** (`RACE_RX`) — an unscoped item
  from an outlet's full river must name a tracked person or visibly concern the
  presidential race before it can reach the review queue.
- **`merge.py`** — idempotent apply (dedup via `signals.jsonl`, keyed
  `person|keys|url`, plus a **cross-source key** `person|keys|normalized-title`
  inside a 72h window so one syndicated story is counted once — more raw signals
  would otherwise mean more momentum); status-history
  on tier change; 7-day delta from momentum snapshots; **denials/downgrades
  routed to review (never auto-applied)**; unknown FEC filers gated on a
  registered principal committee; early-state tallies.
- **`scoring.py` / `series.py`** — momentum + daily snapshots → `series`,
  `slope7`, `slope30`. Pruning at `RETAIN_DAYS` (180) **moves** rows to
  `data/archive/momentum_<year>.jsonl.gz` rather than deleting them, so the
  cycle ends with a complete trail; the archive is idempotent on `(date, id)`
  and gzipped with `mtime=0` so unchanged content makes no commit.
- **`timeline.py`** — `data/timeline.json`: every status-tier change, oldest
  first. Recorded `history` entries are authoritative and carry their headline;
  moves visible only in the snapshot tier trail are emitted with
  `reconstructed: true` and no reason, so the UI never implies evidence that
  does not exist.
- **`money.py`** — financials artifact; a **separate axis, never scored**.
- **`geo.py`** — early-state codes + headline backfill.
- **`brief.py`** — `briefing.json` + SVG/HTML share card.
- **`build.py`** — Jinja render; inject `SEED`/`REVIEW`/`BRIEFING`; attach
  images/series/money; SEO/OG/JSON-LD; static crawl summary; share assets;
  `emit_latest_json()` writes the public `data/latest.json` contract.
- **`pipeline.py`** — orchestrator; `reconcile_review` persists the queue and
  applies human decisions.
- **`review.html`** — local review-queue admin page (vanilla, single file, no
  build). Served from `_hat-in-ring-src/` via `python -m http.server`, it turns
  the queue into cards and exports a schema-valid `review_decisions.json`,
  replacing the hand edit that `_safe_load`'s fail-safe exists to survive. The
  export is validated before the download is enabled, and a queue carrying an
  unrecognised field is REFUSED rather than mis-rendered. `_hat-in-ring-src/` is
  excluded from the Pages artifact, so the page is never published — asserted in
  `tests/test_review_admin.py` against the deploy workflow itself.

## Public data contract (`/data/latest.json`)
Published on every daily build so consumers — the iOS app, embeds, and estate
tooling (command-center, graph-explorer) — read a stable artifact instead of
scraping `index.html`.

- **URL:** `https://hatinring.com/data/latest.json` · **schema:** `hatinring.v1`
- **Emitted by:** `build.emit_latest_json()`, staged next to `index.html` (the
  Pages artifact excludes `_hat-in-ring-src/`, so the pipeline's own `data/`
  copy is not the served one).
- **Envelope:** `{schema, as_of, candidates[], briefing{}, financials{}, timeline[]}`.
  `candidates` is ranked by momentum, descending. `financials` is keyed by
  candidate id — an absent id means *has not filed*, which is not zero, and it
  is never folded into momentum (guardrail 4).
- **Field allowlist:** `build._LATEST_CANDIDATE_FIELDS`. An allowlist, not a
  denylist: a curated / internal / review-queue field added to a record later is
  excluded by default rather than silently published.
- **Deterministic:** sorted keys, no timestamps — identical inputs produce
  byte-identical bytes, so a no-change day produces no commit.
- **Caching:** GitHub Pages may serve a stale copy; consumers must honour
  `as_of` rather than trusting freshness of the response.
- **Change policy:** additive only. New optional fields may be added to
  `hatinring.v1` at any time; consumers must ignore unknown fields. A breaking
  change (removing or retyping a field) ships as `hatinring.v2` at a new path,
  with `v1` maintained for at least 60 days.
- **Schema + tests:** `_hat-in-ring-src/schemas/latest.v1.schema.json`, enforced
  by `tests/test_latest_json_contract.py` (schema validity, determinism,
  allowlist closure against the schema, and internal-field leak sentinels).

## Guardrails (canonical — do not regress)
1. Unknown names → `review_queue.json`, never the live board.
2. Denials / downgrades **never auto-apply** (human-confirmed only).
3. Only FEC filers with a **registered principal committee** surface.
4. **Money is never folded into momentum.**
5. Automation never overwrites curated fields (`why, role, bucket, quotes`);
   manual edits survive rebuilds.

## Frontend
Current frontend ships as a single-file Jinja template with browser-loaded JS.
Framework code or package-managed architecture can be used when the product calls
for it. `SEED` + `REVIEW`
+ `BRIEFING` injected as JS literals (`<` escaped to `<` to prevent a
`</script>` breakout; every data field HTML-escaped). Four views — The Field, Dossiers, The Wire, and **Timeline**
(`#/timeline`), the last rendering every recorded tier change on a horizontal
track plus a keyboard-operable list of `<button>` rows. State in `localStorage`,
version-keyed: a new pipeline build refreshes the seed but preserves manual adds
+ view prefs. SVG sparklines / favicon / share. SEO: canonical = `hatinring.com`,
OG/Twitter/JSON-LD, `<noscript>` top-15 table. A11y: ARIA tablist/roles, keyboard
activation, focus-visible, reduced-motion, sparkline text equivalents. A canvas
"Live Scope" radar (centre = momentum, angle = party, size = confidence,
★ = poll leader).

## CI/CD & testing
- **Daily Action** (`cron 0 11 * * *` + `workflow_dispatch`): ingest → **180-test
  gate** → build into `index.html` → race-safe commit/push → Pages deploy via
  `deploy-pages.yml` (Actions artifact, `workflow_run`-chained; excludes
  `_hat-in-ring-src/` so the pipeline source is not publicly served; also fires
  on direct human pushes to main). `FEC_API_KEY` is a **per-repo secret** with
  `DEMO_KEY` fallback. The commit step rebases + retries (this repo can be
  pushed to by a human too).
- **Tests (180 + 3 xfail):** scoring parity & fuzz; build integrity (incl.
  `node --check`, drop-field leak, SEO); headless render smoke; anticipatory-UX
  check; XSS render/security; schema validation; classify battery; merge
  guardrails; series / geo / brief / money units.

## Local dev
```bash
cd _hat-in-ring-src
pip install -r requirements.txt
python -m hatring.pipeline --offline --fixtures tests/fixtures --build --out ../index.html  # no network
python -m hatring.pipeline --all --out ../index.html                                        # live ingest + build
pytest -q
```

## Known limitations
- Classification is **headline-only** (RSS / paywalls).
- **Money is sparse until 2028 committees file** (mid-2026: ~0 filers; "not
  filed" everywhere — by design, never zero).
- Momentum **sparklines flatten** until daily snapshots accumulate (one/day).
- The review-decision loop is manual (export `review_decisions.json`, commit,
  applied on the next build).
- LLM adjudication is a documented opt-in stub (`classify_llm`).

_Last updated: 2026-06-16._
