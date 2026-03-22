import Foundation
import Security

enum KeychainManager {
    private static let service = "com.librelinkup-healthkit"
    private static let emailKey = "email"
    private static let passwordKey = "password"
    private static let regionKey = "region"

    // MARK: - Credentials

    static func saveCredentials(email: String, password: String, region: String) throws {
        try setString(email, forKey: emailKey)
        try setString(password, forKey: passwordKey)
        try setString(region, forKey: regionKey)
    }

    static func loadCredentials() -> (email: String, password: String, region: String)? {
        guard let email = getString(forKey: emailKey),
              let password = getString(forKey: passwordKey) else {
            return nil
        }
        let region = getString(forKey: regionKey) ?? "us"
        return (email, password, region)
    }

    static func deleteCredentials() {
        deleteItem(forKey: emailKey)
        deleteItem(forKey: passwordKey)
        deleteItem(forKey: regionKey)
    }

    // MARK: - Private

    private static func setString(_ value: String, forKey key: String) throws {
        guard let data = value.data(using: .utf8) else { return }

        // Delete any existing item first
        deleteItem(forKey: key)

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
        ]

        let status = SecItemAdd(query as CFDictionary, nil)
        guard status == errSecSuccess else {
            throw KeychainError.saveFailed(status)
        }
    }

    private static func getString(forKey key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]

        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)

        guard status == errSecSuccess,
              let data = item as? Data,
              let string = String(data: data, encoding: .utf8) else {
            return nil
        }
        return string
    }

    @discardableResult
    private static func deleteItem(forKey key: String) -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
        ]
        return SecItemDelete(query as CFDictionary) == errSecSuccess
    }
}

enum KeychainError: LocalizedError {
    case saveFailed(OSStatus)

    var errorDescription: String? {
        switch self {
        case .saveFailed(let status):
            return "Failed to save to Keychain (OSStatus \(status))."
        }
    }
}
