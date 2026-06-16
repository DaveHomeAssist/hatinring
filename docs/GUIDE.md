# Hat-in-Ring Radar — User Guide

How to read and use the dashboard at **[hatinring.com](https://hatinring.com)**.

## What you're looking at
Every candidate is graded on **two separate things**:

- **Status tier** — the *furthest verifiable step* they've taken: **Declared → Exploratory → Considering → Positioning → Floated → Inactive**.
- **Momentum (0–100)** — *how much they're doing right now*, weighted by activity and cooled over time.

They move independently. A poll-leader who keeps saying "no plans" can sit at **Positioning** with mid momentum — that's the point.

## Getting around (the view tabs)
- **Leaderboard** — ranked table. Click any column header to sort (Momentum, Status, 7-day, Confidence). The **Trend** column shows a momentum sparkline.
- **Cards** — the same data as tiles, with sparkline + status flags.
- **Trajectory** — ranked by who's **heating up** (toggle 7-day / 30-day momentum change).
- **Early States** — Iowa / New Hampshire / South Carolina / Nevada activity by heat. **Click a state** to filter the board to who's active there.
- **Compare** — pick **2–3 candidates** and see them side by side.
- **Review** — discoveries and ambiguous items the pipeline wouldn't auto-trust (see below).
- **Live Scope** (the radar up top) — each blip is a candidate: **center = high momentum**, **angle = party lane**, **dot size = confidence**, **★ = poll leader**. Switch Command / Briefing layout with the view buttons, or open tweaks for the sweep.

## Filtering & finding
- **Search** by name or role.
- **Party / Bucket / Confidence** dropdowns.
- **Quick chips:** *Movers* (changed this week), *Declared*, *My adds*.

## Reading a candidate (click any row or card)
The detail drawer shows:

- Latest signal, why it matters, and how long ago it was.
- **"Why this momentum score?"** — the exact math (e.g. `+20 considering quote, +10 donors, −10 stale`). No black box.
- **Trajectory** — sparkline + 7/30-day change + a status-tier timeline.
- **Early-state activity** and **Money movement** (FEC receipts / cash-on-hand; shows *"not filed"* if they haven't registered a committee).
- **＋ Compare** to add them to a head-to-head.

## Compare & share
Tick **compare** on cards (or **＋ Compare** in the drawer), up to 3, then open the **Compare** tab. The URL updates to a shareable deep link, e.g. `hatinring.com/#compare=newsom,shapiro`.

## Badges & colors
- **Heating ▲ / Cooling ▼** — momentum vs. last week. **Stale** — no signal in 90+ days. **Verified** — high-confidence sourcing. **★** — leads primary polling.
- A colored dot/bar marks the party lane; the momentum score is color-coded by status tier.

## The Review Queue (why some things don't just appear)
Unknown names, parody, and **denials** ("won't run") are *never* auto-applied — they land in **Review**, where you **Confirm** or **Dismiss** each. Decisions save in your browser; click **Export decisions** and commit `review_decisions.json` to apply them in the next daily rebuild.

## Add / edit / export
- **+ Add** or **Edit** a candidate — tick the signals present and watch the **live status / momentum** update. Saves to **your browser only** (find them under the *My adds* chip).
- **Export** downloads the full dataset as JSON to back up or port elsewhere.

## Good to know
- Data refreshes **daily**; the "As of" date and build time are in the header.
- Your edits are **device-local** — they don't change what anyone else sees.
- It's a **manually-defensible tracker**, not a live feed: signals come from public reporting (AP, Reuters, FEC, and similar).

_Last updated: 2026-06-16._
