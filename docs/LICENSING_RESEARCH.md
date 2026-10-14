# OHA licensing due diligence (M0, 2026-10-14)

**Status: RESEARCH ONLY. The owner has not selected or granted an OHA license.**

## Current dependencies, verified from repository manifests

- Cargo.lock contains only the four local OHA packages. No third-party Rust crate or compression library is linked into the core today.
- Windows uses Microsoft.WindowsAppSDK 1.8.260317003 and Microsoft.Windows.SDK.BuildTools 10.0.26100.7175. The self-contained GUI preview includes third-party Microsoft runtime binaries.
- macOS references SwiftUI/AppKit system frameworks and OHA's own Rust dylib. No external SwiftPM packages are declared.
- 7z/xz/zstd research executables are benchmark tools, not bundled in OHA output.

## Proposed OHA source license (approval pending)

Prefer **MIT OR Apache-2.0** for project-owned Rust, C#, Swift, C headers, tests and scripts. Each recipient chooses MIT or Apache-2.0, as explicitly described by Cargo's SPDX documentation: https://doc.rust-lang.org/cargo/reference/manifest.html. This supports commercial reuse and patent clarity, but permits closed-source forks. It does not relicense third-party code.

Alternative if modified files must remain open: MPL-2.0 (file-level copyleft). GPL-3.0 would be stronger copyleft with additional distribution constraints. MIT alone is simpler but lacks Apache's explicit patent terms. The owner must decide the goal, confirm copyright attribution and approve any release grant.

## Candidate codec licenses

| Candidate | Upstream license/scope | Proposed action |
|---|---|---|
| Zstandard libzstd | BSD-3-Clause in upstream LICENSE; alternative GPL licensing available | Choose BSD-3-Clause for integration; retain notices. Audit exact zstd/zstd-safe/zstd-sys wrapper and bundled C version. |
| XZ Utils liblzma | 0BSD; other XZ scripts/build files may be GPL/LGPL | Prefer specifically liblzma, not wholesale XZ tree; verify pinned sources. |
| LZ4 library | BSD-2-Clause within lib/; CLI and other files may use GPL-2.0-or-later | Use only approved library sources/wrappers. |
| BZip3 | LGPL-3.0-only runtime; libsais is Apache-2.0 | HOLD until explicit evaluation of linking, relinkability, licenses, notices and App Store packaging. |
| 7-Zip implementation | Predominantly LGPL-2.1-or-later; RAR component has unRAR restrictions | External 7z benchmarking only. Do not embed 7-Zip code by default. |
| BLAKE3 (future M3) | CC0-1.0 / Apache-2.0 alternatives | Check specific pinned crate and component. |
| FastCDC Rust (future M3) | MIT per upstream Cargo manifest | Check pinned crate and transitive dependencies. |

Primary license sources:
- https://github.com/facebook/zstd/blob/dev/LICENSE
- https://github.com/tukaani-project/xz/blob/master/COPYING
- https://github.com/lz4/lz4/blob/dev/LICENSE
- https://github.com/iczelia/bzip3
- https://github.com/ip7z/7zip/blob/main/DOC/License.txt
- https://github.com/BLAKE3-team/BLAKE3
- https://github.com/nlfiedler/fastcdc-rs/blob/master/Cargo.toml

## Windows self-contained redistribution is a separate gate

The actual Microsoft Windows App SDK 1.8.260317003 package license (https://www.nuget.org/packages/Microsoft.WindowsAppSDK/1.8.260317003/License) permits distributing NuGet-bundled application binaries subject to section 3 restrictions. Those include: significant primary functionality, appropriate terms protecting Microsoft's code for distributors and external users, and indemnity/trademark/redistribution conditions. An OHA MIT/Apache license does **not** extend to Microsoft DLLs.

Before distributing a self-contained Windows preview or production ZIP as a redistributable product: identify every bundled NuGet/.NET/WinRT artifact and its exact license, verify allowed files, include required third-party terms, and obtain a defensible end-user-terms/acceptance model. The M0 probe might not satisfy 'significant primary functionality'; do not assume release clearance. An unrelated upstream issue reports an Engineering Preview license discrepancy in WinUI 2.3.x; OHA pins Windows App SDK 1.8.x, so those exact affected packages are not established in OHA. See https://github.com/microsoft/WindowsAppSDK/issues/6654.

## Release compliance after approval

1. Add verbatim LICENSE-MIT and LICENSE-APACHE only after explicit owner approval (or different chosen license). Set Cargo.workspace package license and inheritance in local crates. Keep project authorship accurate.
2. Add README license declaration, CONTRIBUTING inbound=outbound contribution rule, and appropriate SPDX headers.
3. Ship THIRD_PARTY_NOTICES plus required full license texts for actual embedded dependencies in each Windows/macOS/Linux deliverable, not just a source repository page.
4. Gate every new codec/version or change to binary packaging on license provenance, transitive dependencies, feature flags, compile/linkage method, and exact shipped binary inventory.
5. Introduce Cargo, NuGet and release-artifact license/SBOM checks in CI; do not whitelist GPL/LGPL or unknown licenses without owner review.
6. Do not infer that a codec's whole tree shares the permissive license of its core library. Do not treat use of external 7z for local benchmarks as redistribution of its implementation.

**Decision OPEN:** copyright holder, preferred OHA source license and release redistribution obligations remain unapproved. Issue #4 must stay open.
