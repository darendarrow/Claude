import SwiftUI
import BackgroundTasks

@main
struct CGMPushApp: App {
    @StateObject private var syncService = SyncService()
    @Environment(\.scenePhase) private var scenePhase

    init() {
        BGTaskScheduler.shared.register(
            forTaskWithIdentifier: SyncService.backgroundTaskIdentifier,
            using: nil
        ) { task in
            guard let refreshTask = task as? BGAppRefreshTask else { return }
            let syncTask = Task { @MainActor in
                let service = SyncService()
                await service.loginFromKeychain()
                if service.isLoggedIn {
                    await service.sync()
                    // Schedule the next background refresh
                    service.scheduleBackgroundRefresh()
                }
                refreshTask.setTaskCompleted(success: true)
            }
            refreshTask.expirationHandler = {
                syncTask.cancel()
                refreshTask.setTaskCompleted(success: false)
            }
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(syncService)
        }
        .onChange(of: scenePhase) { _, newPhase in
            if newPhase == .background {
                syncService.scheduleBackgroundRefresh()
            }
        }
    }
}
