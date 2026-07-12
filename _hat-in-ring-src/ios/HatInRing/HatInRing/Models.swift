import Foundation

enum SignalKey: String, Codable, CaseIterable, Hashable {
    case declared
    case exploratory
    case consideringQuote
    case softConsidering
    case earlyState
    case donors
    case staffing
    case mediaBlitz
    case endorsedOther
    case ruledOut
    case barred
}

enum FieldFilter: String, CaseIterable, Identifiable {
    case all
    case movers
    case inRing

    var id: String { rawValue }

    var label: String {
        switch self {
        case .all: return "All"
        case .movers: return "Movers"
        case .inRing: return "In the ring"
        }
    }
}

enum PartyFilter: String, CaseIterable, Identifiable {
    case all
    case democrat
    case republican
    case independent
    case libertarian

    var id: String { rawValue }

    var label: String {
        switch self {
        case .all: return "All lanes"
        case .democrat: return "Democrat"
        case .republican: return "Republican"
        case .independent: return "Independent"
        case .libertarian: return "Libertarian"
        }
    }

    func matches(_ candidate: Candidate) -> Bool {
        switch self {
        case .all: return true
        case .democrat: return candidate.party == "Democrat"
        case .republican: return candidate.party == "Republican"
        case .independent: return candidate.party == "Independent"
        case .libertarian: return candidate.party == "Libertarian"
        }
    }
}

enum ConfidenceFilter: String, CaseIterable, Identifiable {
    case all
    case veryHigh
    case high
    case medium
    case low

    var id: String { rawValue }

    var label: String {
        switch self {
        case .all: return "All confidence"
        case .veryHigh: return "Very high"
        case .high: return "High"
        case .medium: return "Medium"
        case .low: return "Low"
        }
    }

    func matches(_ candidate: Candidate) -> Bool {
        switch self {
        case .all: return true
        case .veryHigh: return candidate.confidence == "Very high"
        case .high: return candidate.confidence == "High"
        case .medium: return candidate.confidence == "Medium"
        case .low: return candidate.confidence == "Low"
        }
    }
}

enum FieldSort: String, CaseIterable, Identifiable {
    case momentum
    case recency
    case name

    var id: String { rawValue }

    var label: String {
        switch self {
        case .momentum: return "Momentum"
        case .recency: return "Recency"
        case .name: return "Name"
        }
    }
}

enum DossierMode: String, CaseIterable, Identifiable {
    case files
    case review

    var id: String { rawValue }

    var label: String {
        switch self {
        case .files: return "Files"
        case .review: return "Review"
        }
    }
}

enum AppTab: String, CaseIterable, Identifiable {
    case field
    case wire
    case dossiers
    case search
    case picks
    case settings

    var id: String { rawValue }

    var label: String {
        switch self {
        case .field: return "Field"
        case .wire: return "Wire"
        case .dossiers: return "Dossiers"
        case .search: return "Search"
        case .picks: return "Picks"
        case .settings: return "Settings"
        }
    }

    var symbol: String {
        switch self {
        case .field: return "scope"
        case .wire: return "dot.radiowaves.left.and.right"
        case .dossiers: return "folder"
        case .search: return "magnifyingglass"
        case .picks: return "star"
        case .settings: return "gearshape"
        }
    }
}

enum DataFreshnessMode: String, Codable {
    case pipeline
    case snapshot
    case live
}

struct DataFreshness: Codable, Hashable {
    static let staleAfterDays = 3
    let mode: DataFreshnessMode
    let asOf: String
    let sourceLabel: String
    let buildLabel: String

    static let bundled = DataFreshness(
        mode: .pipeline,
        asOf: RadarScoring.defaultISODate,
        sourceLabel: "Hat-in-Ring ingest pipeline",
        buildLabel: "Native bundle"
    )

    enum CodingKeys: String, CodingKey {
        case mode
        case asOf = "as_of"
        case sourceLabel = "source"
        case buildLabel = "build"
    }

    init(
        mode: DataFreshnessMode,
        asOf: String,
        sourceLabel: String,
        buildLabel: String
    ) {
        self.mode = mode
        self.asOf = asOf
        self.sourceLabel = sourceLabel
        self.buildLabel = buildLabel
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        mode = try container.decodeIfPresent(DataFreshnessMode.self, forKey: .mode) ?? .pipeline
        asOf = try container.decodeIfPresent(String.self, forKey: .asOf) ?? RadarScoring.defaultISODate
        sourceLabel = try container.decodeIfPresent(String.self, forKey: .sourceLabel) ?? "Hat-in-Ring ingest pipeline"
        buildLabel = try container.decodeIfPresent(String.self, forKey: .buildLabel) ?? "Native bundle"
    }

