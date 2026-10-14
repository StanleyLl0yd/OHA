# ADR 0002 - Wire format evolution and compatibility

Status: Proposed (2026-10-14), subject to M1 implementation/conformance

1. `.oha` is a brand and file extension, not proof of file identity. The binary magic and version govern recognition.
2. Do not publish a stable production-format version in M0. No experimental writer should emit production-like files that later need incompatible parsing.
3. Format readers must reject unsupported mandatory features, overflows and unknown mandatory codec IDs, and must bound sizes before allocation.
4. Codec metadata are versioned independently of application versions. Dictionary dependencies must be embedded and verifiable.
5. Logical paths and metadata must be portable; extraction strategies are platform-specific and conservative.
6. The first production writer must have independently generated conformance test vectors and two decoders before the format is called stable.
7. Non-encrypted integrity checks protect against accidental damage, not active archive forgery. AEAD authentication is mandatory for encrypted archives.
8. Snapshot updates use a transactional commit record; incomplete writes must not replace the last valid state.
