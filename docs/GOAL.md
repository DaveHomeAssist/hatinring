# North-star goal + standards for hatinring.com

> Read this before any work on this repo. It is the standing brief: the mission,
> the bar, the guardrails, and the roadmap. (Persisted from the session goal so it
> travels with every clone.)

## The test that governs every decision

> **Imagine a real presidential candidate — or their campaign manager, or a
> national political reporter — opening this site and reading their own row.**

If something on the page would make that person dismiss it as a hobby project, a
hit piece, or a rumor board, it is a bug. If it would make them trust it, cite
it, and check it daily, it is right. Build for that reader. Everything below
serves that one test.

## Mission

A tracker credible enough that the people it covers, and the people who cover
them, treat it as a reference. Not viral — **referenceable**. The win condition
is a journalist linking to a candidate's hatinring.com page as evidence, and the
candidate's own staff not being able to dispute it.

## Non-negotiable principles

1. **Status is not support.** Never rank by who "should" win or who is popular.
   Two axes only: *status tier* (furthest verifiable step) and *momentum*
   (weighted activity + recency). Repeat this distinction wherever a reader
   could misread a ranking as an endorsement.
2. **Every claim is sourced or it does not ship.** A status or signal with no
   visible, datestamped, clickable source is a defect. "Trust us" is not a source.
3. **Accuracy over speed, always.** A wrong "Declared" badge on a real person is
   a reputational and potentially legal event. When evidence is thin, downgrade
   the tier or route to the review queue — never round up.
4. **Neutral by construction.** No partisan framing, no loaded adjectives, no
   editorializing in `why`/`headline`/`quote`. Same evidentiary standard for
   every party and every name. A reader should not be able to infer the author's
   politics.
5. **No fabricated quotes, ever.** `quote` must be a real, attributable, linked
   statement. Paraphrase is labeled as paraphrase. Satire/parody is tagged and
   never auto-applied to a real person's status.
6. **Defensible, not a rumor board.** Unknown names, denials, and downgrades go
   to the review queue for a human — never straight to the live board.
7. **Money is its own axis.** FEC financials never feed momentum or status.
8. **Static + tokenless.** The site builds to static files on GitHub Pages from
   the in-repo pipeline (GITHUB_TOKEN only, no PATs, no live backend). Don't add
   a server or a cross-repo secret without explicit human sign-off.

## "Primetime ready" — the quality bar

A change is primetime-ready only if all hold:

- **Sourced:** every visible status/signal has a clickable, dated source.
- **Correctable:** a candidate or reporter can find "how to flag an error" in
  under five seconds (corrections path + contact).
- **Explainable:** the momentum number shows its own math; the tiers are defined
  on /about; the two-axis model is stated above the fold.
- **Indexable:** the surface has a real URL, title, meta, canonical, and lands in
  sitemap.xml; it renders meaningfully without JS (noscript/static fallback).
- **Accessible:** keyboard-operable, WCAG AA contrast, text equivalents for any
  visual-only encoding.
- **Neutral + accurate:** re-read it as the person it describes. Would they call
  it fair? Would they call it correct?
- **Green:** `pytest -q` passes (incl. scoring parity, XSS/escape, schema, render
  smoke), and the build is byte-stable except the timestamp.

## How to proceed in a session

1. **Sync** a clean clone of `DaveHomeAssist/hatinring` and read [docs/SPEC.md](SPEC.md)
   for the architecture, data model, scoring, and the five guardrails.
2. **Plan** against the roadmap below; pick the highest-impact item.
3. **Build small, test continuously:** edit the pipeline/template, build offline
   (`python -m hatring.pipeline --build --out ../index.html`), `node --check` the
   embedded JS, run `pytest -q`, and verify the rendered output.
4. **Add a test** for any new feature or guardrail — the daily Action gates on the
   suite, and the suite is what lets us trust unattended rebuilds.
5. **Ship race-safe:** rebuild-wins rebase + retry on push (a human and the bot
   both push `main`). Verify live after Pages rebuilds.
6. **Never** un-archive or touch the retired `hat-in-ring` repo; **never** weaken
   neutrality, sourcing, or the review-queue gate to ship faster.

## Roadmap (priority order)

**P0 — credibility surface (the reason a candidate would trust it)**
- [x] **Per-candidate static pages** — `/c/<id>/`: status, dated+sourced evidence
      trail, momentum + math, status history, early-state + money, `Person`
      JSON-LD, in sitemap.xml, linked from the homepage.
- [x] **Tighten tier definitions to evidentiary standards** on /about, in the
      legend, and on each page/drawer.
- [~] **Corrections workflow that's visibly responsive** — unmissable correction
      link per page/drawer; "last reviewed" shown per candidate.

**P1 — distribution + discovery**
- [x] **RSS daily-brief feed** (`/feed.xml`) + a "Subscribe" CTA.
- [ ] **Search Console** verified + sitemap submitted (needs the human's Google
      account; wire the verification meta tag or DNS TXT when provided).
- [ ] **Dated "what moved today" archive pages** — recurring fresh, indexable URLs.

**P2 — polish + trust hardening**
- [ ] Methodology deep-dive: weights, recency decay, confidence gating, worked examples.
- [ ] Provenance per momentum component (which signal added which points).
- [ ] Accessibility audit pass on the radar/scope visualization.
- [ ] Open the dataset (CSV/JSON + data dictionary) for journalists/researchers.

## Hard constraints (don't regress these)

- GitHub Pages can't set custom response headers (CSP/X-Frame-Options); HSTS is on
  via enforced HTTPS. Don't fake header coverage — note the limitation.
- All-inline JS: a strict meta-CSP would break the page. Don't add one without a
  refactor plan.
- Keep the public payload lean: `history`/`fec_ids`/`evidence` stay out of the
  rendered SEED.
- Scoring parity (Python ⇄ template JS) is a hard test invariant — change both
  sides together or not at all.

## Definition of done for "ready for primetime"

Every candidate has a sourced, indexable page; tiers are defined to a standard a
campaign couldn't fairly dispute; corrections are one obvious click; share
previews render real PNGs; the site is in Search Console with the sitemap
submitted; and a neutral reader — including the candidate — would call it fair and
correct. When that's true, it's ready to put in front of the people it tracks.