    var snapshotDateText: String {
        RadarScoring.longDate(asOf)
    }

    var referenceDate: Date {
        RadarScoring.dateFromISO(asOf) ?? RadarScoring.defaultReferenceDate
    }

    func isStale(relativeTo currentDate: Date = Date()) -> Bool {
        guard mode == .pipeline,
              let pipelineDate = RadarScoring.dateFromISO(asOf) else { return false }
        let calendar = Calendar(identifier: .gregorian)
        let start = calendar.startOfDay(for: pipelineDate)
        let end = calendar.startOfDay(for: currentDate)
        return (calendar.dateComponents([.day], from: start, to: end).day ?? 0) > Self.staleAfterDays
    }

    func statusLabel(relativeTo currentDate: Date = Date()) -> String {
        switch mode {
        case .pipeline: return isStale(relativeTo: currentDate) ? "STALE" : "UPDATED"
        case .snapshot: return "ARCHIVE"
        case .live: return "LIVE"
        }
    }

    var statusLabel: String { statusLabel() }

    var summary: String {
        switch mode {
        case .pipeline: return "\(statusLabel == "STALE" ? "Stale" : "Updated") as of \(snapshotDateText)"
        case .snapshot: return "Archived \(snapshotDateText)"
        case .live: return "Live data"
        }
    }

    var detail: String {
        switch mode {
        case .pipeline: return "\(sourceLabel). Scores remain anchored to the \(snapshotDateText) pipeline run."
        case .snapshot: return "\(sourceLabel). Scores use the archived date."
        case .live: return "\(sourceLabel). Scores use current data."
        }
    }

    func movementSubtitle(moverCount: Int) -> String {
        switch mode {
        case .pipeline: return "\(moverCount) moved in the latest pipeline run"
        case .snapshot: return "\(moverCount) moved in this archived window"
        case .live: return "\(moverCount) moved in the last 14 days"
        }
    }

    func wireSubtitle(dispatchCount: Int) -> String {
        switch mode {
        case .pipeline: return "\(dispatchCount) updated dispatches"
        case .snapshot: return "\(dispatchCount) archived dispatches"
        case .live: return "\(dispatchCount) dispatches, newest first"
        }
    }

    func recencyLabel(days: Int) -> String {
        switch mode {
        case .pipeline:
            if days <= 0 { return "update day" }
            if days == 1 { return "1d before update" }
            if days <= 45 { return "\(days)d before update" }
            return "\(Int(round(Double(days) / 30.0)))mo before update"
        case .snapshot:
            if days <= 0 { return "archive day" }
            if days == 1 { return "1d before archive" }
            if days <= 45 { return "\(days)d before archive" }
            return "\(Int(round(Double(days) / 30.0)))mo before archive"
        case .live:
            return RadarScoring.recencyLabel(days: days)
        }
    }
}

struct RadarStatus: Hashable, Identifiable {
    let tier: Int
    let label: String
    let detail: String

    var id: Int { tier }
}

struct MomentumBreakdown: Hashable, Identifiable {
    let label: String
    let weight: Int

    var id: String { "\(label)-\(weight)" }
}

struct Dispatch: Identifiable, Hashable {
    let id: String
    let candidateID: String
    let candidateName: String
    let party: String
    let title: String
    let source: String
    let date: Date
    let days: Int
    let tags: [String]
    let sourceURL: URL?
}

enum ReviewDecisionAction: String, Codable, CaseIterable, Hashable {
    case confirm
    case dismiss
    case later

    var label: String {
        switch self {
        case .confirm: return "Confirm"
        case .dismiss: return "Dismiss"
        case .later: return "Save"
        }
    }

    var isExportable: Bool {
        self == .confirm || self == .dismiss
    }
}

struct ReviewDecision: Codable, Identifiable, Hashable {
    let rid: String
    let action: ReviewDecisionAction

    var id: String { rid }
}

struct ReviewItem: Codable, Identifiable, Hashable {
    let name: String
    let headline: String
    let url: String?
    let source: String
    let date: String
    let keys: [SignalKey]
    let note: String?
    let rid: String
    let kind: String

