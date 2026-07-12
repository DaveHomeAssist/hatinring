import SwiftUI
import Observation

struct FieldView: View {
    let store: CandidateStore
    @Bindable var state: HatInRingState

    var body: some View {
        let moverCount = store.candidates.filter { RadarScoring.isMover($0) }.count
        let rows = store.fieldCandidates(
            filter: state.fieldFilter,
            party: state.fieldPartyFilter,
            confidence: state.fieldConfidenceFilter,
            sort: state.fieldSort
        )
        let recentCandidate = state.recentCandidateID.flatMap(store.candidate)

        VStack(spacing: 0) {
            ScreenHeader(
                title: "The Field",
                subtitle: store.freshness.movementSubtitle(moverCount: moverCount)
            ) {
                VStack(alignment: .trailing, spacing: 12) {
                    FreshnessBadge(freshness: store.freshness)
                    RadarBadge()
                }
            }

            VStack(spacing: 10) {
                FieldSegmentedControl(selection: $state.fieldFilter)
                FieldFilterControls(state: state)
            }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(HIRTheme.paper)
                .overlay(alignment: .bottom) {
                    Rectangle()
                        .fill(HIRTheme.border)
                        .frame(height: 1)
                }

            ScrollView {
                LazyVStack(spacing: 12) {
                    FreshnessBanner(freshness: store.freshness)

                    if let recentCandidate {
                        ContinueDossierBanner(candidate: recentCandidate) {
                            state.openCandidate(recentCandidate.id)
                        }
                    }

                    if rows.isEmpty {
                        EmptyState(
                            symbol: "line.3.horizontal.decrease.circle",
                            title: "No field matches",
                            message: "Clear one filter or switch back to All lanes."
                        )
                    } else {
                        CandidateRowsCard(
                            rows: rows,
                            state: state,
                            showRank: state.fieldSort == .momentum
                        )
                    }

                    Text("Momentum = breadth and recency of activity. Status = furthest verifiable step. Status is not support.")
                        .font(HIRTheme.mono(10))
                        .foregroundStyle(Color(hex: 0xA99F86))
                        .multilineTextAlignment(.center)
                        .lineSpacing(3)
                        .padding(.horizontal, 24)
                }
                .padding(12)
                .padding(.bottom, 6)
            }
            .background(HIRTheme.parchment)
        }
    }
}

struct WireView: View {
    let store: CandidateStore
    @Bindable var state: HatInRingState

