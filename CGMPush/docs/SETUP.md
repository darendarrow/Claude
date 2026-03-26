# Setup Guide

## Prerequisites

### Software

- **iOS 17.0** or later (iPhone)
- **Xcode 15** or later (Swift 5.9+)

### Accounts

You need a LibreLinkUp account at [librelinkup.com](https://www.librelinkup.com/). This requires:

1. Someone with a FreeStyle Libre sensor sharing their data with you via the LibreLink mobile app, **or**
2. Your own LibreLink account where you've enabled sharing and accepted the invitation in LibreLinkUp

The app reads from the first available connection on your account.

### Apple Developer Account

A development team is required for code signing. The HealthKit entitlement necessitates a provisioning profile, which Xcode manages automatically. A free personal Apple Developer team (your Apple ID) is sufficient for local development.

## Xcode Configuration

### 1. Open the Project

```bash
open "CGM Push.xcodeproj"
```

### 2. Set Your Development Team

1. Select the **CGMPush** target
2. Go to **Signing & Capabilities**
3. Check **Automatically manage signing**
4. Choose your Apple Developer team from the **Team** dropdown

This is required for Keychain access and the HealthKit entitlement. Without a team, the build will fail with: *"CGMPush" requires a provisioning profile.*

### 3. Verify HealthKit Capability

The project already includes the HealthKit entitlement in `CGMPush.entitlements`. If it is missing for any reason:

1. Select the **CGMPush** target
2. Go to **Signing & Capabilities**
3. Click **+ Capability**
4. Add **HealthKit**

The entitlements file should contain:

```xml
<key>com.apple.developer.healthkit</key>
<true/>
<key>com.apple.developer.healthkit.access</key>
<array/>
```

### 4. Build and Run

Press **Cmd+R** or select **Product > Run** to build and install on your connected iPhone.

On first launch, iOS will prompt you to grant HealthKit permissions. Allow read and write access to **Blood Glucose** for the app to function correctly.

### Alternative: Configure via project.yml

If you use [XcodeGen](https://github.com/yonaskolb/XcodeGen), you can set your team ID directly in `project.yml`:

```yaml
settings:
  base:
    DEVELOPMENT_TEAM: "YOUR_TEAM_ID"
```

Then regenerate the project:

```bash
xcodegen generate
```

## First Run

### 1. Grant HealthKit Access

When the app launches for the first time, it requests HealthKit authorization. A system dialog will appear asking permission to read and write blood glucose data. Grant both.

### 2. Log In

1. Tap the **gear icon** in the toolbar to open Settings
2. Enter your LibreLinkUp **email** and **password**
3. Select your **region** from the picker (this must match the region your LibreLinkUp account is registered in)
4. Tap **Log In**

On successful login:
- Your credentials are saved to the iOS Keychain
- The Settings sheet dismisses automatically
- The status indicator turns green ("Connected")

On subsequent launches, the app will automatically log in using saved Keychain credentials without prompting.

### 3. Sync

After logging in, tap **Sync Now** on the main screen. The app will:

1. Fetch glucose graph data from the LibreLinkUp API for your first connected patient
2. Display the readings in the app with the latest value shown prominently
3. Write new readings to HealthKit (skipping any that already exist within a 30-second window)
4. Show a result message below the sync button:
   - "Wrote X readings to HealthKit." — new data was written
   - "Fetched X readings. HealthKit already up to date." — all readings already existed

### 4. Enable Auto-Sync (Optional)

1. Tap the **gear icon** to open Settings
2. Toggle **Auto-Sync** on
3. Select your preferred interval: **10 min**, **30 min**, or **1 hour**

When enabled, the app will sync automatically:
- **In the foreground**: A timer loop syncs at the exact configured interval
- **In the background**: iOS Background App Refresh wakes the app periodically to sync (timing is approximate and managed by iOS)

To ensure background sync works, verify that **Background App Refresh** is enabled for CGM Push in **iOS Settings > General > Background App Refresh**.

### 5. View History

Tap **Reading History** to see all fetched readings sorted by time, with color-coded range indicators:

- **Red** = Low (below 70 mg/dL)
- **Green** = In range (70-180 mg/dL)
- **Orange** = High (above 180 mg/dL)

## Logging Out

Open Settings and tap **Log Out** at the bottom of the form. This will:

- Stop auto-sync if running
- Delete saved credentials from the Keychain
- Clear all in-memory session data (readings, connection state)
- Return the app to the logged-out state

## Troubleshooting

### Build fails with "requires a provisioning profile"

A development team must be selected in Signing & Capabilities. See step 2 above.

### "Login failed" error

- Verify your email and password are correct
- Confirm the region matches your LibreLinkUp account (e.g., a European account should use "Europe", not "United States")
- LibreLinkUp sometimes redirects to a different regional server on first login; the app handles this automatically, but if it persists, try selecting the correct region manually

### "No LibreLinkUp connections found"

- Ensure someone is actively sharing their Libre data with your LibreLinkUp account
- Open the LibreLinkUp mobile app or website to confirm you have at least one active connection

### HealthKit not writing data

- Open **Settings > Privacy & Security > Health** on your iPhone and confirm the app has write access to Blood Glucose
- After syncing, check the result message below the Sync button — it will indicate whether samples were written or if HealthKit was already up to date
- Check the Xcode console for `[HealthKit]` log messages that indicate the exact operation being performed

### Duplicate readings

The app checks for existing HealthKit samples within a 30-second window of each reading's timestamp before writing. If you see duplicates, they may have come from a different source app writing to HealthKit.

### Sync succeeds but shows 0 new readings

The de-duplication logic compares against the last 24 hours of existing HealthKit samples. If the same readings were already written (e.g., from a previous sync), they will be skipped. This is expected behavior.

### Auto-sync not running in the background

- Ensure **Background App Refresh** is enabled for CGM Push in **iOS Settings > General > Background App Refresh**
- iOS controls the exact timing of background refreshes — the configured interval is a minimum, not a guarantee. iOS may delay background tasks based on battery, usage patterns, and system conditions
- Low Power Mode disables Background App Refresh entirely
- The app must have been launched at least once and the Auto-Sync toggle must be enabled in Settings
