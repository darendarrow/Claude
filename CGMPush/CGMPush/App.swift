import SwiftUI

@main
struct CGMPushApp: App {
    @StateObject private var syncService = SyncService()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(syncService)
        }
    }
}
