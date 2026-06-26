import SwiftUI
import Observation

struct RootView: View {
    let store: CandidateStore
    @Bindable var state: HatInRingState
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass

    var body: some View {
        Group {
            if let issue = store.criticalIssue {
                CriticalDataUnavailableView(issue: issue)
            } else if horizontalSizeClass == .regular {
                RegularRootView(store: store, state: state)
            } else {
                CompactRootView(store: store, state: state)
            }
        }
        .tint(HIRTheme.navy)
        .sheet(isPresented: Binding(
            get: { store.criticalIssue == nil && state.shouldShowIntro },
            set: { state.shouldShowIntro = $0 }
        )) {
            OnboardingView(store: store, state: state)
        }
    }
}

private struct CriticalDataUnavailableView: View {
    let issue: StoreLoadIssue

    var body: some View {
        VStack(spacing: 18) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 42, weight: .semibold))
                .foregroundStyle(HIRTheme.accentRed)

            VStack(spacing: 8) {
                Text(issue.title)
                    .font(HIRTheme.display(26, weight: .semibold))
                    .foregroundStyle(HIRTheme.navy)
                    .multilineTextAlignment(.center)

                Text(issue.message)
                    .font(HIRTheme.body(14))
                    .foregroundStyle(HIRTheme.softText)
                    .lineSpacing(3)
                    .multilineTextAlignment(.center)
                    .frame(maxWidth: 420)
            }
        }
        .padding(28)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(HIRTheme.parchment.ignoresSafeArea())
        .accessibilityIdentifier("critical-data-unavailable")
    }
}

private struct CompactRootView: View {
    let store: CandidateStore
    @Bindable var state: HatInRingState

    var body: some View {
        NavigationStack(path: $state.path) {
            VStack(spacing: 0) {
                activeScreen
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                CustomTabBar(
                    state: state,
                    hasFreshWire: store.candidates.contains(where: RadarScoring.isFresh)
                )
            }
            .background(HIRTheme.parchment.ignoresSafeArea())
            .toolbar(.hidden, for: .navigationBar)
            .navigationDestination(for: String.self) { id in
                if let candidate = store.candidate(id: id) {
                    CandidateDetailView(candidate: candidate, store: store, state: state)
                        .toolbar(.hidden, for: .navigationBar)
                } else {
                    MissingCandidateView(state: state)
                        .toolbar(.hidden, for: .navigationBar)
                }
            }
        }
    }

    @ViewBuilder
    private var activeScreen: some View {
        switch state.selectedTab {
        case .field:
            FieldView(store: store, state: state)
        case .wire:
            WireView(store: store, state: state)
        case .dossiers:
            DossiersView(store: store, state: state)
        case .search:
            SearchScreen(store: store, state: state)
        case .picks:
            PicksView(store: store, state: state)
        case .settings:
            SettingsView(store: store, state: state)
        }
    }
}

private struct RegularRootView: View {
    let store: CandidateStore
    @Bindable var state: HatInRingState

    var body: some View {
        NavigationSplitView {
            AppSidebar(
                state: state,
                hasFreshWire: store.candidates.contains(where: RadarScoring.isFresh),
                trackedCount: store.candidates.count
            )
            .navigationBarHidden(true)
        } detail: {
            NavigationStack(path: $state.path) {
                activeScreen
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(HIRTheme.parchment)
                    .toolbar(.hidden, for: .navigationBar)
                    .navigationDestination(for: String.self) { id in
                        if let candidate = store.candidate(id: id) {
                            CandidateDetailView(candidate: candidate, store: store, state: state)
                                .toolbar(.hidden, for: .navigationBar)
                        } else {
                            MissingCandidateView(state: state)
                                .toolbar(.hidden, for: .navigationBar)
                        }
                    }
            }
        }
        .navigationSplitViewStyle(.balanced)
        .background(HIRTheme.parchment.ignoresSafeArea())
    }

    @ViewBuilder
    private var activeScreen: some View {
        switch state.selectedTab {
        case .field:
            FieldView(store: store, state: state)
        case .wire:
            WireView(store: store, state: state)
        case .dossiers:
            DossiersView(store: store, state: state)
        case .search:
            SearchScreen(store: store, state: state)
        case .picks:
            PicksView(store: store, state: state)
        case .settings:
            SettingsView(store: store, state: state)
        }
    }
}

private struct AppSidebar: View {
    @Bindable var state: HatInRingState
    let hasFreshWire: Bool
    let trackedCount: Int

    var body: some View {
        VStack(alignment: .leading, spacing: 22) {
            VStack(alignment: .leading, spacing: 3) {
                Text("Hat-in-Ring")
                    .font(HIRTheme.display(25, weight: .medium))
                    .foregroundStyle(HIRTheme.navy)
                Text("RADAR")
                    .font(HIRTheme.body(9, weight: .bold))
                    .tracking(3)
                    .foregroundStyle(HIRTheme.accentRed)
            }
            .padding(.top, 28)

            VStack(spacing: 6) {
                ForEach(AppTab.allCases) { tab in
                    SidebarTabButton(
                        tab: tab,
                        isSelected: state.selectedTab == tab,
                        hasFreshWire: tab == .wire && hasFreshWire
                    ) {
                        state.selectTab(tab)
                    }
                }
            }

            Spacer()

            VStack(alignment: .leading, spacing: 8) {
                RadarBadge()
                Text("\(trackedCount) tracked figures")
                    .font(HIRTheme.body(11, weight: .semibold))
                    .foregroundStyle(HIRTheme.softText)
            }
            .padding(.bottom, 12)
        }
        .padding(.horizontal, 18)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(HIRTheme.paperAlt)
    }
}

private struct SidebarTabButton: View {
    let tab: AppTab
    let isSelected: Bool
    let hasFreshWire: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                ZStack(alignment: .topTrailing) {
                    Image(systemName: tab.symbol)
                        .font(.system(size: 19, weight: .semibold))
                        .frame(width: 28, height: 28)

                    if hasFreshWire {
                        LiveDot()
                            .frame(width: 6, height: 6)
                            .offset(x: 1, y: 2)
                    }
                }

                Text(tab.label)
                    .font(HIRTheme.body(13, weight: .semibold))
                    .lineLimit(1)

                Spacer()
            }
            .foregroundStyle(isSelected ? HIRTheme.navy : Color(hex: 0x7F7864))
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(isSelected ? HIRTheme.paper : Color.clear)
            .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 10, style: .continuous)
                    .stroke(isSelected ? HIRTheme.border : Color.clear, lineWidth: 1)
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel(tab.label)
        .accessibilityIdentifier("tab-\(tab.rawValue)")
        .accessibilityAddTraits(isSelected ? [.isSelected] : [])
    }
}

private struct MissingCandidateView: View {
    @Bindable var state: HatInRingState

    var body: some View {
        VStack(spacing: 16) {
            Text("Dossier unavailable")
                .font(HIRTheme.display(24, weight: .semibold))
                .foregroundStyle(HIRTheme.navy)
            Button("Back to field") {
                state.selectTab(.field)
            }
            .buttonStyle(.borderedProminent)
            .tint(HIRTheme.navy)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(HIRTheme.parchment)
    }
}
