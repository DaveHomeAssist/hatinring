# Prompt: Initialize the Hat-in-Ring Radar changelog

Use this prompt in a fresh repository task when Hat-in-Ring Radar is ready to adopt a project changelog.

```text
Create an evidence-based `CHANGELOG.md` for Hat-in-Ring Radar.

Read first:
1. Root `README.md`, `_hat-in-ring-src/README.md`, and `docs/SPEC.md`.
2. The daily ingest and Pages workflows.
3. `git log --date=short --pretty=format:'%h %ad %s'`, relevant diffs, and the test suite.

Rules:
- Use dated sections, newest first. Use commit dates and do not invent versions when there are no matching tags.
- Summarize routine daily-ingest commits by cadence or material data change rather than adding one line per run.
- Begin with a `2026-08-10` section covering data-trust guardrails, stable no-op reruns, protection for curated headlines and quotes, FEC downgrade review gating, URL sanitization, workflow pinning and conflict safety, metadata/CSP coverage, mobile statistics rail, contrast and reduced motion, and build-time portrait optimization.
- State that status tier measures verifiable campaign steps and momentum measures activity; neither is an endorsement or polling result.
- Keep source-pipeline changes separate from generated candidate, comparison, and share pages.
- Do not treat daily data refreshes as feature releases unless behavior or methodology changed.
- Record only changes present on `origin/main` and supported by source, tests, or deployment evidence.

Verification:
- Run the full `_hat-in-ring-src` pytest suite.
- Rebuild the dashboard and run `dashboard_smoke.js` and `ux_check.js`.
- Confirm generated portrait bounds and total output size.
- Run `git diff --check` and confirm referenced commits are ancestors of `origin/main`.
```
