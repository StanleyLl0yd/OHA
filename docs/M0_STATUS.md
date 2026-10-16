# OHA M0 status and evidence map

**Date:** 2026-10-14. **Milestone:** M0 Architecture & Research, **OPEN**. Baseline main when this document was reconciled: `4daffbb60de87b66804d73fde83b37ce58881dce`.

**There is NO production `.oha` archive writer, reader, pack, extract or encryption implementation.** The CLI only analyzes local file samples. All physical wire proposals and path policy experiments are unapproved research. A build-green desktop shell is not interactive GUI acceptance.

## Confirmed work

| Gate / component | Evidence | State |
|---|---|---|
| Repository source, MPL-2.0, branch security | PR #1, #8, #19, #20; active main/tag rulesets | PASS for source and branch policy |
| Rust Core research and CLI | Rust 1.89.0 CI on Linux x64, Windows x64, macOS ARM64 and Intel | PASS |
| FFI boundary | PR #10, #12, #14: Rust/ctypes, C# PInvoke and Swift native ABI smoke | PASS for bounded synchronous in-memory probe |
| Native WinUI 3 and SwiftUI/AppKit shells | PR #12/#14; protected `verify` includes native builds and foreign callers | PASS compilation/interop, not user GUI acceptance |
| Native preview bundles | PR #15/#19; Windows self-contained preview and macOS ARM64/Intel ad-hoc bundles | 3/3 packaged; unsigned/non-notarized |
| Python/SAST/supply chain | Rust CI, Python regression, Semgrep, Gitleaks, Dependency Review (PR), 5-language CodeQL; SHA-pinned Actions | PASS on baseline main |
| Independent compression reference | PR #11/#18: 7-Zip LZMA2 solid/non-solid, TAR+XZ/ZSTD, SHA-256 roundtrip and selected-file extract on source-controlled/provenance-pinned corpora | PASS exploratory measurements only |
| Binary inventory | PR #20: manifest SHA-256 + source provenance from real Windows/macOS artifact, candidate native dependency list | PASS inventory; **not** release legal clearance |
| Format research | PR #13: header/footer and frame CRC/limits; PR #21 and PR #22 merged in main (physical envelope and portable-path research, not approved format); PR #24 is a further deterministic CBOR metadata proposal under review | Research only; no full archive conformance |

## OPEN M0 exit blockers

1. **#3: Benchmark representativeness.** Extend to precompressed media, database/VM data and holdout sets; record cold/warm cache, noise/dispersion, memory, time and extraction metrics. No claim OHA outperforms anything before a real writer exists.
2. **#40: Third-party binary redistribution.** Original OHA source is already MPL-2.0 and source-license issue #4 was closed by the owner; exact Windows App SDK/.NET/WinRT self-contained licenses and notice/end-user term requirements need a versioned binary-by-binary decision. BZip3 and 7-Zip code remain on hold.
3. **#5: Format approval.** Decide canonical manifest/index encoding, portable filename semantics, codec/feature registry, quotas, metadata rejection/portability and future version behavior. Candidate read-only research is not a standard. Approval must precede M1 implementation.
4. **#6 and #16: Native GUI on devices.** WinUI/SwiftUI compilation and FFI calls are confirmed, but there is no physical-device, interactive GUI acceptance. Unsigned M0 artifact provenance must be verified before launching; signing/notarization and production packaging are later gates.
5. **#7: Mandatory milestone-wide two-pass audit.** Run twice over the *entire* repository, dependencies, source, CI, docs, tests, platform integration, security and candidate format after all preceding gates. Record fixes, intentional no-ops and exact-main final CI. Do not close M0 early.

## M0 vs M1 boundary

M0 is architecture/research/accepted contracts/verified prototypes. It **does not** implement a usable OHA archive. M1 builds the first accepted STORE+ZSTD archive writer/reader, CLI pack/list/test/extract and independent conformance/fuzz/security testing. The draft format's conformance requirement before publication of a **stable** format is a later release gate, not evidence that M0 already implemented a decoder.

The first 44-file import, early test counts and preliminary prototypes were superseded by subsequent merged PRs. Use GitHub's protected `verify`, CodeQL, benchmark and native preview runs for current proof rather than historical static numbers.
