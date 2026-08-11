# Hat-in-Ring Radar strengthens source trust, mobile access, and image delivery

**Draft press release. Not yet distributed.**

**FOR IMMEDIATE RELEASE**

## Hat-in-Ring Radar strengthens source trust, mobile access, and image delivery

### The 2028 presidential signal tracker adds stricter human-review guardrails, stable reruns, safer source links, and a 72 percent reduction in candidate portrait weight

August 10, 2026

Hat-in-Ring Radar today released a trust, accessibility, and performance update for its source-linked 2028 presidential campaign-signal tracker. The release tightens the boundary between automated evidence collection and human-curated editorial fields while making the dashboard faster and easier to scan on mobile devices.

Hat-in-Ring Radar tracks verifiable campaign steps and activity. Its status tiers are not endorsements, polling results, or predictions of electoral support.

## What changed

- Preserved the last known momentum delta when a repeated ingest contains no new signal.
- Protected human-curated headlines and quotes from automatic replacement.
- Routed unexpected Federal Election Commission downgrade signals to human review instead of silently changing a candidate's tier.
- Kept newer automated source material in a dated evidence trail.
- Rejected non-web source URLs before rendering candidate, evidence, money, and profile links.
- Replaced silent conflict-favoring workflow rebases with explicit failure and retry behavior.
- Pinned workflow dependencies and Python packages to exact releases or immutable commits.
- Added complete social, search, referrer, and content security metadata to generated public pages.
- Added a horizontally scrollable mobile statistics rail, reduced-motion behavior, and higher-contrast helper text.
- Added build-time image resizing and metadata removal for candidate portraits.

## Verification

The release passed all 207 pipeline, trust, security, rendering, and page-generation tests with no expected failures. Dashboard first-visit and interaction smoke checks also passed.

The 40 generated candidate portraits now total approximately 2.57 MB, down from approximately 9.2 MB. A mobile Lighthouse run returned 94 for performance and 100 for accessibility, best practices, and search engine optimization.

## Availability

The updated tracker is live at [hatinring.com](https://hatinring.com/).

## About Hat-in-Ring Radar

Hat-in-Ring Radar is a daily-updated, source-linked tracker of potential 2028 presidential candidates. It separates status tier from momentum, traces material signals to public reporting or Federal Election Commission records, and routes ambiguous discoveries and downgrades to human review.
