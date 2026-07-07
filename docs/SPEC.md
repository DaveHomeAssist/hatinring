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
- **`news.py`** — Google News RSS; per-person + broad discovery queries.
- **`classify.py`** — deterministic regex → signal keys; person-match with a
  surname-collision guard; confidence gated by source × signal strength;
  satire → Noise/review; hedged "considering" demoted to soft; **early-state
  IA/NH/SC/NV tagging**.
- **`merge.py`** — idempotent apply (dedup via `signals.jsonl`); status-history
  on tier change; 7-day delta from momentum snapshots; **denials/downgrades
  routed to review (never auto-applied)**; unknown FEC filers gated on a
  registered principal committee; early-state tallies.
- **`scoring.py` / `series.py`** — momentum + daily snapshots → `series`,
  `slope7`, `slope30`.
- **`money.py`** — financials artifact; a **separate axis, never scored**.
- **`geo.py`** — early-state codes + headline backfill.
- **`brief.py`** — `briefing.json` + SVG/HTML share card.
- **`build.py`** — Jinja render; inject `SEED`/`REVIEW`/`BRIEFING`; attach
  images/series/money; SEO/OG/JSON-LD; static crawl summary; share assets.
- **`pipeline.py`** — orchestrator; `reconcile_review` persists the queue and
  applies human decisions.

## Guardrails (canonical — do not regress)
1. Unknown names → `review_queue.json`, never the live board.
2. Denials / downgrades **never auto-apply** (human-confirmed only).
3. Only FEC filers with a **registered principal committee** surface.
4. **Money is never folded into momentum.**
5. Automation never overwrites curated fields (`why, role, bucket, quotes`);
   manual edits survive rebuilds.

## Frontend
Current frontend ships as a single-file Jinja template with browser-loaded JS.
That shape is not a rule against framework code or package-managed architecture
if the product needs it. `SEED` + `REVIEW`
+ `BRIEFING` injected as JS literals (`<` escaped to `<` to prevent a
`</script>` breakout; every data field HTML-escaped). State in `localStorage`,
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
