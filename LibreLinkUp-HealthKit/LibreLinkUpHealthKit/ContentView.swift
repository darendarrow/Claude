import SwiftUI

struct ContentView: View {
    @EnvironmentObject var syncService: SyncService
    @State private var showingSettings = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                statusCard
                lastReadingCard
                syncButton
                Spacer()
                NavigationLink(destination: GlucoseListView()) {
                    Label("Reading History", systemImage: "list.bullet")
                }
            }
            .padding()
            .navigationTitle("LibreLinkUp")
            .toolbar {
                Button {
                    showingSettings = true
                } label: {
                    Image(systemName: "gear")
                }
            }
            .sheet(isPresented: $showingSettings) {
                SettingsView()
            }
            .task {
                await syncService.requestHealthKitAccess()
                if !syncService.isLoggedIn && syncService.hasSavedCredentials {
                    await syncService.loginFromKeychain()
                }
            }
        }
    }

    private var statusCard: some View {
        HStack {
            Circle()
                .fill(syncService.isLoggedIn ? .green : .red)
                .frame(width: 12, height: 12)
            Text(syncService.isLoggedIn ? "Connected" : "Not Connected")
                .font(.headline)
            Spacer()
            if let lastSync = syncService.lastSyncDate {
                Text(lastSync, style: .relative)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
    }

    private var lastReadingCard: some View {
        VStack(spacing: 8) {
            if let reading = syncService.latestReading {
                Text("\(reading.valueMgDl, specifier: "%.0f")")
                    .font(.system(size: 64, weight: .bold, design: .rounded))
                Text("mg/dL")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Text(reading.timestamp, style: .relative)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            } else {
                Text("--")
                    .font(.system(size: 64, weight: .bold, design: .rounded))
                    .foregroundStyle(.tertiary)
                Text("No readings yet")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 32)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
    }

    private var syncButton: some View {
        Button {
            Task { await syncService.sync() }
        } label: {
            HStack {
                if syncService.isSyncing {
                    ProgressView()
                        .tint(.white)
                } else {
                    Image(systemName: "arrow.triangle.2.circlepath")
                }
                Text(syncService.isSyncing ? "Syncing..." : "Sync Now")
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(syncService.isSyncing ? .gray : .blue, in: RoundedRectangle(cornerRadius: 12))
            .foregroundStyle(.white)
            .font(.headline)
        }
        .disabled(syncService.isSyncing || !syncService.isLoggedIn)
    }
}
