# Architecture

## Overview

LibreLinkUp HealthKit is a SwiftUI application following a service-oriented architecture. The app has three layers: views, a sync orchestrator, and service modules.

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
2. `SyncService.login()` is called
3. `LibreLinkUpClient` authenticates against the regional API
4. If the API responds with a redirect, the client switches to the correct regional endpoint and retries
5. On success, `LibreLinkUpClient` fetches the connections list to get the `patientId`
6. `KeychainManager` saves email, password, and region to the macOS Keychain
7. `SyncService` updates published state, which the UI observes

### Auto-Login (App Launch)

1. `ContentView` appears and runs its `.task` modifier
2. `SyncService.requestHealthKitAccess()` runs first
3. If `hasSavedCredentials` is true, `SyncService.loginFromKeychain()` loads credentials from the Keychain and authenticates silently

### Sync

1. User taps "Sync Now" or the app triggers a sync
2. `SyncService.sync()` calls `LibreLinkUpClient.getGraphData(patientId:)`
3. The client fetches from `/llu/connections/{patientId}/graph` and parses the response into `[GlucoseReading]`
4. `SyncService` updates the published `readings` and `latestReading`
5. `HealthKitManager.writeGlucoseReadings()` is called:
   - Fetches existing blood glucose samples from the last 24 hours
   - Filters out readings whose timestamps are within 30 seconds of existing samples
   - Creates `HKQuantitySample` objects with the `bloodGlucose` type and mg/dL unit
   - Saves the new samples to HealthKit in a single batch

### Logout

1. `SyncService.logout()` deletes Keychain credentials via `KeychainManager`
2. All published state is reset to defaults

## Components

### App.swift

Entry point. Creates the `SyncService` as a `@StateObject` and injects it into the view hierarchy via `.environmentObject()`.

### ContentView.swift

Main screen displaying:
- Connection status indicator (green/red dot)
- Last sync time (relative)
- Latest glucose reading in large text with mg/dL unit
- "Sync Now" button with loading state
- Navigation link to reading history
- Toolbar gear button for settings

Triggers HealthKit authorization and Keychain auto-login on appear.

### Views/SettingsView.swift

Login form with:
- Email and password fields
- Region picker (10 regions)
- Login/Reconnect button with loading spinner
- Error display section
- Connection and Keychain status
- Logout button (destructive)

### Views/GlucoseListView.swift

Scrollable list of all fetched readings showing value, unit, trend arrow, and timestamp. Color-coded dots indicate range category (low/in-range/high).

### Models/GlucoseReading.swift

Core data model with:
- `valueMgDl: Double` — the raw glucose value
- `timestamp: Date` — when the reading was taken
- `trendArrow: TrendArrow?` — optional direction indicator
- Computed `valueMmolL` (mg/dL to mmol/L conversion)
- Computed `rangeCategory` — low (<70), in-range (70-180), high (>180)

### Models/LibreLinkUpModels.swift

Codable types matching the LibreLinkUp API JSON responses:
- `LoginRequest` / `LoginResponse` — authentication
- `ConnectionsResponse` — patient connections list
- `GraphResponse` — glucose graph data points

### Services/LibreLinkUpClient.swift

HTTP client for the LibreLinkUp API:
- Manages auth token state
- Supports 10 regional base URLs
- Handles regional redirects during login
- Sends required headers (`product: llu.ios`, `version: 4.12.0`)
- Parses timestamps in `M/d/yyyy h:mm:ss a` format

### Services/HealthKitManager.swift

HealthKit integration:
- Requests read/write authorization for `bloodGlucose`
- Writes `HKQuantitySample` entries with metadata (`Source: LibreLinkUp`, external UUID)
- De-duplicates by querying existing samples within a 30-second tolerance window
- Uses `mg/dL` (milligrams per deciliter) as the HealthKit unit

### Services/KeychainManager.swift

Credential persistence using the Security framework:
- Stores email, password, and region as separate generic password items
- Uses `SecItemAdd`, `SecItemCopyMatching`, `SecItemDelete`
- Scoped to the service identifier `com.librelinkup-healthkit`
- Delete-before-write pattern to handle updates

### Services/SyncService.swift

Central orchestrator and `ObservableObject` for SwiftUI:
- Publishes `isLoggedIn`, `isSyncing`, `latestReading`, `readings`, `lastSyncDate`, `errorMessage`, `hasSavedCredentials`
- Persists email and region via `@AppStorage`
- Coordinates login, auto-login, sync, and logout flows
- All methods are `@MainActor` isolated for safe UI updates

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
