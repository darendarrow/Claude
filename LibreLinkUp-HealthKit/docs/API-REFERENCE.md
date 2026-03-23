# LibreLinkUp API Reference

This document describes the LibreLinkUp API endpoints used by the application. These are unofficial/undocumented endpoints reverse-engineered from the LibreLinkUp mobile app.

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

All requests must include the following headers:

```
Content-Type: application/json
Accept: application/json
cache-control: no-cache
connection: Keep-Alive
product: llu.android
version: 4.16.0
```

**Important notes on headers:**
- `product` must be `llu.android` (not `llu.ios`). The API rejects `llu.ios` with version 4.16.0+.
- `version` must be `4.16.0` or newer. Older versions (e.g., `4.12.0`) receive a `920` status response with a `minimumVersion` field indicating the required version.
- `cache-control` and `connection` headers are required by the API.

### Authenticated Request Headers

In addition to the headers above, authenticated requests require:

```
Authorization: Bearer <token>
account-id: <sha256-hex-of-user-id>
```

The `account-id` value is the lowercase hexadecimal SHA-256 hash of the `user.id` field returned in the login response. Without this header, authenticated endpoints return `{"message": "RequiredHeaderMissing"}`.

**Example computation (Swift):**

```swift
import CryptoKit

let userId = "019d0939-8463-7887-8520-9c1ee30064a0"
let hash = SHA256.hash(data: Data(userId.utf8))
let accountId = hash.map { String(format: "%02x", $0) }.joined()
// Result: "39a6285451e1f82294fb1f17bb40a1bea29df2701d583a692ac9873555c3065b"
```

## Endpoints

### POST `/llu/auth/login`

Authenticates with LibreLinkUp and returns an auth token.

**Headers:** Default headers only (no auth required).

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (success):**

The `data` object contains many fields; the ones used by this application are:

```json
{
  "status": 0,
  "data": {
    "user": {
      "id": "019d0939-8463-7887-8520-9c1ee30064a0",
      "firstName": "John",
      "lastName": "Doe",
      "email": "user@example.com",
      "country": "US"
    },
    "authTicket": {
      "token": "eyJ...",
      "expires": 1789835800,
      "duration": 15552000000
    }
  }
}
```

Key fields:
- `data.user.id` — used to compute the `account-id` header (SHA-256 hash)
- `data.authTicket.token` — Bearer token for authenticated requests
- `data.authTicket.expires` — Unix timestamp when the token expires
- `data.authTicket.duration` — Token lifetime in milliseconds

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

**Response (version too old):**

If the `version` header is below the minimum required:

```json
{
  "data": {
    "minimumVersion": "4.16.0"
  },
  "status": 920
}
```

### GET `/llu/connections`

Returns the list of patients sharing data with the authenticated user.

**Headers:** Requires `Authorization` and `account-id`.

**Response:**

```json
{
  "status": 0,
  "data": [
    {
      "patientId": "11e9c963-6e83-11ec-90ad-0242ac110005",
      "firstName": "Jane",
      "lastName": "Doe",
      "targetLow": 70,
      "targetHigh": 180,
      "glucoseMeasurement": {
        "Value": 160,
        "ValueInMgPerDl": 160,
        "Timestamp": "3/23/2026 12:38:51 PM",
        "FactoryTimestamp": "3/23/2026 4:38:51 PM",
        "TrendArrow": 3,
        "MeasurementColor": 1,
        "GlucoseUnits": 1,
        "isHigh": false,
        "isLow": false
      },
      "sensor": {
        "sn": "0R8FDDJ820",
        "a": 1773402121
      }
    }
  ],
  "ticket": {
    "token": "eyJ...",
    "expires": 1789835969,
    "duration": 15552000000
  }
}
```

The `glucoseMeasurement` field contains the most recent reading for each connection. The app uses the `patientId` from the first connection.

Note: The response may include a `ticket` object with a refreshed auth token.

### GET `/llu/connections/{patientId}/graph`

Returns historical glucose readings for the specified patient.

**Headers:** Requires `Authorization` and `account-id`.

**Response:**

```json
{
  "status": 0,
  "data": {
    "graphData": [
      {
        "Value": 105.0,
        "Timestamp": "3/23/2026 2:30:00 PM",
        "TrendArrow": 3
      },
      {
        "Value": 110.0,
        "Timestamp": "3/23/2026 2:45:00 PM",
        "TrendArrow": 4
      }
    ]
  }
}
```

## Data Types

### Timestamp Format

All timestamps use the format `M/d/yyyy h:mm:ss a` with `en_US_POSIX` locale. Examples:

- `3/23/2026 2:30:00 PM`
- `12/1/2024 9:05:30 AM`

The `Timestamp` field represents the local time for the user. The `FactoryTimestamp` field (present in connections responses) represents UTC.

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

The connections response also includes `ValueInMgPerDl` as an explicit field.

### MeasurementColor Values

| Value | Meaning |
|---|---|
| 1 | In range |
| 2 | Low |
| 3 | High |

## Error Handling

- **HTTP 401**: Token expired or invalid. The app throws `LibreLinkUpError.notAuthenticated`.
- **Status 920**: Client version too old. The `data.minimumVersion` field indicates the minimum required version.
- **`RequiredHeaderMissing`**: The `account-id` header is missing or the `product`/`version` headers are incorrect. Returned as `{"message": "RequiredHeaderMissing"}`.
- **Login failure**: If `data` is `nil` in the login response (without a redirect), the app throws `LibreLinkUpError.authFailed`.
- **No connections**: If the connections array is empty, the app throws `LibreLinkUpError.noConnections`.

## Rate Limiting

The LibreLinkUp API does not publish rate limits. The app performs on-demand syncs triggered by the user. Avoid excessive automated polling to prevent account restrictions.

## API Versioning

The API enforces minimum client versions. As of March 2026, the minimum version is `4.16.0`. When the API raises the minimum version, update the `version` header in `LibreLinkUpClient.defaultHeaders`. The API may also require new headers in the future; monitor for `RequiredHeaderMissing` responses.