    var body: some View {
        let dispatches = store.dispatches(party: state.wirePartyFilter)

        VStack(spacing: 0) {
            BasicTopHeader(title: "The Wire", subtitle: store.freshness.wireSubtitle(dispatchCount: dispatches.count)) {
                FreshnessBadge(freshness: store.freshness)
            }

            HStack {
                MenuChip(title: "Wire lane", selection: $state.wirePartyFilter) { $0.label }
                Spacer()
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(HIRTheme.paper)
            .overlay(alignment: .bottom) {
                Rectangle()
                    .fill(HIRTheme.border)
                    .frame(height: 1)
            }

            ScrollView {
                LazyVStack(spacing: 10) {
                    FreshnessBanner(freshness: store.freshness)

                    if dispatches.isEmpty {
                        EmptyState(
                            symbol: "dot.radiowaves.left.and.right",
                            title: "No dispatches match",
                            message: "Change the lane filter to see more updated dispatches."
                        )
                    }

                    if let lead = dispatches.first,
                       let candidate = store.candidate(id: lead.candidateID) {
                        Button {
                            state.openCandidate(candidate.id)
                        } label: {
                            DispatchCard(dispatch: lead, candidate: candidate, freshness: store.freshness, isLead: true)
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("Open updated dispatch for \(candidate.name)")
                    }

                    ForEach(Array(dispatches.dropFirst())) { dispatch in
                        if let candidate = store.candidate(id: dispatch.candidateID) {
                            Button {
                                state.openCandidate(candidate.id)
                            } label: {
                                DispatchCard(dispatch: dispatch, candidate: candidate, freshness: store.freshness)
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel("Open dispatch for \(candidate.name)")
                        }
                    }
                }
                .padding(12)
                .padding(.bottom, 6)
            }
            .background(HIRTheme.parchment)
        }
    }
}

struct DossiersView: View {
    let store: CandidateStore
    @Bindable var state: HatInRingState

    var body: some View {
        let rows = store.dossierCandidates(query: state.dossierQuery)
        let pendingCount = store.pendingReviewItems(decisions: state.reviewDecisions).count

        VStack(spacing: 0) {
            VStack(alignment: .leading, spacing: 11) {
                Text("Dossiers")
                    .font(HIRTheme.display(31, weight: .semibold))
                    .foregroundStyle(HIRTheme.navy)
                    .lineLimit(1)

                Text(state.dossierMode == .files ? "All \(store.candidates.count) tracked figures sorted by momentum" : "\(pendingCount) review items need a decision")
                    .font(HIRTheme.body(11.5))
                    .foregroundStyle(HIRTheme.mutedText)

                DossierModeControl(selection: $state.dossierMode)

                if state.dossierMode == .files {
                    HIRSearchField(placeholder: "Find a name or office...", text: $state.dossierQuery)
                }
            }
            .padding(.top, 52)
            .padding(.horizontal, 16)
            .padding(.bottom, 11)
            .background(HIRTheme.paper)
            .overlay(alignment: .bottom) {
                Rectangle()
                    .fill(HIRTheme.border)
                    .frame(height: 1)
            }

            ScrollView {
                LazyVStack(spacing: 0) {
                    if state.dossierMode == .review {
                        ReviewInboxView(store: store, state: state)
                    } else {
                        if rows.isEmpty {
                            EmptyState(
                                symbol: "folder",
                                title: "No dossiers match",
                                message: "Try a name, office, party, or signal tag."
                            )
                        } else {
                            HIRCard {
                                VStack(spacing: 0) {
                                    ForEach(rows) { candidate in
                                        Button {
                                            state.openCandidate(candidate.id)
                                        } label: {
                                            DossierRow(candidate: candidate, isWatching: state.isWatching(candidate.id))
                                        }
                                        .buttonStyle(.plain)

                                        if candidate.id != rows.last?.id {
                                            Divider()
                                                .background(Color(hex: 0xEFE7D4))
                                                .padding(.leading, 64)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                .padding(12)
                .padding(.bottom, 6)
            }
            .background(HIRTheme.parchment)
        }
    }
}

struct SearchScreen: View {
    let store: CandidateStore
    @Bindable var state: HatInRingState

    var body: some View {
        let clean = state.searchQuery.trimmingCharacters(in: .whitespacesAndNewlines)
        let rows = store.searchCandidates(query: state.searchQuery)
        let suggestions = Array(store.candidates.sortedByMomentum().prefix(6))

        VStack(spacing: 0) {
            VStack(spacing: 0) {
                HIRSearchField(placeholder: "Search names, offices, signals...", text: $state.searchQuery)
                    .padding(.top, 52)
                    .padding(.horizontal, 12)
                    .padding(.bottom, 11)
            }
            .background(HIRTheme.paper)
            .overlay(alignment: .bottom) {
                Rectangle()
                    .fill(HIRTheme.border)
                    .frame(height: 1)
            }

            ScrollView {
                LazyVStack(spacing: 12) {
                    if clean.isEmpty {
                        VStack(spacing: 16) {
                            RadarBadge()
                            VStack(spacing: 4) {
                                Text("Search the field")
                                    .font(HIRTheme.display(18, weight: .medium))
                                    .foregroundStyle(Color(hex: 0x3C3A30))
                                Text("Find any tracked figure by name, office, or what they said.")
                                    .font(HIRTheme.body(12.5))
                                    .foregroundStyle(HIRTheme.softText)
                                    .multilineTextAlignment(.center)
                                    .lineSpacing(3)
                                    .frame(maxWidth: 240)
                            }

                            FlexibleChips(candidates: suggestions) { candidate in
                                state.searchQuery = candidate.name
                            }
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.top, 26)
                    } else if rows.isEmpty {
                        VStack(spacing: 18) {
                            EmptyState(
                                symbol: "magnifyingglass",
                                title: "No figures match",
                                message: "No tracked candidate matches \"\(clean)\"."
                            )
                            FlexibleChips(candidates: suggestions) { candidate in
                                state.searchQuery = candidate.name
                            }
                        }
                    } else {
                        CandidateRowsCard(rows: rows, state: state, showRank: false)
                    }
                }
                .padding(12)
                .padding(.bottom, 6)
            }
            .background(HIRTheme.parchment)
        }
    }
}

struct PicksView: View {
    let store: CandidateStore
    @Bindable var state: HatInRingState

    var body: some View {
        let rows = store.watchedCandidates(ids: state.watchedCandidateIDs)

        VStack(spacing: 0) {
            BasicTopHeader(title: "My Picks", subtitle: subtitle(for: rows)) {
                if !rows.isEmpty {
                    Text("\(rows.count)")
                        .font(HIRTheme.mono(15, weight: .bold))
                        .foregroundStyle(HIRTheme.accentRed)
                        .padding(.horizontal, 9)
                        .padding(.vertical, 3)
                        .background(Color(hex: 0xF3E7E5))
                        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
                }
            }

            ScrollView {
                if rows.isEmpty {
                    EmptyState(
                        symbol: "star",
                        title: "No picks yet",
                        message: "Open any dossier and tap the star to track a candidate. Their movement shows up here.",
                        actionTitle: "Browse the field"
                    ) {
                        state.selectTab(.field)
                    }
                } else {
                    HIRCard {
                        VStack(spacing: 0) {
                            ForEach(rows) { candidate in
                                HStack(spacing: 0) {
                                    Button {
                                        state.openCandidate(candidate.id)
                                    } label: {
                                        CandidateListRow(candidate: candidate, rank: nil, isWatching: true)
                                    }
                                    .buttonStyle(.plain)
                                    .accessibilityIdentifier("candidate-row-\(candidate.id)")

                                    Button {
                                        state.toggleWatch(candidate.id)
                                    } label: {
                                        Image(systemName: "star.fill")
                                            .font(.system(size: 17, weight: .semibold))
                                            .foregroundStyle(HIRTheme.accentRed)
                                            .frame(width: 44, height: 44)
                                    }
                                    .buttonStyle(.plain)
                                    .accessibilityLabel("Stop tracking \(candidate.name)")
                                    .padding(.trailing, 6)
                                }

                                if candidate.id != rows.last?.id {
                                    Divider()
                                        .background(Color(hex: 0xEFE7D4))
                                        .padding(.leading, 68)
                                }
                            }
                        }
                    }
                    .padding(12)
                }
            }
            .background(HIRTheme.parchment)
        }
    }

    private func subtitle(for rows: [Candidate]) -> String {
        guard !rows.isEmpty else { return "Nobody on your list yet" }
        let fresh = rows.filter(RadarScoring.isFresh).count
        let noun = rows.count == 1 ? "candidate" : "candidates"
        return "Tracking \(rows.count) \(noun), \(fresh) with updated signals"
    }
}

struct SettingsView: View {
    let store: CandidateStore
    @Bindable var state: HatInRingState
    @State private var confirmClearPicks = false

    var body: some View {
        VStack(spacing: 0) {
            BasicTopHeader(title: "Settings", subtitle: "Local controls and export") {
                FreshnessBadge(freshness: store.freshness)
            }

            ScrollView {
                VStack(spacing: 12) {
                    SettingsSection(title: "Data") {
                        SettingsActionRow(
                            title: store.freshness.summary,
                            subtitle: store.freshness.detail
                        ) {
                            Image(systemName: "archivebox")
                        } trailing: {
                            Text(store.freshness.statusLabel)
                                .font(HIRTheme.mono(11, weight: .bold))
                                .foregroundStyle(HIRTheme.accentRed)
                        }
                    }

                    SettingsSection(title: "Resume") {
                        Toggle(isOn: $state.restoreLastTab) {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Open to last tab")
                                    .font(HIRTheme.body(13, weight: .semibold))
                                    .foregroundStyle(HIRTheme.navy)
                                Text("When off, the app starts on The Field.")
                                    .font(HIRTheme.body(11))
                                    .foregroundStyle(HIRTheme.softText)
                            }
                        }
                        .tint(HIRTheme.navy)

                        Button {
                            state.showIntroAgain()
                        } label: {
                            SettingsActionRow(
                                title: "Show intro again",
                                subtitle: "Replay the first run orientation."
                            ) {
                                Image(systemName: "questionmark.circle")
                            } trailing: {
                                Image(systemName: "chevron.right")
                                    .font(.system(size: 12, weight: .semibold))
                                    .foregroundStyle(HIRTheme.softText)
                            }
                        }
                        .buttonStyle(.plain)
                    }

                    SettingsSection(title: "Picks") {
                        Button {
                            confirmClearPicks = true
                        } label: {
                            SettingsActionRow(
                                title: "Clear all picks",
                                subtitle: state.watchedCandidateIDs.isEmpty ? "Your pick list is already empty." : "Remove \(state.watchedCandidateIDs.count) tracked candidates."
                            ) {
                                Image(systemName: "trash")
                            } trailing: {
                                Text("Clear")
                                    .font(HIRTheme.body(12, weight: .semibold))
                                    .foregroundStyle(HIRTheme.accentRed)
                            }
                        }
                        .buttonStyle(.plain)
                        .disabled(state.watchedCandidateIDs.isEmpty)

                        ShareLink(item: state.exportPicksJSON(from: store.candidates)) {
                            SettingsActionRow(
                                title: "Export picks JSON",
                                subtitle: "Share a portable list of tracked candidates."
                            ) {
                                Image(systemName: "square.and.arrow.up")
                            } trailing: {
                                Text("Export")
                                    .font(HIRTheme.body(12, weight: .semibold))
                                    .foregroundStyle(HIRTheme.navy)
                            }
                        }
                        .disabled(state.watchedCandidateIDs.isEmpty)
                    }

                    SettingsSection(title: "Review") {
                        ShareLink(item: state.exportReviewDecisionsJSON()) {
                            SettingsActionRow(
                                title: "Export review decisions",
                                subtitle: "Creates JSON shaped for data/review_decisions.json."
                            ) {
                                Image(systemName: "tray.and.arrow.up")
                            } trailing: {
                                Text("\(state.exportableReviewDecisions().count)")
                                    .font(HIRTheme.mono(13, weight: .bold))
                                    .foregroundStyle(HIRTheme.accentRed)
                            }
                        }
                        .disabled(state.exportableReviewDecisions().isEmpty)
                    }
                }
                .padding(12)
            }
            .background(HIRTheme.parchment)
        }
        .alert("Clear all picks?", isPresented: $confirmClearPicks) {
            Button("Cancel", role: .cancel) {}
            Button("Clear", role: .destructive) {
                state.clearWatchlist()
            }
        } message: {
            Text("This removes the local pick list on this device.")
        }
    }
}

struct OnboardingView: View {
    let store: CandidateStore
    @Bindable var state: HatInRingState

    var body: some View {
        VStack(spacing: 0) {
            VStack(alignment: .leading, spacing: 14) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 3) {
                        Text("Hat-in-Ring")
                            .font(HIRTheme.display(30, weight: .semibold))
                            .foregroundStyle(HIRTheme.navy)
                        Text("RADAR")
                            .font(HIRTheme.body(10, weight: .bold))
                            .tracking(3)
                            .foregroundStyle(HIRTheme.accentRed)
                    }
                    Spacer()
                    RadarBadge()
                }

                Text("Track the 2028 field from one native radar surface.")
                    .font(HIRTheme.display(20, weight: .regular))
                    .foregroundStyle(Color(hex: 0x2C3A4F))
                    .lineSpacing(4)

                FreshnessBanner(freshness: store.freshness)
            }
            .padding(20)
            .background(HIRTheme.paper)

            VStack(spacing: 10) {
                OnboardingRow(symbol: "scope", title: "Field", message: "Ranked radar view with filters and updated movement.")
                OnboardingRow(symbol: "dot.radiowaves.left.and.right", title: "Wire", message: "Dispatches from the pipeline signal feed.")
                OnboardingRow(symbol: "folder", title: "Dossiers", message: "Full candidate files and the human review inbox.")
                OnboardingRow(symbol: "star", title: "Picks", message: "Your local watchlist that persists on this device.")
            }
            .padding(16)

            Spacer(minLength: 0)

            HStack(spacing: 10) {
                Button {
                    state.dismissIntro(opening: .field)
                } label: {
                    Text("Start in Field")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .tint(HIRTheme.navy)
                .accessibilityIdentifier("intro-start-field")

                Button {
                    state.dismissIntro(opening: .search)
                } label: {
                    Text("Search a name")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)
                .tint(HIRTheme.navy)
                .accessibilityIdentifier("intro-search")
            }
            .font(HIRTheme.body(13, weight: .semibold))
            .padding(16)
        }
        .background(HIRTheme.parchment.ignoresSafeArea())
        .presentationDetents([.large])
    }
}

private struct OnboardingRow: View {
    let symbol: String
    let title: String
    let message: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: symbol)
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(HIRTheme.navy)
                .frame(width: 28, height: 28)
            VStack(alignment: .leading, spacing: 3) {
                Text(title)
                    .font(HIRTheme.body(13, weight: .semibold))
                    .foregroundStyle(HIRTheme.navy)
                Text(message)
                    .font(HIRTheme.body(11.5))
                    .foregroundStyle(HIRTheme.softText)
                    .lineSpacing(2)
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
    }
}

private struct FieldFilterControls: View {
    @Bindable var state: HatInRingState

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                MenuChip(title: "Lane filter", selection: $state.fieldPartyFilter) { $0.label }
                MenuChip(title: "Confidence filter", selection: $state.fieldConfidenceFilter) { $0.label }
                MenuChip(title: "Field sort", selection: $state.fieldSort) { "Sort: \($0.label)" }
            }
        }
    }
}

private struct DossierModeControl: View {
    @Binding var selection: DossierMode

    var body: some View {
        HStack(spacing: 3) {
            ForEach(DossierMode.allCases) { mode in
                Button {
                    selection = mode
                } label: {
                    Text(mode.label)
                        .font(HIRTheme.body(12, weight: .semibold))
                        .foregroundStyle(selection == mode ? HIRTheme.navy : HIRTheme.softText)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 7)
                        .background(selection == mode ? HIRTheme.paper : Color.clear)
                        .clipShape(RoundedRectangle(cornerRadius: 7, style: .continuous))
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Show \(mode.label)")
                .accessibilityIdentifier("dossier-mode-\(mode.rawValue)")
            }
        }
        .padding(3)
        .background(HIRTheme.segmentFill)
        .clipShape(RoundedRectangle(cornerRadius: 9, style: .continuous))
    }
}

private struct ContinueDossierBanner: View {
    let candidate: Candidate
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HIRCard {
                HStack(spacing: 12) {
                    CandidatePortrait(candidate: candidate, width: 42, height: 48)
                    VStack(alignment: .leading, spacing: 3) {
                        Text("Continue dossier")
                            .font(HIRTheme.body(10, weight: .bold))
                            .tracking(0.8)
                            .foregroundStyle(HIRTheme.accentRed)
                        Text(candidate.name)
                            .font(HIRTheme.display(16, weight: .semibold))
                            .foregroundStyle(HIRTheme.navy)
                            .lineLimit(1)
                        Text(candidate.role)
                            .font(HIRTheme.body(11))
                            .foregroundStyle(HIRTheme.softText)
                            .lineLimit(1)
                    }
                    Spacer()
                    Image(systemName: "chevron.right")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundStyle(Color(hex: 0xB8AD91))
                }
                .padding(12)
            }
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("continue-dossier-\(candidate.id)")
    }
}

private struct ReviewInboxView: View {
    let store: CandidateStore
    @Bindable var state: HatInRingState

    var body: some View {
        let pending = store.pendingReviewItems(decisions: state.reviewDecisions)
        let decided = store.reviewItems.filter { item in
            guard let decision = state.reviewDecision(for: item.rid) else { return false }
            return decision != .later
        }

        VStack(spacing: 12) {
            FreshnessBanner(freshness: store.freshness)

            HStack {
                Text("Review queue")
                    .font(HIRTheme.display(20, weight: .semibold))
                    .foregroundStyle(HIRTheme.navy)
                Spacer()
                Text("\(pending.count) pending")
                    .font(HIRTheme.body(11, weight: .semibold))
                    .foregroundStyle(HIRTheme.softText)
            }
            .accessibilityIdentifier("review-queue-heading")

            if pending.isEmpty {
                EmptyState(
                    symbol: "checkmark.seal",
                    title: "No review items in this bundle",
                    message: decided.isEmpty ? "The bundled queue is empty." : "\(decided.count) items have local decisions ready to export."
                )
            } else {
                ForEach(pending) { item in
                    ReviewItemCard(item: item, decision: state.reviewDecision(for: item.rid)) { action in
                        state.setReviewDecision(action, for: item.rid)
                    }
                }
            }

            if !decided.isEmpty {
                SettingsSection(title: "Decisions ready") {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("\(state.exportableReviewDecisions().count) decisions can be exported for the pipeline.")
                            .font(HIRTheme.body(12))
                            .foregroundStyle(HIRTheme.softText)
                        ShareLink(item: state.exportReviewDecisionsJSON()) {
                            Text("Export review decisions")
                                .font(HIRTheme.body(12, weight: .semibold))
                                .foregroundStyle(HIRTheme.paperAlt)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 10)
                                .background(HIRTheme.navy)
                                .clipShape(RoundedRectangle(cornerRadius: 9, style: .continuous))
                        }
                        .disabled(state.exportableReviewDecisions().isEmpty)
                    }
                }
            }
        }
    }
}

