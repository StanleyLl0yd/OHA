# ADR 0001 - Product, platforms and code ownership

Status: Accepted by project direction (2026-10-14)

Decision: OHA (Optimized Hybrid Archiver), extension `.oha`; offline Rust core with Windows native WinUI 3/C#, macOS native SwiftUI/AppKit/Swift and Linux Rust CLI. `oha-archiver` command instead of `oha` due to name conflict.

Consequences: GUI code duplicated only at presentation layer. Contracts and feature completeness tested at common Rust core level. GUI on Linux deferred but architecture must permit later addition. Rust/C ABI compatibility and platform packaging are first-class release gates. No server component.

Alternatives discussed: shared Slint/Qt GUI, three separate desktop GUIs. Native Windows/macOS plus Linux CLI chosen to control UI engineering scope while retaining cross-platform engine.
