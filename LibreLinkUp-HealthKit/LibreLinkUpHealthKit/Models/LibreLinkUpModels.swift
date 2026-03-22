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
        let user: User

        struct AuthTicket: Decodable {
            let token: String
            let expires: Int
            let duration: Int
        }

        struct User: Decodable {
            let id: String
            let firstName: String
            let lastName: String
        }
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