private struct ReviewItemCard: View {
    let item: ReviewItem
    let decision: ReviewDecisionAction?
    let action: (ReviewDecisionAction) -> Void

    var body: some View {
        HIRCard {
            VStack(alignment: .leading, spacing: 11) {
                HStack(alignment: .firstTextBaseline, spacing: 8) {
                    Text(item.kindLabel)
                        .font(HIRTheme.body(9.5, weight: .bold))
                        .tracking(1)
                        .foregroundStyle(HIRTheme.accentRed)
                    Spacer()
                    Text(item.source)
                        .font(HIRTheme.body(10.5, weight: .semibold))
                        .foregroundStyle(HIRTheme.softText)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text(item.name)
                        .font(HIRTheme.display(18, weight: .semibold))
                        .foregroundStyle(HIRTheme.navy)
                    Text(item.headline)
                        .font(HIRTheme.body(12.5))
                        .foregroundStyle(Color(hex: 0x2C3A4F))
                        .lineSpacing(3)
                }

                HStack(spacing: 6) {
                    SignalTag(text: item.signalLabel)
                    SignalTag(text: item.date)
                }

                if let note = item.note {
                    Text(note)
                        .font(HIRTheme.body(11.5))
                        .foregroundStyle(HIRTheme.softText)
                        .lineSpacing(2)
                }

                if let sourceURL = item.sourceURL {
                    Link(destination: sourceURL) {
                        Label("Open review source", systemImage: "arrow.up.right.square")
                            .font(HIRTheme.body(11.5, weight: .semibold))
                            .foregroundStyle(HIRTheme.navy)
                    }
                    .accessibilityIdentifier("review-source-\(item.rid)")
                }

                HStack(spacing: 8) {
                    reviewButton(.confirm, tint: HIRTheme.navy)
                    reviewButton(.dismiss, tint: HIRTheme.accentRed)
                    reviewButton(.later, tint: Color(hex: 0x7F7864))
                }
            }
            .padding(14)
        }
        .accessibilityIdentifier("review-item-\(item.rid)")
    }

