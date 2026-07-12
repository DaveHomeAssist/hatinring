import SwiftUI
import UIKit
import Observation

struct ScreenHeader<Accessory: View>: View {
    let title: String
    let subtitle: String
    let accessory: Accessory

    init(title: String, subtitle: String, @ViewBuilder accessory: () -> Accessory) {
        self.title = title
        self.subtitle = subtitle
        self.accessory = accessory()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 3) {
                    Text("Hat-in-Ring")
                        .font(HIRTheme.display(22, weight: .medium))
                        .foregroundStyle(HIRTheme.navy)
                    Text("RADAR")
                        .font(HIRTheme.body(8, weight: .bold))
                        .tracking(3)
                        .foregroundStyle(HIRTheme.accentRed)
                }

                Spacer()

                accessory
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(HIRTheme.display(31, weight: .semibold))
                    .foregroundStyle(HIRTheme.navy)
                    .lineLimit(1)
                    .minimumScaleFactor(0.85)
                Text(subtitle)
                    .font(HIRTheme.body(11.5))
                    .foregroundStyle(HIRTheme.mutedText)
            }
        }
        .padding(.top, 52)
        .padding(.horizontal, 16)
        .padding(.bottom, 12)
        .background(HIRTheme.paper)
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(HIRTheme.border)
                .frame(height: 1)
        }
    }
}

extension ScreenHeader where Accessory == EmptyView {
    init(title: String, subtitle: String) {
        self.init(title: title, subtitle: subtitle) { EmptyView() }
    }
}

struct HIRCard<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        content
            .background(HIRTheme.paper)
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(HIRTheme.border, lineWidth: 1)
            }
    }
}

struct CandidatePortrait: View {
    let candidate: Candidate
    let width: CGFloat
    let height: CGFloat
    var cornerRadius: CGFloat = 8

    var body: some View {
        Group {
            if let image = BundleResourceImage.image(path: candidate.imagePath) {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFill()
            } else {
                ZStack {
                    HIRTheme.segmentFill
                    Text(candidate.partyLetter)
                        .font(HIRTheme.display(18, weight: .bold))
                        .foregroundStyle(HIRTheme.navy)
                }
            }
        }
        .frame(width: width, height: height)
        .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .stroke(Color(hex: 0xDDD3BB), lineWidth: 1)
        }
        .accessibilityLabel("\(candidate.name) portrait")
    }
}

enum BundleResourceImage {
    static func image(path: String) -> UIImage? {
        guard let root = Bundle.main.resourceURL else { return nil }
        let resourceURL = root.appendingPathComponent("HatInRingData").appendingPathComponent(path)
        if FileManager.default.fileExists(atPath: resourceURL.path) {
            return UIImage(contentsOfFile: resourceURL.path)
        }
        let fallbackURL = root.appendingPathComponent(path)
        if FileManager.default.fileExists(atPath: fallbackURL.path) {
            return UIImage(contentsOfFile: fallbackURL.path)
        }
        return nil
    }
}

struct StatusPill: View {
    let status: RadarStatus
    var compact = false

    var body: some View {
        Text(status.label)
            .font(HIRTheme.body(compact ? 9.5 : 10, weight: .semibold))
            .foregroundStyle(.white)
            .lineLimit(1)
            .padding(.horizontal, compact ? 7 : 8)
            .padding(.vertical, compact ? 2 : 3)
            .background(HIRTheme.statusColor(status.tier))
            .clipShape(RoundedRectangle(cornerRadius: 4, style: .continuous))
            .accessibilityLabel("Status \(status.label)")
    }
}

struct PartyChip: View {
    let party: String
    let letter: String
    var size: CGFloat = 18

    var body: some View {
        Text(letter)
            .font(HIRTheme.body(size >= 20 ? 11 : 10, weight: .bold))
            .foregroundStyle(.white)
            .frame(width: size, height: size)
            .background(HIRTheme.partyColor(party))
            .clipShape(RoundedRectangle(cornerRadius: 3, style: .continuous))
            .accessibilityLabel("\(party) lane")
    }
}

struct MomentumMeter: View {
    let score: Int
    let tier: Int
    var width: CGFloat = 48

