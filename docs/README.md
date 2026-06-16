# Hat-in-Ring Radar — Documentation

A 2028 U.S. presidential **campaign-signal tracker**. Live at **[hatinring.com](https://hatinring.com)**.

It grades ~40 potential candidates on two independent axes — **status tier** (the furthest verifiable step a person has taken) and **momentum** (weighted activity + recency, 0–100) — rebuilt daily from FEC filings and news. *Status is not support.*

## Documents

| Doc | For | What's in it |
| --- | --- | --- |
| [OVERVIEW.md](OVERVIEW.md) | Anyone / press | One-paragraph "what this is and why it's different." |
| [GUIDE.md](GUIDE.md) | Users | How to read and use the dashboard. |
| [SPEC.md](SPEC.md) | Maintainers | Architecture, data model, scoring, pipeline, guardrails, CI. |

## At a glance
- **Static, no live backend.** A Python pipeline bakes a single self-contained `index.html` (inline data) served by GitHub Pages at `hatinring.com` (apex, auto-SSL).
- **Daily GitHub Action**: ingest (FEC + news) → 180-test gate → build → commit → deploy.
- **Source:** [`_hat-in-ring-src/`](../_hat-in-ring-src/) (the pipeline); the built dashboard is at the repo root.

_Last updated: 2026-06-16._