    private func reviewButton(_ value: ReviewDecisionAction, tint: Color) -> some View {
        Button {
            action(value)
        } label: {
            Text(value.label)
                .font(HIRTheme.body(12, weight: .semibold))
                .foregroundStyle(decision == value ? HIRTheme.paperAlt : tint)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 9)
                .background(decision == value ? tint : HIRTheme.paperAlt)
                .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
                .overlay {
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .stroke(tint.opacity(0.55), lineWidth: 1)
                }
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(value.label) \(item.name)")
        .accessibilityIdentifier("review-\(value.rawValue)-\(item.rid)")
    }
}

private struct CandidateRowsCard: View {
    let rows: [Candidate]
    @Bindable var state: HatInRingState
    let showRank: Bool

    var body: some View {
        HIRCard {
            VStack(spacing: 0) {
                ForEach(Array(rows.enumerated()), id: \.element.id) { index, candidate in
                    Button {
                        state.openCandidate(candidate.id)
                    } label: {
                        CandidateListRow(
                            candidate: candidate,
                            rank: showRank ? index + 1 : nil,
                            isWatching: state.isWatching(candidate.id)
                        )
                    }
                    .buttonStyle(.plain)
                    .accessibilityIdentifier("candidate-row-\(candidate.id)")

                    if candidate.id != rows.last?.id {
                        Divider()
                            .background(Color(hex: 0xEFE7D4))
                            .padding(.leading, showRank ? 86 : 68)
                    }
                }
            }
        }
    }
}