    var body: some View {
        GeometryReader { proxy in
            let fillWidth = max(0, min(proxy.size.width, proxy.size.width * CGFloat(score) / 100.0))
            ZStack(alignment: .leading) {
                Capsule().fill(Color(hex: 0xE7DEC9))
                Capsule()
                    .fill(HIRTheme.statusColor(tier))
                    .frame(width: fillWidth)
            }
        }
        .frame(width: width, height: 5)
        .accessibilityLabel("Momentum \(score)")
    }
}

struct LiveDot: View {
    var body: some View {
        Circle()
            .fill(HIRTheme.liveRed)
            .frame(width: 7, height: 7)
            .shadow(color: HIRTheme.liveRed.opacity(0.65), radius: 4)
            .accessibilityHidden(true)
    }
}

struct RadarBadge: View {
    var body: some View {
        ZStack {
            Circle()
                .fill(HIRTheme.navyDeep)
            Circle()
                .stroke(Color(hex: 0x2C476B), lineWidth: 1.2)
                .padding(10)
            Circle()
                .stroke(Color(hex: 0x2C476B), lineWidth: 1.2)
                .padding(21)
            Rectangle()
                .fill(Color(hex: 0x243F63))
                .frame(width: 1.2, height: 55)
            Rectangle()
                .fill(Color(hex: 0x243F63))
                .frame(width: 55, height: 1.2)
            Circle()
                .fill(HIRTheme.liveRed)
                .frame(width: 6, height: 6)
                .offset(x: 14, y: -14)
                .shadow(color: HIRTheme.liveRed.opacity(0.8), radius: 5)
        }
        .frame(width: 58, height: 58)
        .accessibilityLabel("Radar status mark")
    }
}

struct FreshnessBadge: View {
    let freshness: DataFreshness

    var body: some View {
        VStack(alignment: .trailing, spacing: 5) {
            Text(freshness.statusLabel)
                .font(HIRTheme.body(9, weight: .bold))
                .tracking(1.4)
                .foregroundStyle(HIRTheme.accentRed)
            Text(freshness.snapshotDateText)
                .font(HIRTheme.display(13, weight: .semibold))
                .foregroundStyle(HIRTheme.navy)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(freshness.statusLabel), \(freshness.snapshotDateText)")
    }
}

struct FreshnessBanner: View {
    let freshness: DataFreshness

    var body: some View {
        HStack(alignment: .top, spacing: 9) {
            Image(systemName: "archivebox")
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(HIRTheme.accentRed)
                .frame(width: 18, height: 18)
            VStack(alignment: .leading, spacing: 2) {
                Text(freshness.summary)
                    .font(HIRTheme.body(12, weight: .semibold))
                    .foregroundStyle(HIRTheme.navy)
                Text(freshness.detail)
                    .font(HIRTheme.body(10.5))
                    .foregroundStyle(HIRTheme.softText)
                    .lineLimit(2)
            }
            Spacer(minLength: 0)
        }
        .padding(12)
        .background(HIRTheme.paper)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(HIRTheme.border, lineWidth: 1)
        }
        .accessibilityElement(children: .combine)
    }
}

struct FieldSegmentedControl: View {
    @Binding var selection: FieldFilter

    var body: some View {
        HStack(spacing: 3) {
            ForEach(FieldFilter.allCases) { filter in
                Button {
                    selection = filter
                } label: {
                    Text(filter.label)
                        .font(HIRTheme.body(12, weight: .semibold))
                        .foregroundStyle(selection == filter ? HIRTheme.navy : HIRTheme.softText)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 7)
                        .background(selection == filter ? HIRTheme.paper : Color.clear)
                        .clipShape(RoundedRectangle(cornerRadius: 7, style: .continuous))
                        .shadow(color: selection == filter ? HIRTheme.navy.opacity(0.14) : .clear, radius: 2, y: 1)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Filter \(filter.label)")
            }
        }
        .padding(3)
        .background(HIRTheme.segmentFill)
        .clipShape(RoundedRectangle(cornerRadius: 9, style: .continuous))
    }
}

