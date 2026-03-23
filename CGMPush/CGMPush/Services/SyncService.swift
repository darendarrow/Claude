import Foundation
import SwiftUI

@MainActor
final class SyncService: ObservableObject {
    @Published var isLoggedIn = false
    @Published var isSyncing = false
    @Published var latestReading: GlucoseReading?
    @Published var readings: [GlucoseReading] = []
    @Published var lastSyncDate: Date?
    @Published var errorMessage: String?
    @Published var syncResultMessage: String?
    @Published var hasSavedCredentials = false

    private var client: LibreLinkUpClient
    private let healthKit = HealthKitManager()
    private var patientId: String?

    @AppStorage("email") var email = ""
    @AppStorage("region") var region = "us"

    init() {
        self.client = LibreLinkUpClient(region: "us")
        self.hasSavedCredentials = KeychainManager.loadCredentials() != nil
    }

    func requestHealthKitAccess() async {
        do {
            try await healthKit.requestAuthorization()
        } catch {
            errorMessage = "HealthKit access denied: \(error.localizedDescription)"
        }
    }

    /// Attempt to log in using credentials saved in the Keychain.
    func loginFromKeychain() async {
        guard let credentials = KeychainManager.loadCredentials() else { return }
        client = LibreLinkUpClient(region: credentials.region)
        region = credentials.region
        await login(email: credentials.email, password: credentials.password, saveToKeychain: false)
    }

    func login(email: String, password: String, saveToKeychain: Bool = true) async {
        do {
            client = LibreLinkUpClient(region: region)
            try await client.login(email: email, password: password)
            let connections = try await client.getConnections()
            guard let first = connections.first else {
                throw LibreLinkUpError.noConnections
            }
            patientId = first.patientId
            isLoggedIn = true
            self.email = email
            errorMessage = nil

            if saveToKeychain {
                try KeychainManager.saveCredentials(email: email, password: password, region: region)
                hasSavedCredentials = true
            }
        } catch {
            isLoggedIn = false
            errorMessage = error.localizedDescription
        }
    }

    func logout() {
        KeychainManager.deleteCredentials()
        hasSavedCredentials = false
        isLoggedIn = false
        patientId = nil
        latestReading = nil
        readings = []
        lastSyncDate = nil
        email = ""
        errorMessage = nil
    }

    func sync() async {
        guard let patientId, isLoggedIn else { return }

        isSyncing = true
        errorMessage = nil
        syncResultMessage = nil

        do {
            let fetched = try await client.getGraphData(patientId: patientId)
            readings = fetched.sorted { $0.timestamp > $1.timestamp }
            latestReading = readings.first

            let written = try await healthKit.writeGlucoseReadings(fetched)
            lastSyncDate = Date()

            if written > 0 {
                syncResultMessage = "Wrote \(written) reading\(written == 1 ? "" : "s") to HealthKit."
            } else {
                syncResultMessage = "Fetched \(fetched.count) reading\(fetched.count == 1 ? "" : "s"). HealthKit already up to date."
            }
        } catch {
            errorMessage = "Sync failed: \(error.localizedDescription)"
        }

        isSyncing = false
    }
}
