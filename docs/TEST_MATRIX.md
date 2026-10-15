# Test matrix and compatibility contract

## M0 verified cross-platform CI

| Target | Rust fmt/Clippy/test/build | Foreign caller | Native GUI compilation | Device launch |
|---|---|---|---|---|
| Linux x64 | PASS | Python ctypes PASS | Not required | Not required |
| Windows x64 | PASS | Python ctypes + C# PInvoke PASS | WinUI 3 PASS | Pending #16 |
| macOS ARM64 | PASS | Python ctypes + Swift PASS | SwiftUI/AppKit PASS | Pending #16 |
| macOS Intel | PASS | Python ctypes + Swift PASS | SwiftUI/AppKit PASS | Pending #16 |
| Windows ARM64 | Not official initial target | Not verified | Deferred | Deferred |
| Linux ARM64 | Not official initial target | Not verified | CLI-only future | Deferred |

Protected GitHub `verify` requires the four Rust runners, Python, Semgrep, Gitleaks, Dependency Review on PRs, WinUI compile+PInvoke and both macOS SwiftUI+foreign-caller smoke. CodeQL runs separately for Rust/Python/Actions/C#/Swift. These checks are compilation and ABI correctness, **not** safe archive extraction or graphical-device acceptance.

M0 format research currently validates candidate header/footer, DATA/MNFT/INDX framing and CRC/budgets, but no real archive writer/reader or compressed DATA verifier exists. PR #21 and #22 added bounded physical envelope integrity and portable-name research. PR #24 proposes deterministic CBOR metadata. All need accepted format/OS semantics before production use.

## M1 and later correctness requirements

- Create `.oha` on every supported platform, decode on each other and SHA-256 compare all restored regular files.
- Reject traversal, symlinks/TOCTOU, Unicode/Windows name collisions, device/ADS, non-UTF-8 POSIX names and unsupported metadata explicitly; use descriptor-relative safe extraction or platform-equivalent primitives.
- All mandatory codecs/features decode identically on x64/ARM64 or are explicitly unsupported in encoder before creating incompatible archives.
- Bounded time, RAM, total decompression size, file count, depth and record allocations; fuzz headers, index, manifest, records and extraction path handling.
- Interrupted writes must preserve previously completed archives and report errors without silent data loss; later snapshot recovery follows M3 only.
- M4 encryption adds independent cryptographic review, tampered-ciphertext, wrong-password and key/nonce uniqueness tests.

## Performance comparisons

Measure real packed archive bytes **including metadata** and independent 7-Zip/ZSTD/XZ baselines; report full/selected extraction, encoding, decoding, peak RSS, cold/warm cache, held-out heterogeneous corpora and negative outcomes. No claim of actual OHA archive performance until M1 writer exists.
