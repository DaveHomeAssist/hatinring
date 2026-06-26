import Foundation
import Observation

@Observable
final class HatInRingState {
    private static let watchKey = "hir.native.watchlist"
    private static let selectedTabKey = "hir.native.selectedTab"
    private static let restoreTabKey = "hir.native.restoreTab"
    private static let recentCandidateKey = "hir.native.recentCandidate"
    private static let introSeenKey = "hir.native.introSeen"
    private static let reviewDecisionsKey = "hir.native.reviewDecisions"

    var selectedTab: AppTab {
        didSet { saveSelectedTab() }
    }
    var fieldFilter: FieldFilter = .all
    var fieldPartyFilter: PartyFilter = .all
    var fieldConfidenceFilter: ConfidenceFilter = .all
    var fieldSort: FieldSort = .momentum
    var dossierMode: DossierMode = .files
    var wirePartyFilter: PartyFilter = .all
    var dossierQuery = ""
    var searchQuery = ""
    var path: [String] = []
    var recentCandidateID: String? {
        didSet { saveRecentCandidate() }
    }
    var restoreLastTab: Bool {
        didSet { saveRestorePreference() }
    }
    var shouldShowIntro: Bool
    var reviewDecisions: [String: ReviewDecisionAction] {
        didSet { saveReviewDecisions() }
    }
    var watchedCandidateIDs: Set<String> {
        didSet { saveWatchlist() }
    }

    @ObservationIgnored private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard, skipIntro: Bool = false) {
        self.defaults = defaults
        let shouldRestore = defaults.object(forKey: Self.restoreTabKey) as? Bool ?? true
        let restoredTab: AppTab
        if shouldRestore,
           let rawTab = defaults.string(forKey: Self.selectedTabKey),
           let tab = AppTab(rawValue: rawTab) {
            restoredTab = tab
        } else {
            restoredTab = .field
        }
        let shouldShowIntro = skipIntro ? false : !defaults.bool(forKey: Self.introSeenKey)
        let watchedIDs: Set<String>
        let reviewDecisions: [String: ReviewDecisionAction]
        if let data = defaults.data(forKey: Self.watchKey),
           let decoded = try? JSONDecoder().decode([String].self, from: data) {
            watchedIDs = Set(decoded)
        } else {
            watchedIDs = []
        }
        if let data = defaults.data(forKey: Self.reviewDecisionsKey),
           let decoded = try? JSONDecoder().decode([ReviewDecision].self, from: data) {
            reviewDecisions = Dictionary(uniqueKeysWithValues: decoded.map { ($0.rid, $0.action) })
        } else {
            reviewDecisions = [:]
        }
        self.restoreLastTab = shouldRestore
        self.selectedTab = restoredTab
        self.recentCandidateID = defaults.string(forKey: Self.recentCandidateKey)
        self.shouldShowIntro = shouldShowIntro
        self.reviewDecisions = reviewDecisions
        self.watchedCandidateIDs = watchedIDs
    }

    static func resetPersistentState(defaults: UserDefaults = .standard) {
        defaults.removeObject(forKey: watchKey)
        defaults.removeObject(forKey: selectedTabKey)
        defaults.removeObject(forKey: restoreTabKey)
        defaults.removeObject(forKey: recentCandidateKey)
        defaults.removeObject(forKey: introSeenKey)
        defaults.removeObject(forKey: reviewDecisionsKey)
    }

    func selectTab(_ tab: AppTab) {
        selectedTab = tab
        path.removeAll()
    }

    func openCandidate(_ id: String) {
        recentCandidateID = id
        path = [id]
    }

    func isWatching(_ id: String) -> Bool {
        watchedCandidateIDs.contains(id)
    }

    func toggleWatch(_ id: String) {
        if watchedCandidateIDs.contains(id) {
            watchedCandidateIDs.remove(id)
        } else {
            watchedCandidateIDs.insert(id)
        }
    }

    func clearWatchlist() {
        watchedCandidateIDs.removeAll()
    }

    func dismissIntro(opening tab: AppTab? = nil) {
        defaults.set(true, forKey: Self.introSeenKey)
        shouldShowIntro = false
        if let tab {
            selectTab(tab)
        }
    }

    func showIntroAgain() {
        shouldShowIntro = true
    }

    func setReviewDecision(_ action: ReviewDecisionAction, for rid: String) {
        reviewDecisions[rid] = action
    }

    func reviewDecision(for rid: String) -> ReviewDecisionAction? {
        reviewDecisions[rid]
    }

    func exportableReviewDecisions() -> [ReviewDecision] {
        reviewDecisions
            .compactMap { rid, action in
                action.isExportable ? ReviewDecision(rid: rid, action: action) : nil
            }
            .sorted { $0.rid < $1.rid }
    }

    func exportReviewDecisionsJSON() -> String {
        encodePretty(exportableReviewDecisions())
    }

    func exportPicksJSON(from candidates: [Candidate]) -> String {
        let picks = candidates
            .filter { watchedCandidateIDs.contains($0.id) }
            .sortedByMomentum()
            .map { candidate in
                PickExportCandidate(
                    id: candidate.id,
                    name: candidate.name,
                    party: candidate.party,
                    role: candidate.role,
                    momentum: RadarScoring.momentum(for: candidate),
                    status: RadarScoring.status(for: candidate.keys).label
                )
            }
        let export = PickExport(
            updated: RadarScoring.asOfText,
            ids: picks.map(\.id),
            picks: picks
        )
        return encodePretty(export)
    }

    private func saveWatchlist() {
        let ids = Array(watchedCandidateIDs).sorted()
        if let data = try? JSONEncoder().encode(ids) {
            defaults.set(data, forKey: Self.watchKey)
        }
    }

    private func saveSelectedTab() {
        defaults.set(selectedTab.rawValue, forKey: Self.selectedTabKey)
    }

    private func saveRestorePreference() {
        defaults.set(restoreLastTab, forKey: Self.restoreTabKey)
        if !restoreLastTab {
            selectedTab = .field
        }
    }

    private func saveRecentCandidate() {
        if let recentCandidateID {
            defaults.set(recentCandidateID, forKey: Self.recentCandidateKey)
        } else {
            defaults.removeObject(forKey: Self.recentCandidateKey)
        }
    }

    private func saveReviewDecisions() {
        let decisions = reviewDecisions
            .map { ReviewDecision(rid: $0.key, action: $0.value) }
            .sorted { $0.rid < $1.rid }
        if let data = try? JSONEncoder().encode(decisions) {
            defaults.set(data, forKey: Self.reviewDecisionsKey)
        }
    }

    private func encodePretty<T: Encodable>(_ value: T) -> String {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        guard let data = try? encoder.encode(value),
              let text = String(data: data, encoding: .utf8) else {
            return "[]"
        }
        return text
    }
}
