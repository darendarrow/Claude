import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var syncService: SyncService
    @Environment(\.dismiss) var dismiss

    @State private var email = ""
    @State private var password = ""
    @State private var selectedRegion = "us"
    @State private var isLoggingIn = false

    private let regions = [
        ("us", "United States"),
        ("eu", "Europe"),
        ("eu2", "Europe 2"),
        ("ae", "UAE"),
        ("ap", "Asia Pacific"),
        ("au", "Australia"),
        ("ca", "Canada"),
        ("de", "Germany"),
        ("fr", "France"),
        ("jp", "Japan"),
    ]

    var body: some View {
        NavigationStack {
            Form {
                Section("LibreLinkUp Account") {
                    TextField("Email", text: $email)
                        .textContentType(.emailAddress)
                        .autocorrectionDisabled()

                    SecureField("Password", text: $password)
                        .textContentType(.password)

                    Picker("Region", selection: $selectedRegion) {
                        ForEach(regions, id: \.0) { region in
                            Text(region.1).tag(region.0)
                        }
                    }
                }

                Section {
                    Button {
                        Task { await login() }
                    } label: {
                        HStack {
                            Spacer()
                            if isLoggingIn {
                                ProgressView()
                            } else {
                                Text(syncService.isLoggedIn ? "Reconnect" : "Log In")
                            }
                            Spacer()
                        }
                    }
                    .disabled(email.isEmpty || password.isEmpty || isLoggingIn)
                }

                if let error = syncService.errorMessage {
                    Section {
                        Text(error)
                            .foregroundStyle(.red)
                            .font(.caption)
                    }
                }

                Section("Status") {
                    LabeledContent("Connection") {
                        Text(syncService.isLoggedIn ? "Active" : "Inactive")
                            .foregroundStyle(syncService.isLoggedIn ? .green : .secondary)
                    }
                    if syncService.hasSavedCredentials {
                        LabeledContent("Keychain") {
                            Text("Credentials saved")
                                .foregroundStyle(.green)
                        }
                    }
                    if let lastSync = syncService.lastSyncDate {
                        LabeledContent("Last Sync") {
                            Text(lastSync, style: .relative)
                        }
                    }
                }

                if syncService.isLoggedIn || syncService.hasSavedCredentials {
                    Section {
                        Button("Log Out", role: .destructive) {
                            syncService.logout()
                        }
                    }
                }
            }
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .onAppear {
                email = syncService.email
                selectedRegion = syncService.region
            }
        }
    }

    private func login() async {
        isLoggingIn = true
        syncService.region = selectedRegion
        await syncService.login(email: email, password: password)
        isLoggingIn = false
        if syncService.isLoggedIn {
            dismiss()
        }
    }
}
