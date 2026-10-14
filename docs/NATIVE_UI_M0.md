# Native UI compilation probes (M0)

Windows: `apps/oha-windows`, an unpackaged WinUI 3 / C# shell referencing pinned Microsoft.WindowsAppSDK and SDK BuildTools packages. macOS: `apps/oha-macos/OHAApp.swift`, a SwiftUI view with AppKit linkage. Both display a simple OHA window and call the Rust `oha-ffi` analysis API on an in-memory UTF-8 sample when the user presses a button. Neither UI creates, lists, tests or extracts archives.

The GitHub `M0 Native UI Shells` workflow builds the Windows application on Windows x64, compiles the SwiftUI application on macOS arm64 and Intel, and executes a real standalone Swift foreign-caller smoke on both. UI interaction, accessibility, packaging, signing, notarization, deployment prerequisites, main-thread responsiveness for long operations, progress/cancel, and native integration tests are not verified by compilation. Issue #6 remains open.

## Running locally

Windows: build the Rust `oha-ffi` crate in the same checkout (`cargo build -p oha-ffi --locked`). Build the WinUI project with .NET 10 and the Windows SDK (`dotnet build apps/oha-windows/OHA.Windows.csproj -p:Platform=x64`), then copy the matching `target/debug/oha_ffi.dll` alongside the app executable before launching. Windows App Runtime is required for this framework-dependent unpackaged app; there is no signed installer yet.

macOS: build the Rust library (`cargo build -p oha-ffi --locked`), then use `swiftc -parse-as-library -import-objc-header include/oha_ffi.h -L target/debug -loha_ffi apps/oha-macos/OHAApp.swift -o OHA`. The `.dylib` must be discoverable at runtime, e.g. through an appropriate bundle placement and `@rpath` configuration. This sample is **not a distributable `.app` bundle** and is not notarized. Use Xcode tooling appropriate to the target OS.

A successful desktop CI build proves compilation/linkage only. No public FFI ABI or `.oha` format is frozen.

For the SwiftUI shell, the repository root `Package.swift` defines a local Swift Package Manager executable and `include/module.modulemap` exports the canonical C ABI header as the `COHAFFI` module. Use `swift build -c release` after building Rust. This is an executable compilation probe rather than a packaged `.app`. The SwiftPM build is also traced by the CodeQL Swift job; direct `swiftc` foreign-caller smoke remains separate.
