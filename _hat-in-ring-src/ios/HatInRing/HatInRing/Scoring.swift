import Foundation

enum RadarScoring {
    static let defaultISODate = "2026-06-14"

    static let defaultReferenceDate: Date = {
        var components = DateComponents()
        components.calendar = Calendar(identifier: .gregorian)
        components.timeZone = TimeZone(secondsFromGMT: 0)
        components.year = 2026
        components.month = 6
        components.day = 14
        components.hour = 12
        return components.date!
    }()

    private static var configuredReferenceDate = defaultReferenceDate

    static var referenceDate: Date {
        configuredReferenceDate
    }

    static var asOfText: String {
        longFormatter.string(from: configuredReferenceDate)
    }

    static func configure(referenceDate: Date) {
        configuredReferenceDate = referenceDate
    }

    private static let declarativeOrder: [SignalKey] = [
        .declared,
        .exploratory,
        .consideringQuote,
        .softConsidering
    ]

    private static let behavioralOrder: [SignalKey] = [
        .earlyState,
        .donors,
        .staffing,
        .mediaBlitz
    ]

    private static let penaltyOrder: [SignalKey] = [
        .endorsedOther,
        .ruledOut,
        .barred
    ]

    static let weights: [SignalKey: MomentumBreakdown] = [
        .declared: MomentumBreakdown(label: "Formal FEC candidacy / launch", weight: 40),
        .exploratory: MomentumBreakdown(label: "Exploratory committee", weight: 30),
        .consideringQuote: MomentumBreakdown(label: "Direct considering quote", weight: 20),
        .softConsidering: MomentumBreakdown(label: "Soft / not ruling out quote", weight: 12),
        .earlyState: MomentumBreakdown(label: "Early state travel", weight: 10),
        .donors: MomentumBreakdown(label: "Donor meetings / PAC activity", weight: 10),
        .staffing: MomentumBreakdown(label: "Campaign staffing / consultants", weight: 10),
        .mediaBlitz: MomentumBreakdown(label: "National media blitz", weight: 5),
        .endorsedOther: MomentumBreakdown(label: "Endorsed another candidate", weight: -20),
        .ruledOut: MomentumBreakdown(label: "Explicitly ruled out", weight: -40),
        .barred: MomentumBreakdown(label: "Constitutionally ineligible", weight: -100)
    ]

    static func status(for keys: [SignalKey]) -> RadarStatus {
        let set = Set(keys)
        if set.contains(.barred) {
            return RadarStatus(tier: 0, label: "Ineligible", detail: "Constitutionally ineligible")
        }
        if set.contains(.ruledOut) {
            return RadarStatus(tier: 0, label: "Ruled out", detail: "Explicitly ruled out")
        }
        if set.contains(.declared) {
            return RadarStatus(tier: 5, label: "Declared", detail: "Filed FEC Form 2 or formal launch")
        }
        if set.contains(.exploratory) {
            return RadarStatus(tier: 4, label: "Exploratory", detail: "Exploratory committee or testing the waters")
        }
        if set.contains(.consideringQuote) {
            return RadarStatus(tier: 3, label: "Considering", detail: "Direct considering quote on record")
        }
        if !set.intersection(Set(behavioralOrder)).isEmpty {
            return RadarStatus(tier: 2, label: "Positioning", detail: "Travel, donors, staff, or media activity")
        }
        if set.contains(.softConsidering) {
            return RadarStatus(tier: 1, label: "Floated", detail: "Floated or not ruling out")
        }
        return RadarStatus(tier: 0, label: "Inactive", detail: "No current signal")
    }

    static func breakdown(for candidate: Candidate, today: Date? = nil) -> [MomentumBreakdown] {
        let anchor = today ?? referenceDate
        var items: [MomentumBreakdown] = []
        if let top = declarativeOrder.first(where: { candidate.keys.contains($0) }),
           let item = weights[top] {
            items.append(item)
        }

        for key in behavioralOrder where candidate.keys.contains(key) {
            if let item = weights[key] {
                items.append(item)
            }
        }

        if let recency = recencyTerm(for: candidate.lastSignal, today: anchor) {
            items.append(recency)
        }

        for key in penaltyOrder where candidate.keys.contains(key) {
            if let item = weights[key] {
                items.append(item)
            }
        }

        return items
    }

    static func momentum(for candidate: Candidate, today: Date? = nil) -> Int {
        let total = breakdown(for: candidate, today: today).reduce(0) { $0 + $1.weight }
        return max(0, min(100, total))
    }

    static func daysSince(_ isoDate: String, today: Date? = nil) -> Int {
        let anchor = today ?? referenceDate
        let date = dateFromISO(isoDate) ?? anchor
        let calendar = Calendar(identifier: .gregorian)
        return calendar.dateComponents([.day], from: date, to: anchor).day ?? 0
    }

    static func isFresh(_ candidate: Candidate) -> Bool {
        daysSince(candidate.lastSignal) <= 7
    }

    static func isMover(_ candidate: Candidate) -> Bool {
        candidate.delta != 0 || daysSince(candidate.lastSignal) <= 14
    }

    static func recencyLabel(days: Int) -> String {
        if days <= 0 {
            return "update day"
        }
        if days == 1 {
            return "1d before update"
        }
        if days <= 45 {
            return "\(days)d before update"
        }
        return "\(Int(round(Double(days) / 30.0)))mo before update"
    }

    static func dateFromISO(_ isoDate: String) -> Date? {
        isoFormatter.date(from: String(isoDate.prefix(10)))
    }

    static func shortDate(_ date: Date) -> String {
        shortFormatter.string(from: date)
    }

    static func longDate(_ isoDate: String) -> String {
        guard let date = dateFromISO(isoDate) else { return isoDate }
        return longFormatter.string(from: date)
    }

    static func parseSource(_ headline: String) -> (title: String, source: String) {
        guard let range = headline.range(of: " - ", options: .backwards) else {
            return (headline, "Tracker note")
        }
        let title = String(headline[..<range.lowerBound])
        let source = String(headline[range.upperBound...])
        if source.count > 4 && source.count < 46 {
            return (title, source)
        }
        return (headline, "Tracker note")
    }

    private static func recencyTerm(for isoDate: String, today: Date) -> MomentumBreakdown? {
        let days = daysSince(isoDate, today: today)
        if days <= 30 {
            return MomentumBreakdown(label: "Recency boost (signal \(days)d before update)", weight: 5)
        }
        if days > 90 {
            return MomentumBreakdown(label: "Stale (no signal \(days)d)", weight: -10)
        }
        return nil
    }

    private static let isoFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()

    private static let shortFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.dateFormat = "MMM d"
        return formatter
    }()

    private static let longFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.dateStyle = .long
        formatter.timeStyle = .none
        return formatter
    }()
}
