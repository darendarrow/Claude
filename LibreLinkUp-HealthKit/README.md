# LibreLinkUp HealthKit

A macOS application that syncs continuous glucose monitor (CGM) readings from Abbott's [LibreLinkUp](https://www.librelinkup.com/) sharing platform into Apple HealthKit.

## What It Does

If you use a FreeStyle Libre CGM and share your glucose data through LibreLinkUp, this app pulls those readings and writes them as blood glucose samples in HealthKit. This makes your CGM data available to the Health app and any other HealthKit-integrated applications on your Mac.

## Requirements

- macOS 14.0 or later (Apple Silicon required for HealthKit support)
- Xcode 15 or later
- An Apple Developer account (free personal team is sufficient) for code signing
- A LibreLinkUp account with at least one active connection (someone sharing their Libre data with you, or your own data shared to yourself)

## Quick Start

1. Clone the repository
2. Open `LibreLinkUpHealthKit.xcodeproj` in Xcode
3. Select the **LibreLinkUpHealthKit** target, go to **Signing & Capabilities**, enable **Automatically manage signing**, and select your development team
4. Build and run (Cmd+R)
5. Grant HealthKit permissions when prompted
6. Open **Settings** (gear icon), enter your LibreLinkUp credentials, select your region, and tap **Log In**
7. Press **Sync Now** to fetch readings and write them to HealthKit

Credentials are saved to the macOS Keychain on successful login, so you won't need to re-enter them on subsequent launches. The app will automatically log in from saved credentials when relaunched.

See [docs/SETUP.md](docs/SETUP.md) for detailed setup instructions.

## Documentation

| Document | Description |
|---|---|
| [docs/SETUP.md](docs/SETUP.md) | Prerequisites, Xcode configuration, and first-run walkthrough |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Project structure, data flow, and component responsibilities |
| [docs/API-REFERENCE.md](docs/API-REFERENCE.md) | LibreLinkUp API endpoints, authentication flow, and data models |

## Project Structure

```
LibreLinkUpHealthKit/
  App.swift                       # App entry point
  ContentView.swift               # Main screen (status, current reading, sync)
  Info.plist                      # HealthKit usage descriptions
  LibreLinkUpHealthKit.entitlements  # HealthKit entitlement
  Assets.xcassets/                # Asset catalog (app icon)
  Models/
    GlucoseReading.swift          # Local glucose reading model
    LibreLinkUpModels.swift       # API response Codable types
  Services/
    HealthKitManager.swift        # HealthKit read/write operations
    KeychainManager.swift         # Credential storage via macOS Keychain
    LibreLinkUpClient.swift       # LibreLinkUp API client
    SyncService.swift             # Orchestrates API fetch + HealthKit write
  Views/
    GlucoseListView.swift         # Reading history list
    SettingsView.swift            # Login form, region picker, logout
```

## Building

The project uses [XcodeGen](https://github.com/yonaskolb/XcodeGen) for project generation. The `project.yml` file defines the build configuration. If you need to regenerate the Xcode project:

```bash
xcodegen generate
```

To build from the command line:

```bash
xcodebuild -project LibreLinkUpHealthKit.xcodeproj \
           -scheme LibreLinkUpHealthKit \
           -configuration Debug \
           build
```

**Note:** A valid development team must be configured in the project for code signing. The HealthKit entitlement requires a provisioning profile, which Xcode manages automatically when a team is selected. Set `DEVELOPMENT_TEAM` in `project.yml` or configure it in Xcode's Signing & Capabilities editor.

## License

This project is provided as-is for personal use. It is not affiliated with or endorsed by Abbott Laboratories.
