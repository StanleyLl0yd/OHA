// swift-tools-version: 6.0
// SPDX-License-Identifier: MPL-2.0
import PackageDescription

let package = Package(
    name: "OHAPrototype",
    platforms: [.macOS(.v14)],
    products: [
        .executable(name: "OHAPrototype", targets: ["OHAPrototype"])
    ],
    targets: [
        .systemLibrary(name: "COHAFFI", path: "include"),
        .executableTarget(
            name: "OHAPrototype",
            dependencies: ["COHAFFI"],
            path: "apps/oha-macos",
            exclude: ["FFISmoke.swift"],
            sources: ["OHAApp.swift"],
            linkerSettings: [
                .unsafeFlags(["-L", "target/debug"]),
                .linkedLibrary("oha_ffi")
            ]
        )
    ]
)
