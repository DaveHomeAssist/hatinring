# Hat In Ring iOS Current Status Roadmap

Date: 2026-06-25
Last verified: 2026-06-25 ET
Target: `/Users/daverobertson/Desktop/Code/10-projects/active/hat-in-ring`
iOS surface: `ios/HatInRing`

## Goal

Keep the root ingest pipeline, generated dashboard data, and native iOS bundle aligned so Hat In Ring behaves like one radar product instead of a static companion.

The current product loop is:

1. Run the pipeline.
2. Write candidate, review, signal, and freshness data.
3. Sync the native iOS bundle.
4. Build, install, and verify the iOS app.
5. Export iOS review decisions back into the pipeline when needed.

## Ownership Decision

The root repo owns both the pipeline and the native iOS source.

Evidence:

| Check | Result |
| --- | --- |
| Root repo | `/Users/daverobertson/Desktop/Code/10-projects/active/hat-in-ring` |
| Root remote | `https://github.com/DaveHomeAssist/hat-in-ring.git` |
| Nested iOS repo | Had no remote and only tracked `.gitignore` |
| Reconciliation action | Nested `.git` archived to `/private/tmp/hatinring-ios-nested-git-20260625-ownership-archive` |

Commit scope now belongs in the root repo. Do not commit `ios/HatInRing` as a submodule.

## Current Build State

| Surface | Status | Evidence |
| --- | --- | --- |
| Pipeline ingest | Green | Live FEC and news ingest produced refreshed data on 2026-06-25 |
| Pipeline to iOS sync | Green | `python -m hatring.pipeline --sync-ios` writes iOS data and referenced portraits |
| Native iOS app | Green | Built, installed, and launched on David's iPad |
| iOS tests | Green | Unit and UI tests passed in the latest implementation pass |
| Roadmap source | Green | This file replaces the stale preimplementation phase plan |
| Branch state | Yellow | Local branch is ahead 2 and behind 1 from `origin/main` |

Branch note:

| Side | Commit | Meaning |
| --- | --- | --- |
| Local only | `f4cd2b0` | Dashboard trust and usability polish |
| Local only | `4e178e1` | Dashboard template integration |
| Remote only | `79881d4` | Redirect old GitHub Pages path to System by Dave |

The remote side touches redirect, dashboard template, and dashboard test paths. The current pipeline and iOS commit can be made locally, but push should rebase or merge the remote redirect first.

## Implemented Features

### Pipeline

| Feature | Status | Notes |
| --- | --- | --- |
| FEC ingest | Green | Live OpenFEC presidential signal ingest |
| Google News ingest | Green | RSS based person and broad discovery queries |
| Deterministic classifier | Green | Regex and alias based signal classification |
| Merge and audit trail | Green | Idempotent signal log and protected curated fields |
| Review queue persistence | Green | Queue persists across runs and resolved ids are tracked |
| Review decisions input | Green | `data/review_decisions.json` is consumed by the pipeline |
| Freshness metadata | Green | `data/freshness.json` is generated from pipeline date |
| Native iOS sync | Green | `--sync-ios` copies candidate, review, freshness, and referenced portrait files |
| Full local run shortcut | Green | `run.sh` runs `--all --sync-ios` |

### Native iOS

| Feature | Status | Notes |
| --- | --- | --- |
| Native SwiftUI app | Green | No web view dependency |
| Field tab | Green | Candidate rows, portraits, scores, filters, sort |
| Wire tab | Green | Dispatch feed from candidate signals |
| Dossiers tab | Green | Candidate files and review mode |
| Search tab | Green | Suggestions, typed query, detail navigation |
| Picks tab | Green | Followed candidates persist across launch |
| Settings tab | Green | Data status, restore toggle, intro replay, clear picks, exports |
| Candidate detail | Green | Rationale, score ledger, file facts, tags, follow action |
| First run intro | Green | Dismissible intro with Field and Search entry actions |
| Resume state | Green | Last tab and recent candidate id persist safely |
| Data freshness | Green | App shows `UPDATED` with pipeline as of date |
| Review inbox | Green | Confirm, dismiss, save, and export local decisions |
| Critical data errors | Green | Missing or malformed candidate data shows a blocking issue |
| iPad install | Green | Built and launched on David's iPad |

## Phase Roadmap

| Phase | Name | Status | Current definition of done | Remaining work |
| --- | --- | --- | --- | --- |
| 0 | Work surface and ownership | Green | Root repo owns iOS source and nested repo metadata is archived | Commit root changes |
| 1 | Freshness honesty | Green | Pipeline metadata drives iOS copy and scoring date | None for bundled pipeline mode |
| 2 | Exit and return | Green | Last tab and recent candidate persist and recover | Add deeper detail restore only if product wants it |
| 3 | First run orientation | Green | Intro is shown once and can be replayed | Add screenshot proof in release pass |
| 4 | Settings and recovery | Green | Clear picks, export picks, intro replay, restore toggle, data status | Import picks is deferred |
| 5 | Review loop | Green | Bundled queue, local decisions, and pipeline compatible export | Remote submit and import apply are deferred |
| 6 | Core radar loop upgrades | Yellow | Basic filters, sort, search, dispatches, and detail are built | See Phase 6 remaining work |
| 7 | Accessibility and resilience | Yellow | Critical candidate data errors are visible | See Phase 7 remaining work |
| 8 | Release hygiene | Yellow | App builds and launches on device | Commit, rebase before push, add screenshot pack |

