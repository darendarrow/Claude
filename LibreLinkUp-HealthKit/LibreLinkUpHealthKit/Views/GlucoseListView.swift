import SwiftUI

struct GlucoseListView: View {
    @EnvironmentObject var syncService: SyncService

    var body: some View {
        List {
            if syncService.readings.isEmpty {
                ContentUnavailableView(
                    "No Readings",
                    systemImage: "waveform.path.ecg",
                    description: Text("Sync to fetch glucose readings.")
                )
            } else {
                ForEach(syncService.readings) { reading in
                    readingRow(reading)
                }
            }
        }
        .navigationTitle("Readings")
    }

    private func readingRow(_ reading: GlucoseReading) -> some View {
        HStack {
            Circle()
                .fill(colorForRange(reading.rangeCategory))
                .frame(width: 10, height: 10)

            Text("\(reading.valueMgDl, specifier: "%.0f")")
                .font(.headline.monospacedDigit())

            Text("mg/dL")
                .font(.caption)
                .foregroundStyle(.secondary)

            if let trend = reading.trendArrow {
                Text(trend.symbol)
                    .font(.caption)
            }

            Spacer()

            Text(reading.timestamp, style: .time)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    private func colorForRange(_ category: RangeCategory) -> Color {
        switch category {
        case .low: return .red
        case .inRange: return .green
        case .high: return .orange
        }
    }
}
