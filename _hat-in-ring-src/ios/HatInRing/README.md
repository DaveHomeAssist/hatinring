# Hat-in-Ring iOS

Native SwiftUI build of the Hat-in-Ring Radar iOS handoff. The existing Python and generated web dashboard remain at the repo root. This app is a separate native iOS surface, with no web view dependency.

## Run

Open `HatInRing.xcodeproj`, select the `HatInRing` scheme, choose an iPhone or iPad simulator, and run.

Repo strategy: this native app currently stays in the nested `ios/HatInRing` project. Keep SwiftUI app work scoped here until the root project explicitly promotes or flattens the iOS surface.

Command line build:

```bash
xcodebuild -project HatInRing.xcodeproj -scheme HatInRing -destination 'platform=iOS Simulator,name=iPhone 17e,OS=26.5' build
```

If that simulator is not available, run:

```bash
xcrun simctl list devices available
```

Then use the available device id:

```bash
xcodebuild -project HatInRing.xcodeproj -scheme HatInRing -destination 'id=<device-id>' build
```

Core behavior test:

```bash
xcrun -sdk macosx swiftc -D DIRECT_TEST -parse-as-library HatInRing/AppState.swift HatInRing/Models.swift HatInRing/Scoring.swift HatInRing/CandidateStore.swift HatInRingTests/DirectTestMain.swift -o /tmp/hatinring-core-tests && /tmp/hatinring-core-tests
```

## Layout

| Path | Role |
| --- | --- |
| `HatInRing/HatInRingApp.swift` | App entry |
| `HatInRing/Models.swift` | Candidate, Dispatch, RadarStatus, MomentumBreakdown |
| `HatInRing/Scoring.swift` | Native port of scoring and status logic |
| `HatInRing/AppState.swift` | Observable tab, search, navigation, and persisted picks state |
| `HatInRing/CandidateStore.swift` | Bundled JSON loading, filters, search, dispatch feed |
| `HatInRing/Components.swift` | Cards, pills, portraits, rows, custom tab bar |
| `HatInRing/Screens.swift` | Field, Wire, Dossiers, Search, and My Picks |
| `HatInRing/CandidateDetailView.swift` | Native dossier detail |
| `HatInRing/HatInRingData/` | Bundled candidate JSON and portraits |
| `HatInRingTests/` | Scoring, filtering, and watchlist tests |

## Notes

The prototype fonts were Newsreader, Space Grotesk, Pinyon Script, and Space Mono. No font files were included in the handoff, so the app uses native serif, default, and monospaced designs as fallbacks. Add font files to the target and swap `HIRTheme` helpers if exact font matching is required.

The iOS app ships with pipeline-refreshed bundled data. Run the root pipeline with `--sync-ios` before building for device so `HatInRingData/candidates.json`, `review_queue.json`, and `freshness.json` match the latest ingest.

Run `node generate-xcodeproj.js` after adding or removing Swift files.
