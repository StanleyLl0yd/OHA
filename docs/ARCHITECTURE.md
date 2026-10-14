# Architecture baseline (M0)

## Logical boundaries

```text
Windows WinUI3/C#         macOS SwiftUI+AppKit/Swift       Cross-platform Rust CLI
         \                         |                         /
          \             Stable application contract        /
           +----------------------+------------------------+
                                  |
                         Rust application service
                      jobs / progress / cancellation
                                  |
            +---------------------+---------------------+
            |                     |                     |
         Analyzer             Decision engine        Container I/O
            |                     |                     |
       Codec sampling         Resource scheduler       Manifest/index
            |                     |                     |
            +---------------------+---------------------+
                                  |
                          Codec registry / STORE
                                  |
                Platform I/O + safe extraction + integrity
```

- Rust owns every operation and state transition. The GUI is presentation and local platform integration only.
- Expose an object/handle-based, versioned C ABI to .NET P/Invoke and Swift. Rust CLI uses Rust API directly. No language-specific string IDs inside the core.
- Long operations return operation handles and deliver bounded, sequenced progress events; cancellation is cooperative; retries are explicit.
- The C ABI must not expose Rust structs, panics, allocation ownership or threads across the boundary. Include a dedicated `free` API, stable error codes and ABI capability negotiation.
- No plugins that execute arbitrary code from `.oha` files. Codec identifiers are defined by a stable registry; unknown mandatory codecs fail explicitly.
- Linux CLI must be feature-complete as core capabilities mature; no GUI-only archive or recovery features.
- Windows GUI target: Windows 10 1809+ (verify exact Windows App SDK requirements on pinned version); WinUI 3 + C# with P/Invoke adapter.
- macOS GUI: SwiftUI plus AppKit for large file tables and Finder services; exact minimum macOS release determined during native build validation.
- Linux CLI: x86_64 mandatory; other architectures after dependency audit and runner availability.

## Strategic split: Archive vs Backup

- **Archive:** grouping and bounded solid streams improve ratio; independent index and optional seekable blocks permit targeted extraction.
- **Backup:** content-defined chunking and content-addressed deduplication improve successive snapshots; compress unique blocks, keep manifests transactional.
- Never assume deduplication + small independent blocks is always better than solid compression. Both must be benchmarked against baselines, with the total cost of metadata and dictionaries.

## Initial module layout

- `oha-analysis`: bounded sampling and neutral metrics, not policy decisions.
- `oha-policy`: deterministic choice scoring, Pareto filtering, budgets and explicit fallbacks.
- `oha-codecs` (M1): minimal STORE/ZSTD decoder/encoder interfaces, bounded streams.
- `oha-format` (M1): reader, writer, versioned index, checksums.
- `oha-core` (M1): application commands, tasks, cancellation, event sequencing.
- `oha-ffi` (M1): C ABI bindings, zero panics across FFI.
- `oha-dedup` (M3): chunker, content IDs and snapshot storage.
- `oha-crypto` (M4): secure key management and authenticated encryption.

Do not create empty packages for speculative future modules. Document them here until implemented.

## Format and path invariants

- Cross-platform format uses raw bytes for content, normalized logical paths, explicit metadata variants and endian/version declarations.
- A Windows-incompatible logical name must not be silently renamed on extraction. Require explicit user mapping policy or return a clear collision/error.
- Preserve source-platform metadata in the archive even when target OS cannot apply it; do not silently claim restored ACL/xattrs/forks.
- Decompression must be streaming/bounded. A malicious archive must not trigger attacker-controlled unbounded allocation, recursion or traversal.
- Archive write transaction must never overwrite/destroy last committed backup snapshot before new generation becomes valid.

## Delivery policy

Single numbered version and a common compatibility matrix across platforms. A release cannot be marked complete if any mandatory platform fails compatibility tests. Native installer and signature requirements are tracked separately from correct core/CLI builds.
