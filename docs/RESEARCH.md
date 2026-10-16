# M0 preliminary dependency research (2026-10-14)

| Component | Candidate | Status | Reason |
|---|---|---|---|
| Language/build | Rust 2024 edition, Cargo workspace | Selected | Cross-platform safety/performance and shared library/CLI |
| Windows UI | WinUI 3 C#/XAML | Selected | Native Fluent Windows UI |
| macOS UI | SwiftUI + AppKit | Selected | Native UI, large tables where AppKit needed |
| Linux UI | None initially | Deferred | Full Linux CLI first |
| Fast codec | ZSTD / libzstd | Preferred M1 | Good encode/decode speed and dictionary support |
| Fastest codec | LZ4 | Research M2 | May reduce decode latency |
| Dense codec | LZMA2 | Research M2 | Mature high-ratio codec; assess native bindings/distribution |
| Additional dense codec | BZip3 | Deferred | LGPL-3 review and measured benefit needed |
| Dedup chunker | FastCDC | Candidate M3 | Content-defined chunks withstand insertions |
| Dedup/content hash | BLAKE3 | Candidate M3 | Fast, parallel cryptographic hash |
| Password KDF | Argon2id | Candidate M4 | Memory-hard KDF |
| AEAD | XChaCha20-Poly1305 or AES-256-GCM | Decision pending | Must finalize nonce/key schema with audited library and review |

Do not assume license statements for wrappers are identical to native libraries. All legal/compliance decisions require verification from license files of selected *exact versions* and any linking/redistribution obligations.

Authoritative upstream references:
- Rust/Cargo workspaces: https://doc.rust-lang.org/cargo/reference/workspaces.html
- ZSTD: https://github.com/facebook/zstd and RFC 8878
- BZip3 licensing: https://github.com/iczelia/bzip3/blob/master/LICENSE
- FastCDC: https://www.usenix.org/conference/atc16/technical-sessions/presentation/xia
- BLAKE3: https://github.com/BLAKE3-team/BLAKE3
- Windows App SDK: https://learn.microsoft.com/en-us/windows/apps/winui
- SwiftUI/AppKit: https://developer.apple.com/documentation/swiftui/appkit-integration

## Licensing update (2026-10-16)

Original OHA source licensing is **accepted MPL-2.0**, recorded in root `LICENSE` and `docs/adr/0004-licensing.md`. This is distinct from the **OPEN** exact-version third-party binary redistribution gate (#4). `LICENSING_RESEARCH.md` inventories optional codec candidates and unapproved runtime redistribution obligations; a project source license does not grant vendor-runtime or benchmark-corpus rights. Current pinned manifest/package versions and preview inventory reports are inputs to, not completion of, that separate legal review.
