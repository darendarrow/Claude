# LibreLinkUp API Reference

This document describes the LibreLinkUp API endpoints used by the application. These are unofficial/undocumented endpoints used by the LibreLinkUp mobile app.

## Base URLs

The API is region-specific. The client selects a base URL based on the user's region:

| Region | Base URL |
|---|---|
| `us` | `https://api-us.libreview.io` |
| `eu` | `https://api-eu.libreview.io` |
| `eu2` | `https://api-eu2.libreview.io` |
| `ae` | `https://api-ae.libreview.io` |
| `ap` | `https://api-ap.libreview.io` |
| `au` | `https://api-au.libreview.io` |
| `ca` | `https://api-ca.libreview.io` |
| `de` | `https://api-de.libreview.io` |
| `fr` | `https://api-fr.libreview.io` |
| `jp` | `https://api-jp.libreview.io` |

## Required Headers

All requests include these headers to mimic the official iOS app:

```
Content-Type: application/json
Accept: application/json
product: llu.ios
version: 4.12.0
```

Authenticated requests additionally include:

```
Authorization: Bearer <token>
```

## Endpoints

### POST `/llu/auth/login`

Authenticates with LibreLinkUp and returns an auth token.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (success):**

```json
{
  "status": 0,
  "data": {
    "authTicket": {
      "token": "eyJ...",
      "expires": 1234567890,
      "duration": 86400
    },
    "user": {
      "id": "abc-123",
      "firstName": "John",
      "lastName": "Doe"
    }
  }
}
```

**Response (regional redirect):**

If the account belongs to a different region, the API returns a redirect response instead of auth data:

```json
{
  "status": 0,
  "data": null,
  "redirect": true,
  "region": "eu"
}
```

When this happens, the client switches its base URL to the region indicated and retries the login.

### GET `/llu/connections`

Returns the list of patients sharing data with the authenticated user.

**Headers:** Requires `Authorization: Bearer <token>`

**Response:**

```json
{
  "status": 0,
  "data": [
    {
      "patientId": "patient-uuid-123",
      "firstName": "Jane",
      "lastName": "Doe",
      "glucoseMeasurement": {
        "Value": 105.0,
        "Timestamp": "3/15/2025 2:30:00 PM",
        "TrendArrow": 3
      }
    }
  ]
}
```

The `glucoseMeasurement` field contains the most recent reading for each connection. The app uses the `patientId` from the first connection.

### GET `/llu/connections/{patientId}/graph`

Returns historical glucose readings for the specified patient.

**Headers:** Requires `Authorization: Bearer <token>`

**Response:**

```json
{
  "status": 0,
  "data": {
    "graphData": [
      {
        "Value": 105.0,
        "Timestamp": "3/15/2025 2:30:00 PM",
        "TrendArrow": 3
      },
      {
        "Value": 110.0,
        "Timestamp": "3/15/2025 2:45:00 PM",
        "TrendArrow": 4
      }
    ]
  }
}
```

## Data Types

### Timestamp Format

All timestamps use the format `M/d/yyyy h:mm:ss a` with `en_US_POSIX` locale. Examples:

- `3/15/2025 2:30:00 PM`
- `12/1/2024 9:05:30 AM`

### TrendArrow Values

| Value | Meaning | Symbol |
|---|---|---|
| 1 | Falling quickly | `↓↓` |
| 2 | Falling | `↓` |
| 3 | Stable | `→` |
| 4 | Rising | `↑` |
| 5 | Rising quickly | `↑↑` |

### Glucose Values

Glucose values (`Value` field) are in **mg/dL** (milligrams per deciliter). To convert to mmol/L, divide by 18.0182.

## Error Handling

- **HTTP 401**: Token expired or invalid. The app throws `LibreLinkUpError.notAuthenticated`.
- **Login failure**: If `data` is `nil` in the login response (without a redirect), the app throws `LibreLinkUpError.authFailed`.
- **No connections**: If the connections array is empty, the app throws `LibreLinkUpError.noConnections`.

## Rate Limiting

The LibreLinkUp API does not publish rate limits. The app performs on-demand syncs triggered by the user. Avoid excessive automated polling to prevent account restrictions.
