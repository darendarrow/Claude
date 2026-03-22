import SwiftUI

@main
struct LibreLinkUpHealthKitApp: App {
    @StateObject private var syncService = SyncService()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(syncService)
        }
    }
}
