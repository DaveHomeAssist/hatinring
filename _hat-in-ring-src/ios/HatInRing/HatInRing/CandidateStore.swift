import Foundation

struct StoreLoadIssue: Hashable {
    let title: String
    let message: String
}

struct CandidateStore {
    let candidates: [Candidate]
    let reviewItems: [ReviewItem]
    let freshness: DataFreshness
    let criticalIssue: StoreLoadIssue?

    init(
        candidates: [Candidate],
        reviewItems: [ReviewItem] = [],
        freshness: DataFreshness = .bundled,
        criticalIssue: StoreLoadIssue? = nil
    ) {
        self.candidates = candidates
        self.reviewItems = reviewItems
        self.freshness = freshness
        self.criticalIssue = criticalIssue
        RadarScoring.configure(referenceDate: freshness.referenceDate)
    }

    static func load(bundle: Bundle = .hatInRingResources) -> CandidateStore {
        let url = resourceURL(bundle: bundle, filename: "candidates", extension: "json")

        guard let url, let candidateData = try? Data(contentsOf: url) else {
            return load(candidatesData: nil)
        }

        let reviewURL = resourceURL(bundle: bundle, filename: "review_queue", extension: "json")
        let reviewData = reviewURL.flatMap { try? Data(contentsOf: $0) }
        let freshnessURL = resourceURL(bundle: bundle, filename: "freshness", extension: "json")
        let freshnessData = freshnessURL.flatMap { try? Data(contentsOf: $0) }
        return load(candidatesData: candidateData, reviewData: reviewData, freshnessData: freshnessData)
    }

    static func load(
        candidatesData: Data?,
        reviewData: Data? = nil,
        freshnessData: Data? = nil
    ) -> CandidateStore {
        let decoder = JSONDecoder()
        let freshness = loadFreshness(data: freshnessData, decoder: decoder)

        guard let candidatesData else {
            return CandidateStore(
                candidates: [],
                freshness: freshness,
                criticalIssue: StoreLoadIssue(
                    title: "Candidate data unavailable",
                    message: "The bundled candidate file could not be found. Reinstall or rebuild the app bundle before using the radar."
                )
            )
        }

        do {
            let candidates = try decoder.decode([Candidate].self, from: candidatesData)
            let reviewItems = loadReviewItems(data: reviewData, decoder: decoder)
            return CandidateStore(candidates: candidates, reviewItems: reviewItems, freshness: freshness)
        } catch {
            return CandidateStore(
                candidates: [],
                freshness: freshness,
                criticalIssue: StoreLoadIssue(
                    title: "Candidate data could not load",
                    message: "The bundled candidate file is malformed. Rebuild the bundle from the pipeline before using the radar."
                )
            )
        }
    }

    func candidate(id: String) -> Candidate? {
        candidates.first { $0.id == id }
    }

    func fieldCandidates(
        filter: FieldFilter,
        party: PartyFilter = .all,
        confidence: ConfidenceFilter = .all,
        sort: FieldSort = .momentum
    ) -> [Candidate] {
        var rows = candidates
        switch filter {
        case .all:
            break
        case .movers:
            rows = rows.filter(RadarScoring.isMover)
        case .inRing:
            rows = rows.filter { RadarScoring.status(for: $0.keys).tier >= 4 }
        }
        rows = rows.filter { party.matches($0) && confidence.matches($0) }
        return sorted(rows, by: sort)
    }

    func dossierCandidates(query: String) -> [Candidate] {
        let sorted = candidates.sortedByMomentum()
        return filter(sorted, query: query, includeHeadline: false)
    }

    func searchCandidates(query: String) -> [Candidate] {
        let sorted = candidates.sortedByMomentum()
        return filter(sorted, query: query, includeHeadline: true)
    }

    func watchedCandidates(ids: Set<String>) -> [Candidate] {
        candidates
            .filter { ids.contains($0.id) }
            .sortedByMomentum()
    }