struct HIRSearchField: View {
    let placeholder: String
    @Binding var text: String

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(Color(hex: 0xA39A82))
            TextField(placeholder, text: $text)
                .font(HIRTheme.body(14))
                .foregroundStyle(HIRTheme.navy)
                .textInputAutocapitalization(.words)
                .disableAutocorrection(false)
                .accessibilityIdentifier(placeholder)
            if !text.isEmpty {
                Button {
                    text = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundStyle(Color(hex: 0xA39A82))
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Clear search")
                .accessibilityIdentifier("clear-\(placeholder)")
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(Color(hex: 0xF1EADB))
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
        .overlay {
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .stroke(Color(hex: 0xDDD3BB), lineWidth: 1)
        }
        .accessibilityLabel(placeholder)
        .accessibilityIdentifier(placeholder)
    }
}

struct CandidateListRow: View {
    let candidate: Candidate
    let rank: Int?
    let isWatching: Bool

    private var status: RadarStatus {
        RadarScoring.status(for: candidate.keys)
    }

    private var score: Int {
        RadarScoring.momentum(for: candidate)
    }

    var body: some View {
        HStack(spacing: 11) {
            if let rank {
                Text("\(rank)")
                    .font(HIRTheme.mono(11))
                    .foregroundStyle(Color(hex: 0xA99F86))
                    .frame(width: 18, alignment: .trailing)
            }

            CandidatePortrait(candidate: candidate, width: 44, height: 52)

            VStack(alignment: .leading, spacing: 5) {
                HStack(spacing: 6) {
                    Text(candidate.name)
                        .font(HIRTheme.display(15.5, weight: .semibold))
                        .foregroundStyle(HIRTheme.navy)
                        .lineLimit(1)
                    if RadarScoring.isFresh(candidate) {
                        LiveDot()
                            .frame(width: 6, height: 6)
                    }
                    if isWatching {
                        Image(systemName: "star.fill")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundStyle(HIRTheme.accentRed)
                    }
                }

                Text(candidate.role)
                    .font(HIRTheme.body(11))
                    .foregroundStyle(HIRTheme.softText)
                    .lineLimit(1)

                HStack(spacing: 6) {
                    StatusPill(status: status, compact: true)
                    PartyChip(party: candidate.party, letter: candidate.partyLetter, size: 17)
                }
            }

            Spacer(minLength: 8)

            VStack(alignment: .trailing, spacing: 6) {
                Text("\(score)")
                    .font(HIRTheme.mono(18, weight: .bold))
                    .foregroundStyle(HIRTheme.statusColor(status.tier))
                MomentumMeter(score: score, tier: status.tier, width: 42)
            }
        }
        .padding(.horizontal, 13)
        .padding(.vertical, 10)
        .contentShape(Rectangle())
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(candidate.name), \(candidate.role), \(status.label), momentum \(score)")
    }
}

struct DossierRow: View {
    let candidate: Candidate
    let isWatching: Bool

    private var status: RadarStatus { RadarScoring.status(for: candidate.keys) }
    private var score: Int { RadarScoring.momentum(for: candidate) }

    var body: some View {
        HStack(spacing: 11) {
            CandidatePortrait(candidate: candidate, width: 40, height: 46, cornerRadius: 7)
            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 4) {
                    Text(candidate.name)
                        .font(HIRTheme.display(15, weight: .semibold))
                        .foregroundStyle(HIRTheme.navy)
                        .lineLimit(1)
                    if isWatching {
                        Image(systemName: "star.fill")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundStyle(HIRTheme.accentRed)
                    }
                }
                Text(candidate.role)
                    .font(HIRTheme.body(11))
                    .foregroundStyle(HIRTheme.softText)
                    .lineLimit(1)
            }
            Spacer()
            Circle()
                .fill(HIRTheme.statusColor(status.tier))
                .frame(width: 9, height: 9)
            Text("\(score)")
                .font(HIRTheme.mono(14, weight: .bold))
                .foregroundStyle(HIRTheme.statusColor(status.tier))
                .frame(width: 28, alignment: .trailing)
            Image(systemName: "chevron.right")
                .font(.system(size: 11, weight: .semibold))
                .foregroundStyle(Color(hex: 0xC7BDA3))
        }
        .padding(.horizontal, 13)
        .padding(.vertical, 9)
        .contentShape(Rectangle())
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(candidate.name), momentum \(score), \(status.label)")
    }
}

