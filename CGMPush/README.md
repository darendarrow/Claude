# CGM Push

An iOS application that syncs continuous glucose monitor (CGM) readings from Abbott's [LibreLinkUp](https://www.librelinkup.com/) sharing platform into Apple HealthKit.

## What It Does

If you use a FreeStyle Libre CGM and share your glucose data through LibreLinkUp, this app pulls those readings and writes them as blood glucose samples in HealthKit. This makes your CGM data available to the Health app and any other HealthKit-integrated applications on your iPhone.

## Requirements

- iOS 17.0 or later (iPhone)
- Xcode 15 or later
- An Apple Developer account (free personal team is sufficient) for code signing
- A LibreLinkUp account with at least one active connection (someone sharing their Libre data with you, or your own data shared to yourself)

## Quick Start

1. Clone the repository
2. Open `CGM Push.xcodeproj` in Xcode
3. Select the **CGMPush** target, go to **Signing & Capabilities**, enable **Automatically manage signing**, and select your development team
4. Build and run (Cmd+R)
5. Grant HealthKit permissions when prompted
6. Open **Settings** (gear icon), enter your LibreLinkUp credentials, select your region, and tap **Log In**
7. Press **Sync Now** to fetch readings and write them to HealthKit
8. Optionally enable **Auto-Sync** in Settings to sync on a schedule (every 10 min, 30 min, or 1 hour)

Credentials are saved to the iOS Keychain on successful login, so you won't need to re-enter them on subsequent launches. The app will automatically log in from saved credentials when relaunched.

When Auto-Sync is enabled, the app syncs periodically while in the foreground and uses iOS Background App Refresh to continue syncing when the app is in the background.

See [docs/SETUP.md](docs/SETUP.md) for detailed setup instructions.

## Documentation

| Document | Description |
|---|---|
| [docs/SETUP.md](docs/SETUP.md) | Prerequisites, Xcode configuration, and first-run walkthrough |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Project structure, data flow, and component responsibilities |
| [docs/API-REFERENCE.md](docs/API-REFERENCE.md) | LibreLinkUp API endpoints, authentication flow, and data models |

## Project Structure

```
CGMPush/
  App.swift                       # App entry point, background task registration
  ContentView.swift               # Main screen (status, current reading, sync)
  Info.plist                      # HealthKit descriptions, background modes
  CGMPush.entitlements            # HealthKit entitlement
  Assets.xcassets/                # Asset catalog (app icon)
  Models/
    GlucoseReading.swift          # Local glucose reading model
    LibreLinkUpModels.swift       # API response Codable types
  Services/
    HealthKitManager.swift        # HealthKit read/write operations
    KeychainManager.swift         # Credential storage via iOS Keychain
    LibreLinkUpClient.swift       # LibreLinkUp API client
    SyncService.swift             # Orchestrates sync, auto-sync timer, background refresh
  Views/
    GlucoseListView.swift         # Reading history list
    SettingsView.swift            # Login, region picker, auto-sync settings, logout
```

## Building

The project uses [XcodeGen](https://github.com/yonaskolb/XcodeGen) for project generation. The `project.yml` file defines the build configuration. If you need to regenerate the Xcode project:

```bash
xcodegen generate
```

To build from the command line:

```bash
xcodebuild -project "CGM Push.xcodeproj" \
           -scheme CGMPush \
           -configuration Debug \
           build
```

**Note:** A valid development team must be configured in the project for code signing. The HealthKit entitlement requires a provisioning profile, which Xcode manages automatically when a team is selected. Set `DEVELOPMENT_TEAM` in `project.yml` or configure it in Xcode's Signing & Capabilities editor.

## License

This project is provided as-is for personal use. It is not affiliated with or endorsed by Abbott Laboratories.