    func dispatches(party: PartyFilter = .all) -> [Dispatch] {
        candidates.filter { party.matches($0) }.compactMap { candidate in
            guard let date = RadarScoring.dateFromISO(candidate.lastSignal) else {
                return nil
            }
            let sourceParts = RadarScoring.parseSource(candidate.headline)
            let tags = candidate.keys.prefix(2).map(\.label)
            return Dispatch(
                id: "\(candidate.id)-\(candidate.lastSignal)",
                candidateID: candidate.id,
                candidateName: candidate.name,
                party: candidate.party,
                title: sourceParts.title,
                source: sourceParts.source,
                date: date,
                days: RadarScoring.daysSince(candidate.lastSignal),
                tags: tags,
                sourceURL: candidate.sourceURL
            )
        }
        .sorted { $0.date > $1.date }
    }

    func pendingReviewItems(decisions: [String: ReviewDecisionAction]) -> [ReviewItem] {
        reviewItems.filter { item in
            guard let decision = decisions[item.rid] else { return true }
            return decision == .later
        }
    }

    private func filter(_ rows: [Candidate], query: String, includeHeadline: Bool) -> [Candidate] {
        let clean = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !clean.isEmpty else { return rows }

        return rows.filter { candidate in
            var haystack = "\(candidate.name) \(candidate.role) \(candidate.party) \(candidate.tags.joined(separator: " "))"
            if includeHeadline {
                haystack += " \(candidate.headline) \(candidate.why)"
            }
            return haystack.lowercased().contains(clean)
        }
    }

    private func sorted(_ rows: [Candidate], by sort: FieldSort) -> [Candidate] {
        switch sort {
        case .momentum:
            return rows.sortedByMomentum()
        case .recency:
            return rows.sorted {
                let left = RadarScoring.dateFromISO($0.lastSignal) ?? .distantPast
                let right = RadarScoring.dateFromISO($1.lastSignal) ?? .distantPast
                if left == right { return $0.name < $1.name }
                return left > right
            }
        case .name:
            return rows.sorted { $0.name < $1.name }
        }
    }

    private static func resourceURL(bundle: Bundle, filename: String, extension ext: String) -> URL? {
        let fileName = "\(filename).\(ext)"
        let bundles = [bundle, Bundle.main] + Bundle.allBundles + Bundle.allFrameworks
        var searchedRoots = Set<URL>()

        for candidateBundle in bundles {
            guard var root = candidateBundle.resourceURL else { continue }
            for _ in 0..<5 {
                if searchedRoots.insert(root).inserted {
                    let nestedURL = root.appendingPathComponent("HatInRingData").appendingPathComponent(fileName)
                    if FileManager.default.fileExists(atPath: nestedURL.path) {
                        return nestedURL
                    }
                    let flatURL = root.appendingPathComponent(fileName)
                    if FileManager.default.fileExists(atPath: flatURL.path) {
                        return flatURL
                    }
                }
                root.deleteLastPathComponent()
            }
        }
        return nil
    }

    private static func loadReviewItems(data: Data?, decoder: JSONDecoder) -> [ReviewItem] {
        guard let data else { return [] }
        return (try? decoder.decode([ReviewItem].self, from: data)) ?? []
    }

    private static func loadFreshness(data: Data?, decoder: JSONDecoder) -> DataFreshness {
        guard let data else { return .bundled }
        return (try? decoder.decode(DataFreshness.self, from: data)) ?? .bundled
    }
}

extension Array where Element == Candidate {
    func sortedByMomentum() -> [Candidate] {
        sorted {
            let leftScore = RadarScoring.momentum(for: $0)
            let rightScore = RadarScoring.momentum(for: $1)
            if leftScore == rightScore {
                return $0.name < $1.name
            }
            return leftScore > rightScore
        }
    }
}

private extension Bundle {
    static var hatInRingResources: Bundle {
        #if SWIFT_PACKAGE
        return .module
        #else
        return .main
        #endif
    }
}
