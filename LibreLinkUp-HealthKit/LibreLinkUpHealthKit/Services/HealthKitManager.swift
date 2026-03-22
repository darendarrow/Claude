import Foundation
import HealthKit

final class HealthKitManager {
    private let store = HKHealthStore()

    private var glucoseType: HKQuantityType {
        HKQuantityType(.bloodGlucose)
    }

    var isAvailable: Bool {
        HKHealthStore.isHealthDataAvailable()
    }

    func requestAuthorization() async throws {
        guard isAvailable else { return }

        let typesToShare: Set<HKSampleType> = [glucoseType]
        let typesToRead: Set<HKObjectType> = [glucoseType]

        try await store.requestAuthorization(toShare: typesToShare, read: typesToRead)
    }

    func writeGlucoseReadings(_ readings: [GlucoseReading]) async throws -> Int {
        guard isAvailable else { return 0 }

        let existingDates = try await fetchExistingGlucoseDates()

        let newReadings = readings.filter { reading in
            !existingDates.contains(where: { abs($0.timeIntervalSince(reading.timestamp)) < 30 })
        }

        guard !newReadings.isEmpty else { return 0 }

        let unit = HKUnit.gramUnit(with: .milli).unitDivided(by: HKUnit.literUnit(with: .deci))

        let samples: [HKQuantitySample] = newReadings.map { reading in
            let quantity = HKQuantity(unit: unit, doubleValue: reading.valueMgDl)
            let metadata: [String: Any] = [
                HKMetadataKeyExternalUUID: reading.id.uuidString,
                "Source": "LibreLinkUp",
            ]
            return HKQuantitySample(
                type: glucoseType,
                quantity: quantity,
                start: reading.timestamp,
                end: reading.timestamp,
                metadata: metadata
            )
        }

        try await store.save(samples)
        return samples.count
    }

    func fetchExistingGlucoseDates(hoursBack: Int = 24) async throws -> [Date] {
        let startDate = Calendar.current.date(byAdding: .hour, value: -hoursBack, to: Date())!
        let predicate = HKQuery.predicateForSamples(
            withStart: startDate,
            end: Date(),
            options: .strictStartDate
        )

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKSampleQuery(
                sampleType: glucoseType,
                predicate: predicate,
                limit: HKObjectQueryNoLimit,
                sortDescriptors: nil
            ) { _, samples, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                let dates = (samples ?? []).map { $0.startDate }
                continuation.resume(returning: dates)
            }
            store.execute(query)
        }
    }
}
