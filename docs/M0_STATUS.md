# M0 current status

Updated 2026-10-14 following GitHub repository creation and import PR #1. M0 remains OPEN.

## Verified and completed

- Public GitHub repository `StanleyLl0yd/OHA` created; 44-file scaffold imported in draft PR #1.
- Core brand OHA, `.oha`, offline Rust core, Windows WinUI 3/C#, macOS SwiftUI/AppKit and Linux CLI architecture fixed.
- Four ADRs, architecture/security/format/policy documentation, numeric-only versioning and mandatory two-pass whole-repository milestone exit audit in `AGENTS.md`.
- Rust 1.89.0 workspace fmt, Clippy (`-D warnings`), unit tests and build PASSED GitHub Actions on Linux x86_64, Windows x64 and macOS arm64 after formatting fix (PR #1).
- Python 28/28 unit tests PASSED; 72 synthetic and 108 individual real-file codec roundtrips SHA-256 verified, plus six TAR+ZSTD/XZ verified runs. Baselines are illustrative, not representative head-to-head archive performance claims.
- Candidate v1 framing proposal with read-only CRC32C parser and negative tests. No actual `.oha` archive writer or reader exists.
- License options and codec redistributability research documented; no LICENSE approved or added.

## Outstanding M0 gates (tracked in issues #2 through #7)

1. Confirm all required Rust CI variants including macOS x86_64; generate/validate committed Cargo.lock and final-main CI evidence (#2).
2. Independent realistic 7-Zip and other archive baselines including extraction, peak RSS and random-access measures (#3).
3. Owner-approved repository license and third-party codec redistribution policy (#4).
4. Review and approve byte-precise `.oha` format and codec registry, with independent vectors (#5).
5. Build/validate native WinUI and SwiftUI/AppKit GUI/FFI smoke prototypes (#6).
6. Final mandatory complete two-pass repository-wide audit and full exit verification (#7).

Do not close M0 or start M1 before all exit criteria are supported by evidence.

## Security and CI subsequent updates

- PR #8 merged: strict `verify` on Linux/Windows/macOS and Python, Semgrep, Gitleaks, Dependency Review and CodeQL; main ruleset and immutable release tags active.
- PR #9 merged: SHA-pinned CodeQL Action update.
- Experimental Rust C ABI and cross-language smoke tests tracked under #6; they are **not** the complete native GUI/FFI acceptance criterion.

## Next M0 benchmark work

- Independent 7-Zip LZMA2 archive and selective-extraction harness prepared for CI validation. No representative performance claim or complete holdout corpus yet; #3 remains open.

## Native UI M0 work

- C ABI successfully verified via Rust and Python foreign caller on four OS runners (PR #10).
- Minimal native Windows WinUI 3/C# and macOS SwiftUI/AppKit visual shells prepared for hosted compilation; see `docs/NATIVE_UI_M0.md`. No native user interaction or installation/signing validated yet (#6 remains open).
