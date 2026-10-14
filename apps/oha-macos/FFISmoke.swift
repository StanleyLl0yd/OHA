// SPDX-License-Identifier: MPL-2.0
import Foundation

precondition(oha_api_version() == 1)
precondition(MemoryLayout<OhaAnalysisV1>.size == 72)
let data = Array("OHA native Swift probe\n".utf8)
var output = OhaAnalysisV1()
output.struct_size = UInt32(MemoryLayout<OhaAnalysisV1>.size)
output.version = 1
let status = data.withUnsafeBufferPointer { bytes in
    oha_analyze_bytes_v1(bytes.baseAddress, UInt64(bytes.count), &output)
}
precondition(status == 0)
precondition(output.sampled_bytes == UInt64(data.count))
precondition(output.content_hint == 1)
print("OHA Swift -> Rust FFI PASS")
