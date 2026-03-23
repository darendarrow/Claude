# Architecture

## Overview

CGM Push is a SwiftUI macOS application following a service-oriented architecture. The app has three layers: views, a sync orchestrator, and service modules.

```
┌─────────────────────────────────────────┐
│                  Views                  │
│  ContentView  SettingsView  GlucoseList │
└──────────────────┬──────────────────────┘
                   │ @EnvironmentObject
┌──────────────────▼──────────────────────┐
│             SyncService                 │
│       (orchestrator / view model)       │
└───┬──────────────┬──────────────┬───────┘
    │              │              │
┌───▼───┐    ┌────▼─────┐  ┌────▼──────┐
│ Libre │    │HealthKit │  │ Keychain  │
│LinkUp │    │ Manager  │  │ Manager   │
│Client │    └──────────┘  └───────────┘
└───────┘
```

## Data Flow

### Login

1. User enters credentials in `SettingsView`
2. `SyncService.login()` is called, which creates a new `LibreLinkUpClient` with the selected region
3. `LibreLinkUpClient` authenticates against the regional API
4. If the API responds with a redirect, the client switches to the correct regional endpoint and retries
5. On success, the client extracts the auth token and computes the `account-id` header (SHA-256 hash of the user ID via CryptoKit)
6. `SyncService` fetches the connections list to get the `patientId`
7. `KeychainManager` saves email, password, and region to the macOS Keychain
8. `SyncService` updates published state, which the UI observes

### Auto-Login (App Launch)

1. `ContentView` appears and runs its `.task` modifier
2. `SyncService.requestHealthKitAccess()` runs first
3. If `hasSavedCredentials` is true, `SyncService.loginFromKeychain()` loads credentials from the Keychain and authenticates silently

### Sync

1. User clicks "Sync Now"
2. `SyncService.sync()` calls `LibreLinkUpClient.getGraphData(patientId:)`
3. The client fetches from `/llu/connections/{patientId}/graph` with the `Authorization` and `account-id` headers, and parses the response into `[GlucoseReading]`
4. `SyncService` updates the published `readings`, `latestReading`
5. `HealthKitManager.writeGlucoseReadings()` is called:
   - Fetches existing blood glucose samples from the last 24 hours
   - Filters out readings whose timestamps are within 30 seconds of existing samples
   - Creates `HKQuantitySample` objects with the `bloodGlucose` type and mg/dL unit
   - Saves the new samples to HealthKit in a single batch
6. `SyncService` publishes `syncResultMessage` with the write count or an "up to date" message

### Logout

1. `SyncService.logout()` deletes Keychain credentials via `KeychainManager`
2. All published state is reset to defaults

## Components

### App.swift

Entry point. Creates the `SyncService` as a `@StateObject` and injects it into the view hierarchy via `.environmentObject()`.

### ContentView.swift

Main screen displaying:
- Connection status indicator (green/red dot) with "Connected"/"Not Connected" label
- Last sync time (relative)
- Latest glucose reading in large text with mg/dL unit
- "Sync Now" button with loading state
- Sync result message (e.g., "Wrote 5 readings to HealthKit.")
- Error messages in red
- Navigation link to reading history
- Toolbar gear button for settings

Triggers HealthKit authorization and Keychain auto-login on appear.

### Views/SettingsView.swift

Login form with:
- Email and password fields
- Region picker (10 regions: US, EU, EU2, UAE, Asia Pacific, Australia, Canada, Germany, France, Japan)
- Login/Reconnect button with loading spinner
- Error display section
- Status section showing connection state and Keychain status ("Credentials saved")
- Last sync time
- Logout button (destructive, visible when logged in or credentials are saved)

Auto-dismisses on successful login.

### Views/GlucoseListView.swift

Scrollable list of all fetched readings showing value (mg/dL), trend arrow symbol, and timestamp. Color-coded dots indicate range category (low/in-range/high). Shows a `ContentUnavailableView` when no readings are available.

### Models/GlucoseReading.swift

Core data model with:
- `id: UUID` — unique identifier (generated on init)
- `valueMgDl: Double` — the raw glucose value
- `timestamp: Date` — when the reading was taken
- `trendArrow: TrendArrow?` — optional direction indicator (enum: fallingQuickly, falling, stable, rising, risingQuickly)
- Computed `valueMmolL` (mg/dL to mmol/L conversion, divides by 18.0182)
- Computed `rangeCategory` — low (<70), inRange (70-180), high (>180)

