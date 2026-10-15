# `.oha` format - design constraints, not a published specification

**Status: Unfrozen design draft.** This document deliberately does **not** allocate a magic value, wire version, numeric codec registry or byte offsets. Do not create an incompatible archive writer that pretends these are stable.

## Archive logical model

- Header: magic, format major/minor, mandatory/optional feature flags, bounded structural offsets.
- Payload records: independently verifiable compressed blocks or bounded solid groups; codec ID, decoder parameters, original/encoded byte lengths; optional dictionary references.
- Manifest: exact file mapping to segments with logical safe relative path, original size, attributes and platform metadata.
- Index: bounded mapping from file IDs / block IDs to record offsets for random access.
- Footer/commit record: durable pointer to the latest verified manifest and its integrity.
- Snapshot manifest (later M3): chunk references and version graph with transaction/generation ID.

All lengths and offsets must be checked with overflow-safe arithmetic **before reading or allocating**. Numeric byte order, canonical path rules, limits, checksum framing and exact record layouts will be decided before M1 writer implementation.

## Compatibility rules

1. All required decoder inputs are in the archive. No external dictionaries, baseline files, network dependencies or nonstandard dynamic codec downloads.
2. Separate file format version, codec version, ABI version and app version.
3. Decoder rejects unknown mandatory features/codec IDs; optional features may be ignored only if declared noncritical and their bytes can be safely skipped.
4. File contents are lossless and compare exactly after extraction. Metadata portability is explicit and cannot be silently claimed.
5. Archive extensions are hints; validate magic, checksums and structure regardless of filename.
6. A valid physical archive may contain the same bytes in multiple logical files. Cross-file dedup refs must be collision-safe (hash plus bytewise validation on dedup insertion/restore integrity checking as required).
7. Truncated or corrupt archives fail cleanly. Previous valid snapshot remains accessible if append/update interrupted.
8. No `../`, absolute paths, NUL, drive paths, device names or unsafe link targets may escape extraction root. Detect name collisions under target filesystem semantics.
9. Do not trust stored original sizes, counts, nesting depth or CPU/runtime hints without independent application limits.
10. Checksum does not authenticate unencrypted archives against deliberate attackers; encryption authenticates content/manifest/index.

## Decisions required before stable wire v1

- Precise magic, record framing, endianness and fixed-width field sizes.
- Index ordering, offset encoding, path representation, duplicate names and hard/symlink semantics.
- Codec registry, parameters, dictionary dependencies, unknown codec behavior.
- Integrity domains: per-segment, index, footer; snapshot transaction pattern.
- Encryption envelope and nonce domain separation, KDF memory policies, metadata confidentiality and dedup privacy.
- Maximum sizes and limits, independent verification decoder and cross-platform golden vectors.

**M0 design gate:** owner-approved written wire proposal and codec registry, explicit path/metadata/resource policies and negative bounded research vectors. **Before publishing any stable wire format in M1 or later:** independently implemented encoder/decoder prototypes, invalid corpus/fuzz checks and cross-OS end-to-end conformance. Until then `.oha` is reserved naming only.

## Concrete proposal for review (not approved)

`FORMAT_V1_PROPOSAL.md` documents tentative header/frame/footer offsets, two codec IDs and CRC32C semantics. A Python **read-only header/footer probe** and negative tests exercise this proposed framing only. No production writer or archive decoder exists, no format identifier is frozen, and all decisions in the preceding section remain subject to approval.
