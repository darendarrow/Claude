import CryptoKit
import Foundation

final class LibreLinkUpClient {
    private var token: String?
    private var accountId: String?
    private var baseURL: URL

    private static let regionURLs: [String: String] = [
        "us": "https://api-us.libreview.io",
        "eu": "https://api-eu.libreview.io",
        "eu2": "https://api-eu2.libreview.io",
        "ae": "https://api-ae.libreview.io",
        "ap": "https://api-ap.libreview.io",
        "au": "https://api-au.libreview.io",
        "ca": "https://api-ca.libreview.io",
        "de": "https://api-de.libreview.io",
        "fr": "https://api-fr.libreview.io",
        "jp": "https://api-jp.libreview.io",
    ]

    private static let defaultHeaders: [String: String] = [
        "Content-Type": "application/json",
        "Accept": "application/json",
        "cache-control": "no-cache",
        "connection": "Keep-Alive",
        "product": "llu.android",
        "version": "4.16.0",
    ]

    init(region: String = "us") {
        let urlString = Self.regionURLs[region] ?? Self.regionURLs["us"]!
        self.baseURL = URL(string: urlString)!
    }

    // MARK: - Auth

    func login(email: String, password: String) async throws {
        let url = baseURL.appendingPathComponent("llu/auth/login")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        Self.defaultHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }

        let body = LoginRequest(email: email, password: password)
        request.httpBody = try JSONEncoder().encode(body)

        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(LoginResponse.self, from: data)

        // Handle regional redirect
        if response.redirect == true, let region = response.region {
            if let newURL = Self.regionURLs[region] {
                self.baseURL = URL(string: newURL)!
            }
            try await login(email: email, password: password)
            return
        }

        guard let authData = response.data else {
            throw LibreLinkUpError.authFailed
        }

        self.token = authData.authTicket.token

        // Compute account-id header: SHA-256 hash of the user ID
        if let userId = authData.userId {
            let hash = SHA256.hash(data: Data(userId.utf8))
            self.accountId = hash.map { String(format: "%02x", $0) }.joined()
        }
    }

    // MARK: - Connections

    func getConnections() async throws -> [ConnectionsResponse.Connection] {
        let url = baseURL.appendingPathComponent("llu/connections")
        let data = try await authenticatedRequest(url: url)
        let response = try JSONDecoder().decode(ConnectionsResponse.self, from: data)
        return response.data
    }

    // MARK: - Graph Data

    func getGraphData(patientId: String) async throws -> [GlucoseReading] {
        let url = baseURL.appendingPathComponent("llu/connections/\(patientId)/graph")
        let data = try await authenticatedRequest(url: url)
        let response = try JSONDecoder().decode(GraphResponse.self, from: data)

        return response.data.graphData.compactMap { point in
            guard let date = Self.parseTimestamp(point.Timestamp) else { return nil }
            return GlucoseReading(
                valueMgDl: point.Value,
                timestamp: date,
                trendArrow: point.TrendArrow.flatMap { TrendArrow(rawValue: $0) }
            )
        }
    }

    // MARK: - Private

    private func authenticatedRequest(url: URL) async throws -> Data {
        guard let token else { throw LibreLinkUpError.notAuthenticated }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        Self.defaultHeaders.forEach { request.setValue($1, forHTTPHeaderField: $0) }
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        if let accountId {
            request.setValue(accountId, forHTTPHeaderField: "account-id")
        }

        let (data, response) = try await URLSession.shared.data(for: request)

        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 401 {
            throw LibreLinkUpError.notAuthenticated
        }

        return data
    }

    private static func parseTimestamp(_ string: String) -> Date? {
        let formatter = DateFormatter()
        formatter.dateFormat = "M/d/yyyy h:mm:ss a"
        formatter.locale = Locale(identifier: "en_US_POSIX")
        return formatter.date(from: string)
    }
}

enum LibreLinkUpError: LocalizedError {
    case authFailed
    case notAuthenticated
    case noConnections

    var errorDescription: String? {
        switch self {
        case .authFailed: return "Login failed. Check your email and password."
        case .notAuthenticated: return "Not logged in. Please log in first."
        case .noConnections: return "No LibreLinkUp connections found."
        }
    }
}
