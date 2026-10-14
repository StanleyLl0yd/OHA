# OHA roadmap

Version numbers are purely numeric; no alpha/beta/rc suffixes. Milestone completion always triggers mandatory complete repository-wide audit, deep refactor/review and verified all-platform gates (`AGENTS.md`).

## M0: Architecture & Research (ACTIVE)

Deliverables:
- [x] Product brand OHA / `.oha` and platform architecture recorded.
- [x] Architecture, threat model, initial decision engine and format constraints documented.
- [x] Dependency-free Rust analyzer + selector research scaffold prepared (not yet compiled).
- [x] Portable benchmark harness and synthetic smoke corpus created; local Python tests executed successfully.
- [x] Verify Rust 1.89 toolchain and execute Linux x86_64, Windows x64, and macOS arm64 builds, fmt, Clippy and Rust tests (GitHub Actions PR #1).
- [x] Verify macOS x86_64 runner Rust fmt, Clippy, tests and build (PR #1).
- [ ] Validate native GUI/FFI targets; a bounded Rust C ABI/foreign-caller smoke prototype is in progress.
- [ ] Complete real diverse benchmark corpora and independent 7-Zip, ZSTD, XZ/LZMA2 archive baselines with extraction and memory measurements. Initial 9-file/108-roundtrip real codec probe and six verified TAR+ZSTD/XZ multi-file archive runs recorded; 7-Zip, RSS, holdout and random extraction pending.
- [ ] Resolve project distribution license and codec redistribution/licensing policy.
- [ ] Review/approve v1 `.oha` wire format design and codec registry (actual implementation belongs to M1). Preliminary framing proposal and read-only negative tests prepared.
- [ ] Minimal native GUI prototypes, compile on Windows/macOS and validate Rust FFI semantics.
- [ ] Full M0 repository-wide two-pass audit, security review, and final CI evidence.

Exit: research results with evidence, reviewed architecture/format proposal, demonstrated cross-platform builds/ABI, verified dependencies/licenses, full audit. Until then M0 remains open.

## M1: Minimal working archive

STORE + ZSTD streaming codec, standalone `.oha` format, indexed file tree, CLI pack/list/extract/test, bounded extraction, independent conformance tests and native minimal Windows/macOS GUI calling shared API. No unsupported security claims.

## M2: Adaptive archive compression

Sample-based selection, calibrated candidate set, LZMA2 after legal review, bounded solid groups/dictionaries, robust fallback; compare to simple ZSTD/7z baselines on independent datasets.

## M3: Smart Backup

Content-defined chunks (FastCDC candidate), BLAKE3, deduplication, transactional snapshots, safe restoration, interruption/recovery tests; compare to established backup tools.

## M4: Encryption/security hardening

Reviewed AEAD, Argon2id KDF, metadata authentication/confidentiality, key-handling policy and dedup leakage treatment, independent security tests/audit.

## M5: Native desktop completeness

Windows WinUI 3/C# and macOS SwiftUI/AppKit/Swift functional parity, shell integrations, accessibility, localization, large file trees, packaging/notarization/signing. Linux remains full CLI.

## M6: Optimization and production release

Cross-platform benchmark regression suite, fuzz coverage, deterministic conformance corpus, packaging, signed release with provenance and common version, full repository-wide exit audit.
