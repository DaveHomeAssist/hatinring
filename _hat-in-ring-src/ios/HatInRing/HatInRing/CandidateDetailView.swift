import SwiftUI
import Observation

struct CandidateDetailView: View {
    let candidate: Candidate
    let store: CandidateStore
    @Bindable var state: HatInRingState

    private var status: RadarStatus { RadarScoring.status(for: candidate.keys) }
    private var score: Int { RadarScoring.momentum(for: candidate) }
    private var days: Int { RadarScoring.daysSince(candidate.lastSignal) }
    private var latestDispatch: Dispatch? {
        store.dispatches().first { $0.candidateID == candidate.id }
    }

    var body: some View {
        VStack(spacing: 0) {
            detailToolbar

            ScrollView {
                VStack(spacing: 0) {
                    hero

                    VStack(spacing: 13) {
                        rationaleSection
                        ledgerSection
                        freshnessSection
                        latestDispatchSection
                        fileSection
                        if !candidate.tags.isEmpty {
                            tagsSection
                        }
                    }
                    .padding(14)
                    .padding(.bottom, 12)
                }
            }
            .background(HIRTheme.parchment)
        }
        .background(HIRTheme.parchment.ignoresSafeArea())
        .navigationBarBackButtonHidden(true)
    }

    private var detailToolbar: some View {
        HStack {
            Button {
                state.path.removeAll()
            } label: {
                HStack(spacing: 5) {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 16, weight: .bold))
                    Text("Back")
                        .font(HIRTheme.body(14, weight: .semibold))
                }
                .foregroundStyle(HIRTheme.navy)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Back")

            Spacer()

            Button {
                state.toggleWatch(candidate.id)
            } label: {
                HStack(spacing: 5) {
                    Image(systemName: state.isWatching(candidate.id) ? "star.fill" : "star")
                    Text(state.isWatching(candidate.id) ? "Following" : "Follow")
                }
                .font(HIRTheme.body(13, weight: .semibold))
                .foregroundStyle(state.isWatching(candidate.id) ? .white : Color(hex: 0x5A5443))
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(state.isWatching(candidate.id) ? HIRTheme.accentRed : HIRTheme.paper)
                .clipShape(RoundedRectangle(cornerRadius: 9, style: .continuous))
                .overlay {
                    RoundedRectangle(cornerRadius: 9, style: .continuous)
                        .stroke(state.isWatching(candidate.id) ? HIRTheme.accentRed : Color(hex: 0xCBBFA3), lineWidth: 1)
                }
            }
            .buttonStyle(.plain)
            .accessibilityLabel(state.isWatching(candidate.id) ? "Unfollow \(candidate.name)" : "Follow \(candidate.name)")
        }
        .padding(.top, 52)
        .padding(.horizontal, 12)
        .padding(.bottom, 9)
        .background(HIRTheme.paper)
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(HIRTheme.border)
                .frame(height: 1)
        }
    }

    private var hero: some View {
        ZStack {
            HIRTheme.navyDeep

            StarField()
                .opacity(0.16)

            VStack(alignment: .leading, spacing: 15) {
                HStack(alignment: .top, spacing: 15) {
                    CandidatePortrait(candidate: candidate, width: 90, height: 112)

                    VStack(alignment: .leading, spacing: 8) {
                        HStack(spacing: 8) {
                            PartyChip(party: candidate.party, letter: candidate.partyLetter, size: 22)
                            Text(candidate.party)
                                .font(HIRTheme.body(11.5, weight: .semibold))
                                .foregroundStyle(Color(hex: 0xBACAEF))
                            StatusPill(status: status, compact: true)
                        }

                        Text(candidate.name)
                            .font(HIRTheme.display(27, weight: .semibold))
                            .foregroundStyle(HIRTheme.paperAlt)
                            .lineLimit(2)
                            .minimumScaleFactor(0.85)

                        Text(candidate.role)
                            .font(HIRTheme.body(12.5))
                            .foregroundStyle(Color(hex: 0x9DB0CE))
                            .lineLimit(2)
                    }
                    .padding(.top, 2)
                }

                HStack(alignment: .bottom, spacing: 14) {
                    MetricBlock(label: "Momentum") {
                        HStack(spacing: 8) {
                            Text("\(score)")
                                .font(HIRTheme.mono(24, weight: .bold))
                                .foregroundStyle(HIRTheme.paperAlt)
                            MomentumMeter(score: score, tier: status.tier, width: 74)
                        }
                    }

                    MetricDivider()

                    MetricBlock(label: "Confidence") {
                        HStack(spacing: 6) {
                            Circle()
                                .fill(HIRTheme.confidenceColor(candidate.confidence))
                                .frame(width: 8, height: 8)
                            Text(candidate.confidence)
                                .font(HIRTheme.body(12.5, weight: .semibold))
                                .foregroundStyle(Color(hex: 0xCDD9EE))
                        }
                    }

                    if let pollLead = candidate.pollLead, !pollLead.isEmpty {
                        MetricDivider()
                        MetricBlock(label: "Polling") {
                            HStack(spacing: 5) {
                                Image(systemName: "star.fill")
                                    .font(.system(size: 10, weight: .bold))
                                    .foregroundStyle(HIRTheme.liveRed)
                                Text(pollLead)
                                    .font(HIRTheme.body(12, weight: .semibold))
                                    .foregroundStyle(Color(hex: 0xE7B7B3))
                                    .lineLimit(2)
                            }
                        }
                    }
                }
            }
            .padding(18)
        }
    }

    private var rationaleSection: some View {
        DetailSection {
            VStack(alignment: .leading, spacing: 8) {
                SectionKicker("WHY IT'S ON THE RADAR")
                Text(candidate.why)
                    .font(HIRTheme.display(15.5, weight: .regular))
                    .foregroundStyle(Color(hex: 0x2C3A4F))
                    .lineSpacing(4)
                if !candidate.quote.isEmpty {
                    Text("\"\(candidate.quote)\"")
                        .font(HIRTheme.display(15, weight: .regular).italic())
                        .foregroundStyle(Color(hex: 0x46402F))
                        .lineSpacing(3)
                        .padding(.leading, 14)
                        .overlay(alignment: .leading) {
                            Rectangle()
                                .fill(Color(hex: 0xC9BE9E))
                                .frame(width: 3)
                        }
                        .padding(.top, 5)
                }
            }
        }
    }

    private var ledgerSection: some View {
        DetailSection(padding: 0) {
            VStack(spacing: 0) {
                HStack(alignment: .firstTextBaseline) {
                    Text("Momentum ledger")
                        .font(HIRTheme.display(15, weight: .semibold))
                        .foregroundStyle(HIRTheme.navy)
                    Spacer()
                    Text("how the score builds")
                        .font(HIRTheme.body(10.5))
                        .foregroundStyle(Color(hex: 0x8A8470))
                }
                .padding(.horizontal, 16)
                .padding(.top, 13)
                .padding(.bottom, 7)

                VStack(spacing: 0) {
                    ForEach(RadarScoring.breakdown(for: candidate)) { item in
                        HStack(spacing: 12) {
                            Text(item.label)
                                .font(HIRTheme.body(12.5))
                                .foregroundStyle(Color(hex: 0x3C3A30))
                            Spacer()
                            Text(item.weight >= 0 ? "+\(item.weight)" : "\(item.weight)")
                                .font(HIRTheme.mono(12.5, weight: .bold))
                                .foregroundStyle(item.weight >= 0 ? Color(hex: 0x2E7D4F) : HIRTheme.accentRed)
                        }
                        .padding(.vertical, 7)
                        .overlay(alignment: .bottom) {
                            DashedSeparator()
                        }
                    }

                    HStack {
                        Text("Momentum (0 to 100)")
                            .font(HIRTheme.body(13, weight: .bold))
                            .foregroundStyle(HIRTheme.navy)
                        Spacer()
                        Text("\(score)")
                            .font(HIRTheme.mono(17, weight: .bold))
                            .foregroundStyle(HIRTheme.statusColor(status.tier))
                    }
                    .padding(.top, 10)
                    .overlay(alignment: .top) {
                        Rectangle()
                            .fill(HIRTheme.navy)
                            .frame(height: 2)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 14)
            }
        }
    }

    private var latestDispatchSection: some View {
        DetailSection {
            VStack(alignment: .leading, spacing: 10) {
                SectionKicker("LATEST DISPATCH")
                if let latestDispatch {
                    HStack(alignment: .top, spacing: 11) {
                        Text(store.freshness.recencyLabel(days: days))
                            .font(HIRTheme.mono(10.5, weight: .bold))
                            .foregroundStyle(HIRTheme.accentRed)
                            .padding(.top, 3)
                        VStack(alignment: .leading, spacing: 5) {
                            Text(latestDispatch.title)
                                .font(HIRTheme.display(15.5, weight: .regular))
                                .foregroundStyle(Color(hex: 0x1B2942))
                                .lineSpacing(3)
                            Text("\(RadarScoring.longDate(candidate.lastSignal)) - \(latestDispatch.source)")
                                .font(HIRTheme.body(11))
                                .foregroundStyle(HIRTheme.softText)
                        }
                    }

                    Button {
                        state.selectTab(.wire)
                    } label: {
                        Text("See all dispatches on The Wire")
                            .font(HIRTheme.body(12, weight: .semibold))
                            .foregroundStyle(HIRTheme.paperAlt)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                            .background(HIRTheme.navy)
                            .clipShape(RoundedRectangle(cornerRadius: 9, style: .continuous))
                    }
                    .buttonStyle(.plain)
                    .padding(.top, 3)
                }
            }
        }
    }

    private var fileSection: some View {
        DetailSection(padding: 0) {
            VStack(alignment: .leading, spacing: 0) {
                Text("The file")
                    .font(HIRTheme.display(15, weight: .semibold))
                    .foregroundStyle(HIRTheme.navy)
                    .padding(.horizontal, 16)
                    .padding(.top, 13)
                    .padding(.bottom, 4)

                VStack(spacing: 0) {
                    DetailFact(label: "Lane", value: candidate.party)
                    DetailFact(label: "Office / role", value: candidate.role)
                    DetailFact(label: "Posture", value: candidate.bucketLabel)
                    DetailFact(label: "Last signal", value: "\(RadarScoring.longDate(candidate.lastSignal)) - \(store.freshness.recencyLabel(days: days))")
                    DetailFact(label: "Confidence", value: candidate.confidence)
                    DetailFact(label: "Poll standing", value: candidate.pollLead ?? "-")
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 8)
            }
        }
    }

    private var tagsSection: some View {
        DetailSection {
            VStack(alignment: .leading, spacing: 9) {
                Text("TAGS")
                    .font(HIRTheme.body(9.5, weight: .bold))
                    .tracking(1)
                    .foregroundStyle(Color(hex: 0x9A917A))
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 84), spacing: 6)], alignment: .leading, spacing: 6) {
                    ForEach(candidate.tags, id: \.self) { tag in
                        SignalTag(text: tag)
                    }
                }
            }
        }
    }

    private var freshnessSection: some View {
        DetailSection {
            VStack(alignment: .leading, spacing: 8) {
                SectionKicker("DATA MODE")
                Text(store.freshness.summary)
                    .font(HIRTheme.display(15.5, weight: .semibold))
                    .foregroundStyle(HIRTheme.navy)
                Text("Scored against update date: \(store.freshness.snapshotDateText)")
                    .font(HIRTheme.body(12))
                    .foregroundStyle(HIRTheme.softText)
            }
        }
    }
}

