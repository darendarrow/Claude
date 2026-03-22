# Setup Guide

## Prerequisites

### Software

- **macOS 14.0 (Sonoma)** or later
- **Xcode 15** or later (Swift 5.9+)

### Accounts

You need a LibreLinkUp account at [librelinkup.com](https://www.librelinkup.com/). This requires:

1. Someone with a FreeStyle Libre sensor sharing their data with you via the LibreLink mobile app, **or**
2. Your own LibreLink account where you've enabled sharing and accepted the invitation in LibreLinkUp

The app reads from the first available connection on your account.

### HealthKit Availability

HealthKit on macOS is limited. It is available on:

- Apple Silicon Macs running macOS 14+
- Some configurations may report `HKHealthStore.isHealthDataAvailable() == false`

If HealthKit is not available on your Mac, the app will still fetch and display glucose readings but will not be able to write them to the Health database.

## Xcode Configuration

### 1. Open the Project

```bash
open LibreLinkUpHealthKit.xcodeproj
```

### 2. Set Your Development Team

1. Select the **LibreLinkUpHealthKit** target
2. Go to **Signing & Capabilities**
3. Choose your Apple Developer team (a free personal team works for local development)

This is required for Keychain access and HealthKit entitlements.

### 3. Enable HealthKit Capability

The HealthKit entitlement may need to be enabled in the target:

1. Select the **LibreLinkUpHealthKit** target
2. Go to **Signing & Capabilities**
3. Click **+ Capability**
4. Add **HealthKit**

This adds the `com.apple.developer.healthkit` entitlement to the entitlements file.

### 4. Build and Run

Press **Cmd+R** or select **Product > Run**.

On first launch, macOS will prompt you to grant HealthKit permissions. Allow read and write access to **Blood Glucose** for the app to function correctly.

## First Run

### 1. Grant HealthKit Access

When the app launches for the first time, it requests HealthKit authorization. A system dialog will appear asking permission to read and write blood glucose data. Grant both.

### 2. Log In

1. Tap the **gear icon** in the toolbar to open Settings
2. Enter your LibreLinkUp **email** and **password**
3. Select your **region** from the dropdown (this must match the region your LibreLinkUp account is registered in)
4. Tap **Log In**

On successful login, your credentials are saved to the macOS Keychain. On subsequent launches, the app will automatically log in without prompting.

### 3. Sync

After logging in, tap **Sync Now** on the main screen. The app will:

1. Fetch glucose graph data from the LibreLinkUp API for your first connected patient
2. Display the readings in the app
3. Write new readings to HealthKit (skipping any that already exist within a 30-second window)

### 4. View History

Tap **Reading History** to see all fetched readings sorted by time, with color-coded range indicators:

- **Red** = Low (below 70 mg/dL)
- **Green** = In range (70-180 mg/dL)
- **Orange** = High (above 180 mg/dL)

## Logging Out

Open Settings and tap **Log Out** at the bottom of the form. This will:

- Delete saved credentials from the Keychain
- Clear all in-memory session data
- Return the app to the logged-out state

## Troubleshooting

### "Login failed" error

- Verify your email and password are correct
- Confirm the region matches your LibreLinkUp account (e.g., a European account should use "Europe", not "United States")
- LibreLinkUp sometimes redirects to a different regional server on first login; the app handles this automatically, but if it persists, try selecting the correct region manually

### "No LibreLinkUp connections found"

- Ensure someone is actively sharing their Libre data with your LibreLinkUp account
- Open the LibreLinkUp mobile app or website to confirm you have at least one active connection

### HealthKit not writing data

- Open **System Settings > Privacy & Security > Health** and confirm the app has write access to Blood Glucose
- Check that `HKHealthStore.isHealthDataAvailable()` returns `true` on your Mac
- If running on an Intel Mac, HealthKit may not be available

### Duplicate readings

The app checks for existing HealthKit samples within a 30-second window of each reading's timestamp before writing. If you see duplicates, they may have come from a different source app writing to HealthKit.
