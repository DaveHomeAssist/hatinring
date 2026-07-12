#if DIRECT_TEST
import Foundation

@main
struct DirectTestRunner {
    static func main() {
        var failures: [String] = []

        func expect(_ condition: @autoclosure () -> Bool, _ message: String) {
            if !condition() {
                failures.append(message)
            }
        }

        let hardStop = RadarScoring.status(for: [.declared, .barred])
        expect(hardStop.tier == 0, "hard stop status tier")
        expect(hardStop.label == "Ineligible", "hard stop status label")

        let newsom = makeCandidate(
            id: "newsom",
            keys: [.consideringQuote, .earlyState, .donors, .staffing, .mediaBlitz],
            lastSignal: "2026-06-12"
        )
        expect(RadarScoring.momentum(for: newsom) == 60, "momentum score")

        let declared = makeCandidate(id: "declared", keys: [.declared], lastSignal: "2026-05-26")
        let stale = makeCandidate(id: "stale", keys: [.mediaBlitz], lastSignal: "2026-01-01")
        let mover = makeCandidate(id: "mover", keys: [.softConsidering], lastSignal: "2026-06-10")
        let store = CandidateStore(candidates: [declared, stale, mover])
        expect(Set(store.fieldCandidates(filter: .inRing).map(\.id)) == ["declared"], "in ring filter")
        expect(Set(store.fieldCandidates(filter: .movers).map(\.id)) == ["mover"], "movers filter")

        let suiteName = "HatInRingDirectTests.\(UUID().uuidString)"
        let defaults = UserDefaults(suiteName: suiteName)!
        defer { defaults.removePersistentDomain(forName: suiteName) }

        let first = HatInRingState(defaults: defaults)
        first.toggleWatch("newsom")
        first.toggleWatch("vance")

        let second = HatInRingState(defaults: defaults)
        expect(second.isWatching("newsom"), "watchlist persisted newsom")
        expect(second.isWatching("vance"), "watchlist persisted vance")
        expect(!second.isWatching("harris"), "watchlist excludes unpicked candidate")

        let freshness = DataFreshness(
            mode: .pipeline,
            asOf: "2026-07-06",
            sourceLabel: "Hat-in-Ring ingest pipeline",
            buildLabel: "Direct test"
        )
        expect(freshness.statusLabel(relativeTo: RadarScoring.dateFromISO("2026-07-09")!) == "UPDATED", "current status label")
        expect(freshness.statusLabel(relativeTo: RadarScoring.dateFromISO("2026-07-10")!) == "STALE", "stale status label")
        expect(freshness.summary.contains("July 6, 2026"), "freshness retains exact as-of date")
        expect(freshness.movementSubtitle(moverCount: 9) == "9 moved in the latest pipeline run", "updated movement copy")
        expect(freshness.recencyLabel(days: 1) == "1d before update", "updated recency copy")

        let state = HatInRingState(defaults: defaults, skipIntro: true)
        state.selectTab(.search)
        state.openCandidate("newsom")
        state.setReviewDecision(.confirm, for: "rid-a")
        state.setReviewDecision(.later, for: "rid-b")
        let restored = HatInRingState(defaults: defaults, skipIntro: true)
        expect(restored.selectedTab == .search, "selected tab restored")
        expect(restored.recentCandidateID == "newsom", "recent candidate restored")
        expect(restored.exportableReviewDecisions() == [ReviewDecision(rid: "rid-a", action: .confirm)], "review export filters later")

        let candidateJSON = Data("""
        {
          "id": "fixture", "name": "Fixture Person", "party": "Independent",
          "role": "Governor", "bucket": "considering", "keys": ["softConsidering"],
          "conf": "High", "delta": 1, "lastSignal": "2026-07-06",
          "headline": "Fixture headline - Source", "why": "Fixture reason",
          "quote": "", "tags": [], "sourceUrl": "https://example.com/report"
        }
        """.utf8)
        if let decoded = try? JSONDecoder().decode(Candidate.self, from: candidateJSON) {
            expect(decoded.imagePath.isEmpty, "missing image decodes to placeholder path")
            expect(decoded.sourceURL?.absoluteString == "https://example.com/report", "source URL decodes")
        } else {
            failures.append("candidate without image decodes")
        }

        let bundleCandidatesURL = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
            .appendingPathComponent("HatInRing/HatInRingData/candidates.json")
        if let data = try? Data(contentsOf: bundleCandidatesURL),
           let decoded = try? JSONDecoder().decode([Candidate].self, from: data) {
            expect(!decoded.isEmpty, "bundled candidates JSON decodes")
        } else {
            failures.append("bundled candidates JSON decodes")
        }

        if failures.isEmpty {
            print("HatInRing core behavior tests passed.")
        } else {
            for failure in failures {
                print("FAILED: \(failure)")
            }
            Foundation.exit(1)
        }
    }

    private static func makeCandidate(
        id: String,
        keys: [SignalKey],
        lastSignal: String,
        delta: Int = 0
    ) -> Candidate {
        Candidate(
            id: id,
            name: id.capitalized,
            party: "Democrat",
            role: "Governor",
            bucket: "considering",
            keys: keys,
            confidence: "High",
            delta: delta,
            lastSignal: lastSignal,
            headline: "Signal headline - Source",
            why: "Fixture",
            quote: "",
            tags: [],
            imagePath: "assets/candidates/newsom/01_governor_of_california_gavin_newsom_cropped_3x4_jp.jpg",
            pollLead: nil
        )
    }
}
#endif
