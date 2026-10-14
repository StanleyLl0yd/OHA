// SPDX-License-Identifier: MPL-2.0
import SwiftUI
import AppKit
import COHAFFI

struct OHAHomeView: View {
    @State private var result = "Ready"

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("OHA")
                .font(.largeTitle.bold())
            Text("Optimized Hybrid Archiver")
            Text("M0 native prototype: offline byte analysis only. Archive creation and extraction are not implemented.")
                .foregroundStyle(.secondary)
            Button("Run local Rust analysis probe", action: runProbe)
            Text(result)
                .font(.system(.body, design: .monospaced))
                .textSelection(.enabled)
            Spacer()
        }
        .padding(28)
        .frame(minWidth: 520, minHeight: 280)
    }

    private func runProbe() {
        guard oha_api_version() == 1 else {
            result = "Incompatible Rust ABI"
            return
        }
        let data = Array("OHA local Rust probe\n".utf8)
        var output = OhaAnalysisV1()
        output.struct_size = UInt32(MemoryLayout<OhaAnalysisV1>.size)
        output.version = 1
        let status = data.withUnsafeBufferPointer { bytes in
            oha_analyze_bytes_v1(bytes.baseAddress, UInt64(bytes.count), &output)
        }
        if status == 0 {
            result = "Rust analyzed \(output.sampled_bytes) bytes, entropy \(String(format: "%.2f", output.entropy_bits_per_byte)) bits/byte"
        } else {
            result = "Rust returned status \(status)"
        }
    }
}

@main
struct OHAApp: App {
    var body: some Scene {
        WindowGroup {
            OHAHomeView()
        }
    }
}
