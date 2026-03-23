import Foundation

// MARK: - Auth

struct LoginRequest: Encodable {
    let email: String
    let password: String
}

struct LoginResponse: Decodable {
    let status: Int
    let data: AuthData?
    let redirect: Bool?
    let region: String?

    struct AuthData: Decodable {
        let authTicket: AuthTicket
        let userId: String?

        struct AuthTicket: Decodable {
            let token: String
            let expires: Int
            let duration: Int
        }

        struct User: Decodable {
            let id: String
        }

        enum CodingKeys: String, CodingKey {
            case authTicket, user
        }

        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)
            authTicket = try container.decode(AuthTicket.self, forKey: .authTicket)
            userId = try container.decodeIfPresent(User.self, forKey: .user)?.id
        }
    }

    enum CodingKeys: String, CodingKey {
        case status, data, redirect, region
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        status = try container.decode(Int.self, forKey: .status)
        redirect = try container.decodeIfPresent(Bool.self, forKey: .redirect)
        region = try container.decodeIfPresent(String.self, forKey: .region)
        // data can be null, missing, or an object that may lack authTicket
        data = try? container.decodeIfPresent(AuthData.self, forKey: .data)
    }
}

// MARK: - Connections

struct ConnectionsResponse: Decodable {
    let status: Int
    let data: [Connection]

    struct Connection: Decodable {
        let patientId: String
        let firstName: String
        let lastName: String
        let glucoseMeasurement: GlucoseMeasurement?

        struct GlucoseMeasurement: Decodable {
            let Value: Double
            let Timestamp: String
            let TrendArrow: Int?
        }
    }
}

// MARK: - Graph

struct GraphResponse: Decodable {
    let status: Int
    let data: GraphData

    struct GraphData: Decodable {
        let graphData: [GraphPoint]

        struct GraphPoint: Decodable {
            let Value: Double
            let Timestamp: String
            let TrendArrow: Int?
        }
    }
}