    var id: String { rid }

    var sourceURL: URL? { ValidatedSourceURL.url(from: url) }

    var signalLabel: String {
        keys.map(\.label).joined(separator: ", ")
    }

    var kindLabel: String {
        switch kind {
        case "denial": return "Denial check"
        case "discovery": return "Discovery"
        default: return kind.capitalized
        }
    }
}

struct Candidate: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let party: String
    let role: String
    let bucket: String
    let keys: [SignalKey]
    let confidence: String
    let delta: Int
    let lastSignal: String
    let headline: String
    let why: String
    let quote: String
    let tags: [String]
    let imagePath: String
    let pollLead: String?
    let sourceUrl: String?

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case party
        case role
        case bucket
        case keys
        case confidence = "conf"
        case delta
        case lastSignal
        case headline
        case why
        case quote
        case tags
        case imagePath = "img"
        case pollLead
        case sourceUrl
    }

    init(
        id: String, name: String, party: String, role: String, bucket: String,
        keys: [SignalKey], confidence: String, delta: Int, lastSignal: String,
        headline: String, why: String, quote: String, tags: [String],
        imagePath: String, pollLead: String?, sourceUrl: String? = nil
    ) {
        self.id = id
        self.name = name
        self.party = party
        self.role = role
        self.bucket = bucket
        self.keys = keys
        self.confidence = confidence
        self.delta = delta
        self.lastSignal = lastSignal
        self.headline = headline
        self.why = why
        self.quote = quote
        self.tags = tags
        self.imagePath = imagePath
        self.pollLead = pollLead
        self.sourceUrl = sourceUrl
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        name = try container.decode(String.self, forKey: .name)
        party = try container.decode(String.self, forKey: .party)
        role = try container.decode(String.self, forKey: .role)
        bucket = try container.decode(String.self, forKey: .bucket)
        keys = try container.decode([SignalKey].self, forKey: .keys)
        confidence = try container.decode(String.self, forKey: .confidence)
        delta = try container.decode(Int.self, forKey: .delta)
        lastSignal = try container.decode(String.self, forKey: .lastSignal)
        headline = try container.decode(String.self, forKey: .headline)
        why = try container.decode(String.self, forKey: .why)
        quote = try container.decode(String.self, forKey: .quote)
        tags = try container.decode([String].self, forKey: .tags)
        imagePath = try container.decodeIfPresent(String.self, forKey: .imagePath) ?? ""
        pollLead = try container.decodeIfPresent(String.self, forKey: .pollLead)
        sourceUrl = try container.decodeIfPresent(String.self, forKey: .sourceUrl)
    }

    var sourceURL: URL? { ValidatedSourceURL.url(from: sourceUrl) }

    var partyLetter: String {
        switch party {
        case "Democrat": return "D"
        case "Republican": return "R"
        case "Libertarian": return "L"
        case "Independent": return "I"
        default: return "."
        }
    }

    var bucketLabel: String {
        switch bucket {
        case "formal": return "Formal: declared or exploratory"
        case "considering": return "Actively considering"
        case "soft": return "Soft or positioning"
        case "edge": return "Edge or conditional"
        case "out": return "Ruled out or inactive"
        default: return bucket.capitalized
        }
    }
}

enum ValidatedSourceURL {
    static func url(from value: String?) -> URL? {
        guard let value,
              let url = URL(string: value),
              ["http", "https"].contains(url.scheme?.lowercased() ?? ""),
              url.host != nil else { return nil }
        return url
    }
}

extension SignalKey {
    var label: String {
        switch self {
        case .declared: return "Declared"
        case .exploratory: return "Exploratory"
        case .consideringQuote: return "Considering quote"
        case .softConsidering: return "Not ruling out"
        case .earlyState: return "Early state"
        case .donors: return "Donor activity"
        case .staffing: return "Staffing"
        case .mediaBlitz: return "Media blitz"
        case .endorsedOther: return "Endorsed another"
        case .ruledOut: return "Ruled out"
        case .barred: return "Ineligible"
        }
    }
}

struct PickExport: Codable {
    let updated: String
    let ids: [String]
    let picks: [PickExportCandidate]
}

struct PickExportCandidate: Codable {
    let id: String
    let name: String
    let party: String
    let role: String
    let momentum: Int
    let status: String
}
