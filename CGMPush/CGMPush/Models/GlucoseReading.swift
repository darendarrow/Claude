import Foundation

struct GlucoseReading: Identifiable, Codable {
    let id: UUID
    let valueMgDl: Double
    let timestamp: Date
    let trendArrow: TrendArrow?

    init(valueMgDl: Double, timestamp: Date, trendArrow: TrendArrow? = nil) {
        self.id = UUID()
        self.valueMgDl = valueMgDl
        self.timestamp = timestamp
        self.trendArrow = trendArrow
    }

    var valueMmolL: Double {
        valueMgDl / 18.0182
    }

    var rangeCategory: RangeCategory {
        switch valueMgDl {
        case ..<70: return .low
        case 70..<180: return .inRange
        default: return .high
        }
    }
}

enum TrendArrow: Int, Codable {
    case fallingQuickly = 1
    case falling = 2
    case stable = 3
    case rising = 4
    case risingQuickly = 5

    var symbol: String {
        switch self {
        case .fallingQuickly: return "↓↓"
        case .falling: return "↓"
        case .stable: return "→"
        case .rising: return "↑"
        case .risingQuickly: return "↑↑"
        }
    }
}

enum RangeCategory {
    case low, inRange, high

    var color: String {
        switch self {
        case .low: return "red"
        case .inRange: return "green"
        case .high: return "orange"
        }
    }
}