struct DispatchCard: View {
    let dispatch: Dispatch
    let candidate: Candidate
    let freshness: DataFreshness
    var isLead = false

    var body: some View {
        HIRCard {
            HStack(alignment: .top, spacing: isLead ? 13 : 10) {
                if isLead {
                    CandidatePortrait(candidate: candidate, width: 62, height: 76)
                }

                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 8) {
                        Text(isLead ? "\(freshness.statusLabel) \(freshness.recencyLabel(days: dispatch.days))" : RadarScoring.shortDate(dispatch.date))
                            .font(HIRTheme.mono(11, weight: .bold))
                            .foregroundStyle(dispatch.days <= 7 ? HIRTheme.accentRed : Color(hex: 0x9A917A))
                            .lineLimit(1)
                        PartyChip(party: candidate.party, letter: candidate.partyLetter, size: 18)
                        Text(candidate.name)
                            .font(HIRTheme.body(12.5, weight: .bold))
                            .foregroundStyle(HIRTheme.navy)
                            .lineLimit(1)
                    }

                    Text(dispatch.title)
                        .font(HIRTheme.display(isLead ? 18 : 15, weight: .semibold))
                        .foregroundStyle(Color(hex: 0x1B2942))
                        .lineLimit(isLead ? 4 : 3)

                    HStack(spacing: 7) {
                        Text(dispatch.source)
                            .font(HIRTheme.body(10.5, weight: .semibold))
                            .foregroundStyle(HIRTheme.softText)
                        ForEach(dispatch.tags, id: \.self) { tag in
                            SignalTag(text: tag)
                        }
                    }

                    if let sourceURL = dispatch.sourceURL {
                        Link(destination: sourceURL) {
                            Label("Source", systemImage: "arrow.up.right.square")
                                .font(HIRTheme.body(10.5, weight: .semibold))
                        }
                        .accessibilityIdentifier("dispatch-source-\(candidate.id)")
                    }
                }
            }
            .padding(isLead ? 14 : 12)
        }
        .overlay(alignment: .top) {
            if isLead {
                Rectangle()
                    .fill(HIRTheme.liveRed)
                    .frame(height: 3)
                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(candidate.name), \(dispatch.title), \(dispatch.source)")
    }
}

struct MenuChip<Selection: Hashable & Identifiable & CaseIterable>: View where Selection.AllCases: RandomAccessCollection, Selection.AllCases.Element == Selection {
    let title: String
    @Binding var selection: Selection
    let label: (Selection) -> String

    var body: some View {
        Menu {
            Picker(title, selection: $selection) {
                ForEach(Selection.allCases) { option in
                    Text(label(option)).tag(option)
                }
            }
        } label: {
            HStack(spacing: 5) {
                Text(label(selection))
                    .lineLimit(1)
                Image(systemName: "chevron.down")
                    .font(.system(size: 9, weight: .bold))
            }
            .font(HIRTheme.body(11.5, weight: .semibold))
            .foregroundStyle(HIRTheme.navy)
            .padding(.horizontal, 10)
            .padding(.vertical, 7)
            .background(HIRTheme.paper)
            .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 8, style: .continuous)
                    .stroke(HIRTheme.border, lineWidth: 1)
            }
        }
        .accessibilityLabel(title)
    }
}

struct SettingsSection<Content: View>: View {
    let title: String
    let content: Content

    init(title: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.content = content()
    }

    var body: some View {
        HIRCard {
            VStack(alignment: .leading, spacing: 12) {
                Text(title.uppercased())
                    .font(HIRTheme.body(9.5, weight: .bold))
                    .tracking(1)
                    .foregroundStyle(HIRTheme.accentRed)
                content
            }
            .padding(14)
        }
    }
}

struct SettingsActionRow<Icon: View, Trailing: View>: View {
    let title: String
    let subtitle: String
    let icon: Icon
    let trailing: Trailing