Supporting types:
- `TrendArrow` — raw `Int` enum (1-5) with `symbol` property returning arrow characters
- `RangeCategory` — enum with `color` property returning color name strings

### Models/LibreLinkUpModels.swift

Codable types matching the LibreLinkUp API JSON responses:
- `LoginRequest` — encodable email/password pair
- `LoginResponse` — custom decoder that tolerates malformed `data` fields (uses `try?` to handle empty objects or missing `authTicket`); extracts `authTicket.token` and `user.id`
- `LoginResponse.AuthData` — custom decoder that extracts `authTicket` and optionally `userId` from the nested `user.id` path
- `ConnectionsResponse` — status + array of `Connection` with `patientId`, `firstName`, `lastName`, and optional `glucoseMeasurement`
- `GraphResponse` — status + `GraphData` containing an array of `GraphPoint` with `Value`, `Timestamp`, `TrendArrow`

### Services/LibreLinkUpClient.swift

HTTP client for the LibreLinkUp API:
- Manages auth `token` and `accountId` state
- Supports 10 regional base URLs
- Handles regional redirects during login
- Sends required headers: `product: llu.android`, `version: 4.16.0`, `cache-control: no-cache`, `connection: Keep-Alive`
- Computes `account-id` header as SHA-256 hash of the user ID (via `CryptoKit.SHA256`) — required for all authenticated requests
- Sends `Authorization: Bearer <token>` and `account-id` on authenticated GET requests
- Parses timestamps in `M/d/yyyy h:mm:ss a` format with `en_US_POSIX` locale

### Services/HealthKitManager.swift

HealthKit integration:
- Checks `HKHealthStore.isHealthDataAvailable()` and throws `HealthKitManagerError.notAvailable` if unavailable
- Requests read/write authorization for `bloodGlucose`
- Writes `HKQuantitySample` entries with metadata (`Source: LibreLinkUp`, `HKMetadataKeyExternalUUID`)
- De-duplicates by querying existing samples within a 30-second tolerance window
- Uses `mg/dL` (milligrams per deciliter) as the HealthKit unit
- Logs operations to console with `[HealthKit]` prefix for diagnostics

### Services/KeychainManager.swift

Credential persistence using the Security framework:
- Stores email, password, and region as separate generic password items
- Uses `SecItemAdd`, `SecItemCopyMatching`, `SecItemDelete`
- Scoped to the service identifier `com.librelinkup-healthkit`
- Delete-before-write pattern to handle updates
- `KeychainError.saveFailed` with `OSStatus` for error reporting

### Services/SyncService.swift

Central orchestrator and `ObservableObject` for SwiftUI:
- Publishes `isLoggedIn`, `isSyncing`, `latestReading`, `readings`, `lastSyncDate`, `errorMessage`, `syncResultMessage`, `hasSavedCredentials`
- Persists email and region via `@AppStorage`
- Coordinates login, auto-login (from Keychain), sync, and logout flows
- Creates a new `LibreLinkUpClient` with the correct region on each login
- All methods are `@MainActor` isolated for safe UI updates

### Assets.xcassets

Asset catalog containing the app icon:
- 1024x1024 PNG icon featuring a white blood drop with a glucose pulse line on a teal-to-blue gradient, with sync arrows below
- Referenced via `ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon` in `project.yml`

### Configuration Files

- **Info.plist** — contains `NSHealthShareUsageDescription` and `NSHealthUpdateUsageDescription` for HealthKit permission prompts
- **LibreLinkUpHealthKit.entitlements** — contains `com.apple.developer.healthkit` and `com.apple.developer.healthkit.access` entitlements
- **project.yml** — XcodeGen project definition targeting macOS 14.0, Swift 5.9, with `ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon`

## State Management

The app uses SwiftUI's built-in state management:

| Mechanism | Used For |
|---|---|
| `@StateObject` | `SyncService` lifetime in `App.swift` |
| `@EnvironmentObject` | Sharing `SyncService` across views |
| `@Published` | Reactive UI updates from `SyncService` |
| `@AppStorage` | Persisting email and region in UserDefaults |
| `@State` | Local view state (form fields, loading flags) |
| Keychain (Security framework) | Secure credential storage across launches |

## Dependencies

The project uses only Apple frameworks — no third-party dependencies:

| Framework | Used In | Purpose |
|---|---|---|
| SwiftUI | All views, App.swift | UI framework |
| Foundation | All files | Networking, data, dates |
| HealthKit | HealthKitManager | Blood glucose read/write |
| Security | KeychainManager | Credential storage |
| CryptoKit | LibreLinkUpClient | SHA-256 hash for `account-id` header |
