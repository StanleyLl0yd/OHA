# OHA roadmap

Versions are **numeric only**, no alpha/beta/rc suffixes. After every milestone, `AGENTS.md` mandates two full repository-wide audit/review/refactoring passes plus final cross-platform verification.

## M0: Architecture & Research (ACTIVE)

- [x] OHA brand and `.oha` extension, offline Rust core, WinUI 3/C# for Windows, SwiftUI/AppKit for macOS and CLI-first Linux architecture fixed.
- [x] Rust 1.89 workspace analyzed, formatted, linted, tested and built on Linux x64, Windows x64 and macOS ARM64/Intel with protected CI (PR #1 and subsequent exact-main runs).
- [x] Experimental, bounded Rust C ABI plus ctypes, C# PInvoke, Swift foreign-caller smoke on supported runners (PR #10/#12/#14).
- [x] Minimal native WinUI and SwiftUI shells compiled, linked and packaged for three target configurations (PR #12/#15); native tests are required by protected `verify`.
- [x] Baseline real 7-Zip LZMA2 and TAR+ZSTD/XZ archive measurements, full/selected extraction SHA verification, metadata and RSS where measurable; pinned external Canterbury holdout probe (PR #11/#18).
- [x] Original source license is MPL-2.0, SPDX/inbound contribution policy and source notice in previews (PR #19).
- [x] Baseline architecture, threat model, draft framing and negative header/footer/frame tests.
- [ ] **#3** Expand benchmarking coverage and controlled methodology for media/VM/database, cold/warm repeats and honest uncertainty (no OHA archive performance claim).
- [ ] **#40** Audit exact bundled Windows App SDK/.NET/WinRT and future codec licenses; preserve full required third-party notices and redistributable terms. Preliminary machine inventories available (PR #20).
- [ ] **#5** Review and approve the complete candidate v1 `.oha` physical/manifest/index/portable-name and codec contracts. Code remains research-only until accepted.
- [ ] **#6/#16** Verify native previews interactively on physical Windows/macOS devices, record actual build/OS/CPU/UX acceptance.
- [ ] **#7** Complete both entire-repository exit audit passes and all exact-main cross-platform CI/security checks, with evidence.

**M0 exit:** accepted architecture/format proposal and dependency policy, defensible benchmark and platform evidence, GUI device acceptance and two-pass audit. Remain M0 until all gates are met. Do not implement or claim a stable archive writer as part of the preliminary parser probes.

## M1: Minimal working archive

Approved standalone `.oha` STORE+ZSTD streaming writer/reader, indexed file tree, CLI pack/list/extract/test, bounded extraction, independent conformance vectors and native minimal GUI calling the same core. No unsupported security or stable-format claim until tested.

## M2: Adaptive archive compression

Measured sample-based codec selection, LZMA2 after licensing review, bounded solid groups and dictionaries; independent held-out comparison to simple ZSTD/7z baselines.

## M3: Smart Backup

FastCDC candidate, BLAKE3, deduplication, transactional snapshots and interruption/recovery tests, reproducible backup comparison.

## M4: Encryption/security hardening

Reviewed authenticated encryption, Argon2id KDF, protected manifest/index, key handling and dedup leakage policy, independent crypto review.

## M5: Native desktop completeness

WinUI 3 and SwiftUI/AppKit functional parity, shell integration, accessibility/localization, large file trees, packaging, notarization and code signing; Linux remains full CLI.

## M6: Optimization and production release

Platform benchmark regression, fuzz/conformance corpus, provenance and signed packaging, final release audit. Every milestone has its own two-pass repository-wide exit audit.