private struct DetailSection<Content: View>: View {
    var padding: CGFloat = 15
    let content: Content

    init(padding: CGFloat = 15, @ViewBuilder content: () -> Content) {
        self.padding = padding
        self.content = content()
    }

    var body: some View {
        content
            .padding(padding)
            .background(HIRTheme.paper)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(HIRTheme.border, lineWidth: 1)
            }
    }
}

private struct SectionKicker: View {
    let text: String

    init(_ text: String) {
        self.text = text
    }

    var body: some View {
        Text(text)
            .font(HIRTheme.body(10, weight: .bold))
            .tracking(1)
            .foregroundStyle(HIRTheme.accentRed)
    }
}

private struct MetricBlock<Content: View>: View {
    let label: String
    let content: Content

    init(label: String, @ViewBuilder content: () -> Content) {
        self.label = label
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(label.uppercased())
                .font(HIRTheme.body(9, weight: .bold))
                .tracking(1.2)
                .foregroundStyle(Color(hex: 0x7E92B2))
            content
        }
        .frame(minWidth: 0, alignment: .leading)
    }
}

private struct MetricDivider: View {
    var body: some View {
        Rectangle()
            .fill(Color(hex: 0x2C476B))
            .frame(width: 1, height: 30)
    }
}

private struct DetailFact: View {
    let label: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label.uppercased())
                .font(HIRTheme.body(9.5, weight: .semibold))
                .tracking(0.6)
                .foregroundStyle(Color(hex: 0x9A917A))
            Text(value)
                .font(HIRTheme.body(13, weight: .medium))
                .foregroundStyle(Color(hex: 0x2C3A4F))
                .lineLimit(3)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.vertical, 8)
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(Color(hex: 0xECE4D2))
                .frame(height: 1)
        }
    }
}

private struct DashedSeparator: View {
    var body: some View {
        GeometryReader { proxy in
            Path { path in
                path.move(to: .zero)
                path.addLine(to: CGPoint(x: proxy.size.width, y: 0))
            }
            .stroke(Color(hex: 0xE4DBC6), style: StrokeStyle(lineWidth: 1, dash: [4, 4]))
        }
        .frame(height: 1)
    }
}

private struct StarField: View {
    private let points: [CGPoint] = [
        CGPoint(x: 0.84, y: 0.16),
        CGPoint(x: 0.93, y: 0.38),
        CGPoint(x: 0.76, y: 0.54),
        CGPoint(x: 0.88, y: 0.70),
        CGPoint(x: 0.66, y: 0.28)
    ]

    var body: some View {
        GeometryReader { proxy in
            ZStack {
                ForEach(points.indices, id: \.self) { index in
                    Circle()
                        .fill(.white)
                        .frame(width: 3, height: 3)
                        .position(
                            x: proxy.size.width * points[index].x,
                            y: proxy.size.height * points[index].y
                        )
                }
            }
        }
    }
}
