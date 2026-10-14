# Test matrix and compatibility contract

## M0 required validation (not yet completed)

| Target | Compile | Tests | GUI | Status |
|---|---|---|---|---|
| Linux x86_64 Rust CLI | cargo build | fmt, clippy, unit tests | Not required | Pending toolchain |
| Windows x64 Rust CLI | cargo build | unit/FFI validation | WinUI prototype | Pending runner |
| macOS arm64 Rust CLI | cargo build | unit/FFI validation | SwiftUI/AppKit prototype | Pending runner |
| macOS x86_64 Rust CLI | cargo build | unit/FFI validation | Same universal app | Pending runner |
| Windows ARM64 | Optional first release | Core tests where supported | Deferred official tier | Planned |
| Linux ARM64 | Optional first release | Core tests where supported | Not required | Planned |

## M1+ archive correctness

- Create `.oha` on each supported platform, decode on every other platform and byte-compare all restored regular files.
- Include filenames with normalization/case collisions, symlink attacks, long names, UNC/drive ambiguities, non-UTF-8 POSIX bytes, giant sparse files and platform metadata with nonrepresentable targets.
- All codecs and feature combinations included in mandatory decoder must work on x64 and ARM64 or be explicitly disallowed before creating incompatible archives.
- Archive commit interruption tests at every index/footer write boundary; no old snapshot can become inaccessible without clear recoverable corruption.
- Fuzz individual format header, record and manifest parsers; ensure bounded time, memory, recursion and output.
- Encryption release requires independent cryptographic review and test vectors including wrong password, modified ciphertext and nonce uniqueness.

## Performance comparison

Full and random access extraction, encoder time, decode time, peak RSS, archive bytes **including metadata**, repeatability, warm/cold caching, and heterogeneous corpora. Use declared baselines and record negative outcomes.