## Phase 6 Remaining Work

Goal: Make daily triage faster for a repeat user.

Definition of done:

| Area | Done when |
| --- | --- |
| Field rows | Rows show the reason a candidate moved when space allows |
| Wire | User can filter by signal type and party, and long lists group by date |
| Dossiers | Detail includes source trail, related review items, and a clearer score explanation |
| Picks | Picks support either notes or priority markers |
| Search | Search has clear recent searches and useful no result suggestions |
| iPad | Regular width layout can keep navigation and detail visible together |
| Tests | At least one UI test covers a filter empty state and reset path |

## Phase 7 Remaining Work

Goal: Make the app reliable under real iOS usage conditions.

Definition of done:

| Area | Done when |
| --- | --- |
| Dynamic Type | Field rows, tab labels, detail hero, and buttons remain readable at large sizes |
| VoiceOver | Candidate rows, filters, follow state, and review actions have useful labels |
| Reduced motion | Any future motion respects system settings |
| Local storage recovery | Corrupt picks and corrupt review decisions reset without crash |
| Resource recovery | Missing review bundle and empty review bundle have intentional states |
| Screenshots | Small iPhone and iPad screenshots show no text collisions |
| Tests | Storage recovery and missing resource paths are covered |

## Product Backlog

These are not part of the current local commit, but remain real product gaps.

| Item | Status | Definition of done |
| --- | --- | --- |
| In app live refresh | Not built | App can request a fresh bundle or API result, show loading and failure states, and preserve picks |
| Remote review submit | Not built | Confirm and dismiss actions can reach the pipeline without manual JSON export |
| Review import apply in iOS | Not built | A rebuilt bundle or imported decisions can mark resolved items inside the app |
| LLM adjudication | Stub | `classify_llm()` has a real provider path, tests, cost controls, and fallback behavior |
| Early state travel feed | Not built | Dedicated event or travel source adds `earlyState` without relying only on headlines |
| Cowork sidebar update path | Manual | Cowork handoff can be refreshed from generated output without copy paste drift |

## Commit Readiness

Stage these root owned changes:

| Path | Reason |
| --- | --- |
| `README.md` | Documents iOS sync and freshness output |
| `run.sh` | Runs pipeline plus iOS sync |
| `hatring/pipeline.py` | Freshness generation and iOS bundle sync |
| `data/candidates.json` | Refreshed pipeline dataset |
| `data/review_queue.json` | Refreshed review queue |
| `data/signals.jsonl` | Refreshed audit trail |
| `data/freshness.json` | Pipeline run metadata consumed by iOS |
| `ios/HatInRing/` | Native iOS app source, tests, docs, and bundle resources |

Do not stage these unrelated artifacts:

| Path | Reason |
| --- | --- |
| `Hat-In-Ring-handoff.zip` | Prior handoff artifact |
| `assets/candidates 2/` | Duplicate portrait export |
| `candidate-gallery 2.html` | Duplicate gallery artifact |

## Verification Gates

Before claiming a green release pass:

```bash
/tmp/hatinring-venv/bin/python -m pytest -q tests/test_pipeline_cli.py tests/test_pipeline_offline.py
/tmp/hatinring-venv/bin/python -m pytest -q tests/test_build_integrity.py
/tmp/hatinring-venv/bin/python -m hatring.pipeline --sync-ios -v
node -e "const fs=require('fs'); const b='ios/HatInRing/HatInRing/HatInRingData'; const c=JSON.parse(fs.readFileSync(b+'/candidates.json','utf8')); const q=JSON.parse(fs.readFileSync(b+'/review_queue.json','utf8')); const f=JSON.parse(fs.readFileSync(b+'/freshness.json','utf8')); console.log({candidates:c.length, missingImages:c.filter(x=>!x.img).length, reviewQueue:q.length, freshness:f.as_of});"
xcodebuild -project HatInRing.xcodeproj -scheme HatInRing -configuration Debug -destination 'platform=iOS,id=445A14BE-DDF1-5220-8D09-B83312A28AE6' -derivedDataPath /tmp/hatinring-device-derived build
xcrun devicectl device install app --device 445A14BE-DDF1-5220-8D09-B83312A28AE6 /tmp/hatinring-device-derived/Build/Products/Debug-iphoneos/HatInRing.app
xcrun devicectl device process launch --device 445A14BE-DDF1-5220-8D09-B83312A28AE6 com.davehomeassist.hatinring
```

Release note:

Local commit is safe after the gates pass. Push is not green until the branch divergence from `origin/main` is reconciled.
