# Hat-in-Ring Radar

**2028 U.S. presidential signal tracker — live at [hatinring.com](https://hatinring.com).**

Grades ~40 potential candidates on two independent axes — **status tier** (the
furthest verifiable step taken) and **momentum** (weighted activity + recency,
0–100) — rebuilt daily from FEC filings and news. *Status is not support.*

A fully static GitHub Pages site: a Python pipeline ([`_hat-in-ring-src/`](_hat-in-ring-src/))
ingests FEC + news, scores, and bakes a single self-contained `index.html`. No
live backend. A daily GitHub Action runs ingest → tests → build → deploy.

## Documentation
- [docs/OVERVIEW.md](docs/OVERVIEW.md) — what it is (and why it's different)
- [docs/GUIDE.md](docs/GUIDE.md) — how to read and use the dashboard
- [docs/SPEC.md](docs/SPEC.md) — architecture, data model, scoring, pipeline, CI

Signals are drawn from public reporting (AP, Reuters, Time, WaPo, ABC, C-SPAN, FEC).
