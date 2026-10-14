# OHA security threat model (M0)

## Assets

User file confidentiality; integrity of extracted bytes and metadata; filesystem integrity; backup snapshot availability; bounded CPU/RAM/disk; signing keys; trust in GUI/CLI native bridges.

## Adversaries and inputs

Malformed archives from untrusted third parties, crafted compressed streams, hostile pathnames/symlink/hardlink graphs, corrupt snapshots, pre-compressed bombs, malicious media containers misclassified by analyzer, interrupted writes, FFI misuse and untrusted build dependencies. The *archive itself* is never trusted, even when produced by OHA.

## Required guards

- Streaming parse; cap every count, size, offset, nesting depth, dictionary, decompressed output, time budget and concurrency before allocation/operation. Validate integer arithmetic.
- Check path normalization/absolute/traversal/device names, case-insensitive and Unicode normalization collisions on extraction platform. Default deny suspicious links, special files and unexpected overwrite. Use file-descriptor-relative extraction primitives where available to defend against symlink races; don't rely on string path checks alone.
- Cap total extracted bytes and max per-file bytes based on explicit user/system quotas; do not assume huge compression ratio is itself malicious.
- Do not follow input symlinks by default when archiving. Capture link metadata only if policy permits. Avoid TOCTOU on input files changing during read; surface consistency risk.
- Detect corrupt records, duplicate IDs, missing dictionary/chunk refs, length mismatches and invalid indexes without panic.
- Embedded codecs are untrusted native code from a trust-boundary perspective. Consider subprocess isolation for high-risk decoders, and fuzz their adapters.
- Unknown codec/version: reject; never fetch external decoder plugins or execute instructions embedded in archives.
- For encrypted archives use reviewed AEAD with key/nonce uniqueness, Argon2id password derivation and complete index/manifest authentication. Do not invent nonce derivations; obtain independent cryptographic review before release.
- Reused plaintext hashes leak cross-archive equality if exposed; encrypted snapshot dedup scope, keyed IDs and leakage model require a specific design review.
- Clear secret buffers where practical, never log keys/passwords/plaintext file contents. No diagnostic telemetry.
- Backup append: new generation becomes visible only after durable commit. Recovery chooses latest structurally valid snapshot, not necessarily latest footer bytes.
- Builds: pin all actions and dependencies, SBOM, license scans, secret scan, SAST, cross-platform compatibility tests; release assets should be signed when infrastructure exists.

## Testing gate

Property tests for parser invariants; fuzz on archive bytes; path traversal variants including Windows reserved names and NTFS ADS; zip-bomb-like decompression limits; cancellation during writes; interrupted snapshots; metadata collision; invalid FFI lengths; fuzz determinism. Manual audits before enabling encryption or publishing stable wire spec.

## Non-goals at M0

No encryption module, no production file parser, no promises of secure archive extraction. The M0 research prototype reads local input bytes only.