private struct BasicTopHeader<Accessory: View>: View {
    let title: String
    let subtitle: String
    let accessory: Accessory

    init(title: String, subtitle: String, @ViewBuilder accessory: () -> Accessory) {
        self.title = title
        self.subtitle = subtitle
        self.accessory = accessory()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(alignment: .center) {
                Text(title)
                    .font(HIRTheme.display(31, weight: .semibold))
                    .foregroundStyle(HIRTheme.navy)
                    .lineLimit(1)
                    .minimumScaleFactor(0.85)
                Spacer()
                accessory
            }
            Text(subtitle)
                .font(HIRTheme.body(11.5))
                .foregroundStyle(HIRTheme.mutedText)
                .lineLimit(2)
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

private struct FlexibleChips: View {
    let candidates: [Candidate]
    let action: (Candidate) -> Void

    var body: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 98), spacing: 7)], spacing: 7) {
            ForEach(candidates) { candidate in
                Button {
                    action(candidate)
                } label: {
                    Text(label(for: candidate))
                        .font(HIRTheme.body(12, weight: .semibold))
                        .foregroundStyle(Color(hex: 0x3F5C86))
                        .frame(minWidth: 74, minHeight: 32)
                        .padding(.horizontal, 12)
                        .background(HIRTheme.paper)
                        .clipShape(Capsule())
                        .overlay {
                            Capsule().stroke(Color(hex: 0xDED5BD), lineWidth: 1)
                        }
                }
                .buttonStyle(.plain)
                .contentShape(Capsule())
                .accessibilityIdentifier("suggestion-chip-\(candidate.id)")
            }
        }
        .padding(.horizontal, 20)
    }

    private func label(for candidate: Candidate) -> String {
        if candidate.id == "aoc" { return "Ocasio-Cortez" }
        return candidate.name.split(separator: " ").last.map(String.init) ?? candidate.name
    }
}