    init(
        title: String,
        subtitle: String,
        @ViewBuilder icon: () -> Icon,
        @ViewBuilder trailing: () -> Trailing
    ) {
        self.title = title
        self.subtitle = subtitle
        self.icon = icon()
        self.trailing = trailing()
    }

    var body: some View {
        HStack(alignment: .center, spacing: 12) {
            icon
                .frame(width: 25, height: 25)
                .foregroundStyle(HIRTheme.navy)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(HIRTheme.body(13, weight: .semibold))
                    .foregroundStyle(HIRTheme.navy)
                Text(subtitle)
                    .font(HIRTheme.body(11))
                    .foregroundStyle(HIRTheme.softText)
                    .lineLimit(2)
            }
            Spacer(minLength: 8)
            trailing
        }
    }
}

struct SignalTag: View {
    let text: String

    var body: some View {
        Text(text)
            .font(HIRTheme.body(9.5, weight: .semibold))
            .foregroundStyle(Color(hex: 0x6A6450))
            .lineLimit(1)
            .padding(.horizontal, 7)
            .padding(.vertical, 2)
            .background(HIRTheme.chipFill)
            .clipShape(RoundedRectangle(cornerRadius: 3, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 3, style: .continuous)
                    .stroke(Color(hex: 0xE0D7C1), lineWidth: 1)
            }
    }
}

struct EmptyState: View {
    let symbol: String
    let title: String
    let message: String
    var actionTitle: String?
    var action: (() -> Void)?

    var body: some View {
        VStack(spacing: 10) {
            Image(systemName: symbol)
                .font(.system(size: 42, weight: .light))
                .foregroundStyle(Color(hex: 0xC7BDA3))
                .padding(.bottom, 4)
            Text(title)
                .font(HIRTheme.display(19, weight: .medium))
                .foregroundStyle(Color(hex: 0x3C3A30))
            Text(message)
                .font(HIRTheme.body(12.5))
                .foregroundStyle(HIRTheme.softText)
                .multilineTextAlignment(.center)
                .lineSpacing(3)
                .frame(maxWidth: 260)

            if let actionTitle, let action {
                Button(action: action) {
                    Text(actionTitle)
                        .font(HIRTheme.body(13, weight: .semibold))
                        .foregroundStyle(HIRTheme.paperAlt)
                        .padding(.horizontal, 18)
                        .padding(.vertical, 10)
                        .background(HIRTheme.navy)
                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                }
                .buttonStyle(.plain)
                .padding(.top, 8)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.horizontal, 26)
        .padding(.top, 40)
    }
}

struct CustomTabBar: View {
    @Bindable var state: HatInRingState
    let hasFreshWire: Bool

    var body: some View {
        HStack(spacing: 0) {
            ForEach(AppTab.allCases) { tab in
                Button {
                    state.selectTab(tab)
                } label: {
                    VStack(spacing: 3) {
                        ZStack(alignment: .topTrailing) {
                            Image(systemName: tab.symbol)
                                .font(.system(size: 22, weight: .regular))
                                .frame(width: 32, height: 25)
                            if tab == .wire && hasFreshWire {
                                LiveDot()
                                    .frame(width: 6, height: 6)
                                    .offset(x: 2, y: 0)
                            }
                        }
                        Text(tab.label)
                            .font(HIRTheme.body(10, weight: .semibold))
                            .lineLimit(1)
                            .minimumScaleFactor(0.8)
                    }
                    .foregroundStyle(state.selectedTab == tab ? HIRTheme.navy : Color(hex: 0x9A9684))
                    .frame(maxWidth: .infinity)
                    .padding(.top, 8)
                    .padding(.bottom, 18)
                    .frame(maxWidth: .infinity, minHeight: 66)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel(tab.label)
                .accessibilityIdentifier("tab-\(tab.rawValue)")
                .accessibilityAddTraits(state.selectedTab == tab ? [.isSelected] : [])
            }
        }
        .background(HIRTheme.paperAlt)
        .overlay(alignment: .top) {
            Rectangle()
                .fill(HIRTheme.borderStrong)
                .frame(height: 1)
        }
    }
}
