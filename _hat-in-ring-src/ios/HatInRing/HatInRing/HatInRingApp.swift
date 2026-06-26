import SwiftUI

@main
struct HatInRingApp: App {
    @State private var state: HatInRingState
    private let store = CandidateStore.load()

    init() {
        let arguments = ProcessInfo.processInfo.arguments
        if arguments.contains("-ui-testing-reset") {
            HatInRingState.resetPersistentState()
        }
        _state = State(initialValue: HatInRingState(skipIntro: arguments.contains("-ui-testing-skip-intro")))
    }

    var body: some Scene {
        WindowGroup {
            RootView(store: store, state: state)
        }
    }
}
