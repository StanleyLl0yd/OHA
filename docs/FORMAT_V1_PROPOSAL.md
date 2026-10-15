# Candidate `.oha` wire format v1 (M0 design proposal only)

**UNAPPROVED, NOT STABLE, NOT IMPLEMENTED.** The byte values and structure below are a concrete review proposal, *not* a public format, commitment, or a compatible file writer. Do not publish `.oha` files from these layouts or implement an encoder before the owner signs off. The canonical constraints in `FORMAT_DRAFT.md` continue to apply.

## Scope / upgrade discipline

M1: immutable single-generation archives containing regular files and directories only, STORE and ZSTD. No encryption, append updates, deduplication, external dictionaries, symlinks, hardlinks, NTFS alternate streams or complete ACL/fork preservation. Unsupported files/metadata must be reported explicitly, never silently dropped or flattened. No guarantees about malicious archives are made until a hardened implementation is tested and reviewed.

M3 backup snapshots, transactions/append, and M4 AEAD require separately specified versioned features. An M1 decoder rejects unknown *required* features rather than guessing; it must never execute archive-defined codecs or fetch plugins. No unauthenticated checksum can prove authenticity.

All integer fields are **unsigned little-endian** except declared timestamps. All offsets refer to absolute bytes from start of archive; all lengths include or exclude headers exactly as labelled. Unsigned arithmetic must be checked before parsing/allocating/reading. The appendix contains limited proposed header/footer vectors, **not** a full conformance corpus.

## 1. 64-byte archive header at offset zero

| Offset | Size | Type | Meaning (proposed) |
|---|---:|---|---|
| 0 | 8 | bytes | `4F 48 41 1A 0D 0A 00 01` (`OHA` + binary marker) |
| 8 | 2 | u16 | format major = 1 |
| 10 | 2 | u16 | format minor = 0 |
| 12 | 4 | u32 | header length = 64 |
| 16 | 4 | u32 | required feature mask = 0 in M1 |
| 20 | 4 | u32 | optional feature mask = 0 in M1 |
| 24 | 32 | bytes | reserved, must be zero |
| 56 | 4 | u32 | CRC32C over bytes 0..55 |
| 60 | 4 | u32 | reserved, must be zero |

CRC32C uses reflected Castagnoli polynomial `0x82F63B78`, init and xor-out `0xFFFFFFFF`; test string `123456789` -> `E3069283`. CRC is accidental-corruption detection only. Unknown version or required/optional flags in research v1 are rejected; future optional flags require explicit skippability semantics.

## 2. Physical frame sequence (candidate)

`header | zero or more DATA frames | one MNFT frame | one INDX frame | footer`

No unreferenced trailing garbage, overlapping frames, duplicate block IDs, holes except specifically encoded alignment records (none in M1), or alternate footer locations. The file length must equal the footer's declared total length. Writer creates a new temporary file and atomically replaces the destination *after* fsync/flush semantics are checked on each OS; **M1 never modifies existing `.oha` archives in place**. This avoids making an unsupported crash-recovery claim for append operations.

### 80-byte frame header (candidate, before payload)

| Offset | Size | Type | Description |
|---|---:|---|---|
| 0 | 4 | bytes | `DATA`, `MNFT`, or `INDX` |
| 4 | 2 | u16 | fixed frame header length = 80 |
| 6 | 2 | u16 | frame version = 1 |
| 8 | 4 | u32 | flags = 0 |
| 12 | 8 | u64 | payload byte length, excluding frame header |
| 20 | 8 | u64 | fully decoded content length |
| 28 | 8 | u64 | unique block ID for DATA; zero for metadata |
| 36 | 2 | u16 | codec ID: 0 = STORE, 1 = ZSTD |
| 38 | 2 | u16 | codec parameter length; zero in this proposal |
| 40 | 32 | bytes | SHA-256 of decoded bytes (not authenticated) |
| 72 | 4 | u32 | CRC32C over frame header bytes 0..71 |
| 76 | 4 | u32 | reserved zero |

For MNFT/INDX only STORE is legal at M1; decoded length must equal payload length. STORE DATA likewise requires equal sizes. ZSTD is a self-contained RFC 8878 frame with no external dictionary. Frames decode into bounded buffers/streams and must match declared length and SHA256. Avoid trusting codec-advertised decompressed lengths for allocation.

## 3. Footer: final 128 bytes at EOF

| Offset | Size | Type | Meaning |
|---|---:|---|---|
| 0 | 8 | bytes | ASCII `OHAEND1` then `00` |
| 8 | 8 | u64 | total archive bytes, including footer |
| 16 | 8 | u64 | MNFT frame absolute offset |
| 24 | 8 | u64 | MNFT frame total bytes (header + payload) |
| 32 | 8 | u64 | INDX frame absolute offset |
| 40 | 8 | u64 | INDX frame total bytes |
| 48 | 8 | u64 | generation = 1 in M1 |
| 56 | 32 | bytes | SHA-256 of MNFT **payload** (not authenticated) |
| 88 | 32 | bytes | SHA-256 of INDX **payload** (not authenticated) |
| 120 | 4 | u32 | CRC32C over bytes 0..119 |
| 124 | 4 | u32 | reserved zero |

Range checks precede all reads. MNFT must end at or before INDX, INDX ends exactly at footer, and both contain complete 80-byte frame headers. Footer SHA must be validated against full referenced metadata bytes, and frame SHA must agree. Reading the footer itself never grants trust in archive paths, sizes, frame contents or authenticity.

## 4. Unresolved items before format approval

- **Canonical manifest and index byte serialization**: path encoding/normalization, file mapping, exact offset tables, file hash semantics, file metadata and ordering. Candidate: length-prefixed UTF-8 NFC relative paths with `/`; strict Windows device/ADS/casefold compatibility checks at extraction. POSIX undecodable filenames require explicit refusal/export policy, not lossy conversion.
- Quotas and resource budgets: proposed defaults `DATA` decoded frame <= 16 MiB, max path <= 4096 UTF-8 bytes, <= 1,000,000 entries, maximum decoded total configurable, and maximum archive metadata processing budget. Exact accepted limits and low-memory streaming behavior need implementation profiling.
- SHA-256 vs BLAKE3 for content hashes and eventual M3; avoid rolling own cryptography.
- Optional feature rule, unknown frame skipping, ZSTD dictionary policy and codec registry stability.
- Explicit supported timestamp granularity, ACL/xattr handling and platform error reporting.
- Windows/macOS/Linux golden cross-decoder vectors and fuzzed invalid corpus.
- Future append/snapshot commit chain and AEAD envelope are **not** defined by this proposal.

## 5. Research verification

`tools/wire_header_probe.py` checks only header/footer structure and CRC32C without writing archives. `tests/test_wire_header_probe.py` includes the independently specified CRC32C standard vector and negative bounds, endian, version and corruption cases. The fixed research examples in `research/wire-v1-framing-vectors.json` are only framing examples, **not valid full archives or independent end-to-end vectors**. **A passing test is not archive-conformance or security certification.**

## M0 80-byte frame header research checks

The **unapproved** `DATA`, `MNFT`, and `INDX` frame proposal now has a read-only `validate_frame_header()` negative-test suite in `tools/wire_header_probe.py` and `tests/test_wire_header_probe.py`. It rejects unknown frame kinds, versions, flags, codecs, invalid block IDs, CRC32C corruption, declared size inconsistencies and over-budget frame lengths. The bounded default research limits are 16 MiB decoded and 18 MiB encoded bytes, each caller-overridable by a stricter budget; they are **not accepted public wire limits**. Hash verification, manifest/index serialization, compressed body validation, archive consistency and safe extraction remain unimplemented. No `.oha` writer or decoding claim follows from these tests.

## Physical envelope integrity research (M0, pending wire approval)

`tools/wire_header_probe.py::validate_candidate_envelope()` checks only a **bounded, in-memory candidate byte envelope**. It requires contiguous DATA records before exactly one MNFT and one INDX frame followed by the final footer; rejects duplicate block IDs, range/gap violations and frame CRC failures. It independently checks SHA-256 of all STORE DATA and both metadata payloads against record fields, and metadata digest against the footer. It tracks but **does not decode or authenticate ZSTD DATA**, reporting the count explicitly as `zstd_payloads_NOT_verified`. It does not interpret manifest/index payload bytes, validate filenames or paths, extract files, produce archives or prove any compressed stream is valid. Candidate default budgets: 64 MiB envelope, 4 MiB per metadata payload, 4096 DATA frames. These are research limits, not an accepted wire contract. Tests construct transient candidate buffers only and reject deliberate mutations. Owner approval and actual independent implementation are still required by #5.

## Candidate portable path semantics (research-only)

`tools/candidate_paths.py` and `tests/test_candidate_paths.py` implement a **conservative, non-extracting** manifest path eligibility and collision probe. The candidate requires relative `/`-separated NFC UTF-8, rejects parent traversal, symlinks/special entry types, Windows ADS/drive/reserved device names (including superscript COM/LPT digits, console names `CONIN# Candidate `.oha` wire format v1 (M0 design proposal only)

**UNAPPROVED, NOT STABLE, NOT IMPLEMENTED.** The byte values and structure below are a concrete review proposal, *not* a public format, commitment, or a compatible file writer. Do not publish `.oha` files from these layouts or implement an encoder before the owner signs off. The canonical constraints in `FORMAT_DRAFT.md` continue to apply.

## Scope / upgrade discipline

M1: immutable single-generation archives containing regular files and directories only, STORE and ZSTD. No encryption, append updates, deduplication, external dictionaries, symlinks, hardlinks, NTFS alternate streams or complete ACL/fork preservation. Unsupported files/metadata must be reported explicitly, never silently dropped or flattened. No guarantees about malicious archives are made until a hardened implementation is tested and reviewed.

M3 backup snapshots, transactions/append, and M4 AEAD require separately specified versioned features. An M1 decoder rejects unknown *required* features rather than guessing; it must never execute archive-defined codecs or fetch plugins. No unauthenticated checksum can prove authenticity.

All integer fields are **unsigned little-endian** except declared timestamps. All offsets refer to absolute bytes from start of archive; all lengths include or exclude headers exactly as labelled. Unsigned arithmetic must be checked before parsing/allocating/reading. The appendix contains limited proposed header/footer vectors, **not** a full conformance corpus.

## 1. 64-byte archive header at offset zero

| Offset | Size | Type | Meaning (proposed) |
|---|---:|---|---|
| 0 | 8 | bytes | `4F 48 41 1A 0D 0A 00 01` (`OHA` + binary marker) |
| 8 | 2 | u16 | format major = 1 |
| 10 | 2 | u16 | format minor = 0 |
| 12 | 4 | u32 | header length = 64 |
| 16 | 4 | u32 | required feature mask = 0 in M1 |
| 20 | 4 | u32 | optional feature mask = 0 in M1 |
| 24 | 32 | bytes | reserved, must be zero |
| 56 | 4 | u32 | CRC32C over bytes 0..55 |
| 60 | 4 | u32 | reserved, must be zero |

CRC32C uses reflected Castagnoli polynomial `0x82F63B78`, init and xor-out `0xFFFFFFFF`; test string `123456789` -> `E3069283`. CRC is accidental-corruption detection only. Unknown version or required/optional flags in research v1 are rejected; future optional flags require explicit skippability semantics.

## 2. Physical frame sequence (candidate)

`header | zero or more DATA frames | one MNFT frame | one INDX frame | footer`

No unreferenced trailing garbage, overlapping frames, duplicate block IDs, holes except specifically encoded alignment records (none in M1), or alternate footer locations. The file length must equal the footer's declared total length. Writer creates a new temporary file and atomically replaces the destination *after* fsync/flush semantics are checked on each OS; **M1 never modifies existing `.oha` archives in place**. This avoids making an unsupported crash-recovery claim for append operations.

### 80-byte frame header (candidate, before payload)

| Offset | Size | Type | Description |
|---|---:|---|---|
| 0 | 4 | bytes | `DATA`, `MNFT`, or `INDX` |
| 4 | 2 | u16 | fixed frame header length = 80 |
| 6 | 2 | u16 | frame version = 1 |
| 8 | 4 | u32 | flags = 0 |
| 12 | 8 | u64 | payload byte length, excluding frame header |
| 20 | 8 | u64 | fully decoded content length |
| 28 | 8 | u64 | unique block ID for DATA; zero for metadata |
| 36 | 2 | u16 | codec ID: 0 = STORE, 1 = ZSTD |
| 38 | 2 | u16 | codec parameter length; zero in this proposal |
| 40 | 32 | bytes | SHA-256 of decoded bytes (not authenticated) |
| 72 | 4 | u32 | CRC32C over frame header bytes 0..71 |
| 76 | 4 | u32 | reserved zero |

For MNFT/INDX only STORE is legal at M1; decoded length must equal payload length. STORE DATA likewise requires equal sizes. ZSTD is a self-contained RFC 8878 frame with no external dictionary. Frames decode into bounded buffers/streams and must match declared length and SHA256. Avoid trusting codec-advertised decompressed lengths for allocation.

## 3. Footer: final 128 bytes at EOF

| Offset | Size | Type | Meaning |
|---|---:|---|---|
| 0 | 8 | bytes | ASCII `OHAEND1` then `00` |
| 8 | 8 | u64 | total archive bytes, including footer |
| 16 | 8 | u64 | MNFT frame absolute offset |
| 24 | 8 | u64 | MNFT frame total bytes (header + payload) |
| 32 | 8 | u64 | INDX frame absolute offset |
| 40 | 8 | u64 | INDX frame total bytes |
| 48 | 8 | u64 | generation = 1 in M1 |
| 56 | 32 | bytes | SHA-256 of MNFT **payload** (not authenticated) |
| 88 | 32 | bytes | SHA-256 of INDX **payload** (not authenticated) |
| 120 | 4 | u32 | CRC32C over bytes 0..119 |
| 124 | 4 | u32 | reserved zero |

Range checks precede all reads. MNFT must end at or before INDX, INDX ends exactly at footer, and both contain complete 80-byte frame headers. Footer SHA must be validated against full referenced metadata bytes, and frame SHA must agree. Reading the footer itself never grants trust in archive paths, sizes, frame contents or authenticity.

## 4. Unresolved items before format approval

- **Canonical manifest and index byte serialization**: path encoding/normalization, file mapping, exact offset tables, file hash semantics, file metadata and ordering. Candidate: length-prefixed UTF-8 NFC relative paths with `/`; strict Windows device/ADS/casefold compatibility checks at extraction. POSIX undecodable filenames require explicit refusal/export policy, not lossy conversion.
- Quotas and resource budgets: proposed defaults `DATA` decoded frame <= 16 MiB, max path <= 4096 UTF-8 bytes, <= 1,000,000 entries, maximum decoded total configurable, and maximum archive metadata processing budget. Exact accepted limits and low-memory streaming behavior need implementation profiling.
- SHA-256 vs BLAKE3 for content hashes and eventual M3; avoid rolling own cryptography.
- Optional feature rule, unknown frame skipping, ZSTD dictionary policy and codec registry stability.
- Explicit supported timestamp granularity, ACL/xattr handling and platform error reporting.
- Windows/macOS/Linux golden cross-decoder vectors and fuzzed invalid corpus.
- Future append/snapshot commit chain and AEAD envelope are **not** defined by this proposal.

## 5. Research verification

`tools/wire_header_probe.py` checks only header/footer structure and CRC32C without writing archives. `tests/test_wire_header_probe.py` includes the independently specified CRC32C standard vector and negative bounds, endian, version and corruption cases. The fixed research examples in `research/wire-v1-framing-vectors.json` are only framing examples, **not valid full archives or independent end-to-end vectors**. **A passing test is not archive-conformance or security certification.**

## M0 80-byte frame header research checks

The **unapproved** `DATA`, `MNFT`, and `INDX` frame proposal now has a read-only `validate_frame_header()` negative-test suite in `tools/wire_header_probe.py` and `tests/test_wire_header_probe.py`. It rejects unknown frame kinds, versions, flags, codecs, invalid block IDs, CRC32C corruption, declared size inconsistencies and over-budget frame lengths. The bounded default research limits are 16 MiB decoded and 18 MiB encoded bytes, each caller-overridable by a stricter budget; they are **not accepted public wire limits**. Hash verification, manifest/index serialization, compressed body validation, archive consistency and safe extraction remain unimplemented. No `.oha` writer or decoding claim follows from these tests.

## Physical envelope integrity research (M0, pending wire approval)

`tools/wire_header_probe.py::validate_candidate_envelope()` checks only a **bounded, in-memory candidate byte envelope**. It requires contiguous DATA records before exactly one MNFT and one INDX frame followed by the final footer; rejects duplicate block IDs, range/gap violations and frame CRC failures. It independently checks SHA-256 of all STORE DATA and both metadata payloads against record fields, and metadata digest against the footer. It tracks but **does not decode or authenticate ZSTD DATA**, reporting the count explicitly as `zstd_payloads_NOT_verified`. It does not interpret manifest/index payload bytes, validate filenames or paths, extract files, produce archives or prove any compressed stream is valid. Candidate default budgets: 64 MiB envelope, 4 MiB per metadata payload, 4096 DATA frames. These are research limits, not an accepted wire contract. Tests construct transient candidate buffers only and reject deliberate mutations. Owner approval and actual independent implementation are still required by #5.

## Candidate portable path semantics (research-only)

`tools/candidate_paths.py` and `tests/test_candidate_paths.py` implement a **conservative, non-extracting** manifest path eligibility and collision probe. The candidate requires relative `/`-separated NFC UTF-8, rejects parent traversal, symlinks/special entry types, Windows ADS/drive/reserved device names (/`CONOUT# Candidate `.oha` wire format v1 (M0 design proposal only)

**UNAPPROVED, NOT STABLE, NOT IMPLEMENTED.** The byte values and structure below are a concrete review proposal, *not* a public format, commitment, or a compatible file writer. Do not publish `.oha` files from these layouts or implement an encoder before the owner signs off. The canonical constraints in `FORMAT_DRAFT.md` continue to apply.

## Scope / upgrade discipline

M1: immutable single-generation archives containing regular files and directories only, STORE and ZSTD. No encryption, append updates, deduplication, external dictionaries, symlinks, hardlinks, NTFS alternate streams or complete ACL/fork preservation. Unsupported files/metadata must be reported explicitly, never silently dropped or flattened. No guarantees about malicious archives are made until a hardened implementation is tested and reviewed.

M3 backup snapshots, transactions/append, and M4 AEAD require separately specified versioned features. An M1 decoder rejects unknown *required* features rather than guessing; it must never execute archive-defined codecs or fetch plugins. No unauthenticated checksum can prove authenticity.

All integer fields are **unsigned little-endian** except declared timestamps. All offsets refer to absolute bytes from start of archive; all lengths include or exclude headers exactly as labelled. Unsigned arithmetic must be checked before parsing/allocating/reading. The appendix contains limited proposed header/footer vectors, **not** a full conformance corpus.

## 1. 64-byte archive header at offset zero

| Offset | Size | Type | Meaning (proposed) |
|---|---:|---|---|
| 0 | 8 | bytes | `4F 48 41 1A 0D 0A 00 01` (`OHA` + binary marker) |
| 8 | 2 | u16 | format major = 1 |
| 10 | 2 | u16 | format minor = 0 |
| 12 | 4 | u32 | header length = 64 |
| 16 | 4 | u32 | required feature mask = 0 in M1 |
| 20 | 4 | u32 | optional feature mask = 0 in M1 |
| 24 | 32 | bytes | reserved, must be zero |
| 56 | 4 | u32 | CRC32C over bytes 0..55 |
| 60 | 4 | u32 | reserved, must be zero |

CRC32C uses reflected Castagnoli polynomial `0x82F63B78`, init and xor-out `0xFFFFFFFF`; test string `123456789` -> `E3069283`. CRC is accidental-corruption detection only. Unknown version or required/optional flags in research v1 are rejected; future optional flags require explicit skippability semantics.

## 2. Physical frame sequence (candidate)

`header | zero or more DATA frames | one MNFT frame | one INDX frame | footer`

No unreferenced trailing garbage, overlapping frames, duplicate block IDs, holes except specifically encoded alignment records (none in M1), or alternate footer locations. The file length must equal the footer's declared total length. Writer creates a new temporary file and atomically replaces the destination *after* fsync/flush semantics are checked on each OS; **M1 never modifies existing `.oha` archives in place**. This avoids making an unsupported crash-recovery claim for append operations.

### 80-byte frame header (candidate, before payload)

| Offset | Size | Type | Description |
|---|---:|---|---|
| 0 | 4 | bytes | `DATA`, `MNFT`, or `INDX` |
| 4 | 2 | u16 | fixed frame header length = 80 |
| 6 | 2 | u16 | frame version = 1 |
| 8 | 4 | u32 | flags = 0 |
| 12 | 8 | u64 | payload byte length, excluding frame header |
| 20 | 8 | u64 | fully decoded content length |
| 28 | 8 | u64 | unique block ID for DATA; zero for metadata |
| 36 | 2 | u16 | codec ID: 0 = STORE, 1 = ZSTD |
| 38 | 2 | u16 | codec parameter length; zero in this proposal |
| 40 | 32 | bytes | SHA-256 of decoded bytes (not authenticated) |
| 72 | 4 | u32 | CRC32C over frame header bytes 0..71 |
| 76 | 4 | u32 | reserved zero |

For MNFT/INDX only STORE is legal at M1; decoded length must equal payload length. STORE DATA likewise requires equal sizes. ZSTD is a self-contained RFC 8878 frame with no external dictionary. Frames decode into bounded buffers/streams and must match declared length and SHA256. Avoid trusting codec-advertised decompressed lengths for allocation.

## 3. Footer: final 128 bytes at EOF

| Offset | Size | Type | Meaning |
|---|---:|---|---|
| 0 | 8 | bytes | ASCII `OHAEND1` then `00` |
| 8 | 8 | u64 | total archive bytes, including footer |
| 16 | 8 | u64 | MNFT frame absolute offset |
| 24 | 8 | u64 | MNFT frame total bytes (header + payload) |
| 32 | 8 | u64 | INDX frame absolute offset |
| 40 | 8 | u64 | INDX frame total bytes |
| 48 | 8 | u64 | generation = 1 in M1 |
| 56 | 32 | bytes | SHA-256 of MNFT **payload** (not authenticated) |
| 88 | 32 | bytes | SHA-256 of INDX **payload** (not authenticated) |
| 120 | 4 | u32 | CRC32C over bytes 0..119 |
| 124 | 4 | u32 | reserved zero |

Range checks precede all reads. MNFT must end at or before INDX, INDX ends exactly at footer, and both contain complete 80-byte frame headers. Footer SHA must be validated against full referenced metadata bytes, and frame SHA must agree. Reading the footer itself never grants trust in archive paths, sizes, frame contents or authenticity.

## 4. Unresolved items before format approval

- **Canonical manifest and index byte serialization**: path encoding/normalization, file mapping, exact offset tables, file hash semantics, file metadata and ordering. Candidate: length-prefixed UTF-8 NFC relative paths with `/`; strict Windows device/ADS/casefold compatibility checks at extraction. POSIX undecodable filenames require explicit refusal/export policy, not lossy conversion.
- Quotas and resource budgets: proposed defaults `DATA` decoded frame <= 16 MiB, max path <= 4096 UTF-8 bytes, <= 1,000,000 entries, maximum decoded total configurable, and maximum archive metadata processing budget. Exact accepted limits and low-memory streaming behavior need implementation profiling.
- SHA-256 vs BLAKE3 for content hashes and eventual M3; avoid rolling own cryptography.
- Optional feature rule, unknown frame skipping, ZSTD dictionary policy and codec registry stability.
- Explicit supported timestamp granularity, ACL/xattr handling and platform error reporting.
- Windows/macOS/Linux golden cross-decoder vectors and fuzzed invalid corpus.
- Future append/snapshot commit chain and AEAD envelope are **not** defined by this proposal.

## 5. Research verification

`tools/wire_header_probe.py` checks only header/footer structure and CRC32C without writing archives. `tests/test_wire_header_probe.py` includes the independently specified CRC32C standard vector and negative bounds, endian, version and corruption cases. The fixed research examples in `research/wire-v1-framing-vectors.json` are only framing examples, **not valid full archives or independent end-to-end vectors**. **A passing test is not archive-conformance or security certification.**

## M0 80-byte frame header research checks

The **unapproved** `DATA`, `MNFT`, and `INDX` frame proposal now has a read-only `validate_frame_header()` negative-test suite in `tools/wire_header_probe.py` and `tests/test_wire_header_probe.py`. It rejects unknown frame kinds, versions, flags, codecs, invalid block IDs, CRC32C corruption, declared size inconsistencies and over-budget frame lengths. The bounded default research limits are 16 MiB decoded and 18 MiB encoded bytes, each caller-overridable by a stricter budget; they are **not accepted public wire limits**. Hash verification, manifest/index serialization, compressed body validation, archive consistency and safe extraction remain unimplemented. No `.oha` writer or decoding claim follows from these tests.

## Physical envelope integrity research (M0, pending wire approval)

`tools/wire_header_probe.py::validate_candidate_envelope()` checks only a **bounded, in-memory candidate byte envelope**. It requires contiguous DATA records before exactly one MNFT and one INDX frame followed by the final footer; rejects duplicate block IDs, range/gap violations and frame CRC failures. It independently checks SHA-256 of all STORE DATA and both metadata payloads against record fields, and metadata digest against the footer. It tracks but **does not decode or authenticate ZSTD DATA**, reporting the count explicitly as `zstd_payloads_NOT_verified`. It does not interpret manifest/index payload bytes, validate filenames or paths, extract files, produce archives or prove any compressed stream is valid. Candidate default budgets: 64 MiB envelope, 4 MiB per metadata payload, 4096 DATA frames. These are research limits, not an accepted wire contract. Tests construct transient candidate buffers only and reject deliberate mutations. Owner approval and actual independent implementation are still required by #5.

## Candidate portable path semantics (research-only)

`tools/candidate_paths.py` and `tests/test_candidate_paths.py` implement a **conservative, non-extracting** manifest path eligibility and collision probe. The candidate requires relative `/`-separated NFC UTF-8, rejects parent traversal, symlinks/special entry types, Windows ADS/drive/reserved device names (, and conservatively `CLOCK# Candidate `.oha` wire format v1 (M0 design proposal only)

**UNAPPROVED, NOT STABLE, NOT IMPLEMENTED.** The byte values and structure below are a concrete review proposal, *not* a public format, commitment, or a compatible file writer. Do not publish `.oha` files from these layouts or implement an encoder before the owner signs off. The canonical constraints in `FORMAT_DRAFT.md` continue to apply.

## Scope / upgrade discipline

M1: immutable single-generation archives containing regular files and directories only, STORE and ZSTD. No encryption, append updates, deduplication, external dictionaries, symlinks, hardlinks, NTFS alternate streams or complete ACL/fork preservation. Unsupported files/metadata must be reported explicitly, never silently dropped or flattened. No guarantees about malicious archives are made until a hardened implementation is tested and reviewed.

M3 backup snapshots, transactions/append, and M4 AEAD require separately specified versioned features. An M1 decoder rejects unknown *required* features rather than guessing; it must never execute archive-defined codecs or fetch plugins. No unauthenticated checksum can prove authenticity.

All integer fields are **unsigned little-endian** except declared timestamps. All offsets refer to absolute bytes from start of archive; all lengths include or exclude headers exactly as labelled. Unsigned arithmetic must be checked before parsing/allocating/reading. The appendix contains limited proposed header/footer vectors, **not** a full conformance corpus.

## 1. 64-byte archive header at offset zero

| Offset | Size | Type | Meaning (proposed) |
|---|---:|---|---|
| 0 | 8 | bytes | `4F 48 41 1A 0D 0A 00 01` (`OHA` + binary marker) |
| 8 | 2 | u16 | format major = 1 |
| 10 | 2 | u16 | format minor = 0 |
| 12 | 4 | u32 | header length = 64 |
| 16 | 4 | u32 | required feature mask = 0 in M1 |
| 20 | 4 | u32 | optional feature mask = 0 in M1 |
| 24 | 32 | bytes | reserved, must be zero |
| 56 | 4 | u32 | CRC32C over bytes 0..55 |
| 60 | 4 | u32 | reserved, must be zero |

CRC32C uses reflected Castagnoli polynomial `0x82F63B78`, init and xor-out `0xFFFFFFFF`; test string `123456789` -> `E3069283`. CRC is accidental-corruption detection only. Unknown version or required/optional flags in research v1 are rejected; future optional flags require explicit skippability semantics.

## 2. Physical frame sequence (candidate)

`header | zero or more DATA frames | one MNFT frame | one INDX frame | footer`

No unreferenced trailing garbage, overlapping frames, duplicate block IDs, holes except specifically encoded alignment records (none in M1), or alternate footer locations. The file length must equal the footer's declared total length. Writer creates a new temporary file and atomically replaces the destination *after* fsync/flush semantics are checked on each OS; **M1 never modifies existing `.oha` archives in place**. This avoids making an unsupported crash-recovery claim for append operations.

### 80-byte frame header (candidate, before payload)

| Offset | Size | Type | Description |
|---|---:|---|---|
| 0 | 4 | bytes | `DATA`, `MNFT`, or `INDX` |
| 4 | 2 | u16 | fixed frame header length = 80 |
| 6 | 2 | u16 | frame version = 1 |
| 8 | 4 | u32 | flags = 0 |
| 12 | 8 | u64 | payload byte length, excluding frame header |
| 20 | 8 | u64 | fully decoded content length |
| 28 | 8 | u64 | unique block ID for DATA; zero for metadata |
| 36 | 2 | u16 | codec ID: 0 = STORE, 1 = ZSTD |
| 38 | 2 | u16 | codec parameter length; zero in this proposal |
| 40 | 32 | bytes | SHA-256 of decoded bytes (not authenticated) |
| 72 | 4 | u32 | CRC32C over frame header bytes 0..71 |
| 76 | 4 | u32 | reserved zero |

For MNFT/INDX only STORE is legal at M1; decoded length must equal payload length. STORE DATA likewise requires equal sizes. ZSTD is a self-contained RFC 8878 frame with no external dictionary. Frames decode into bounded buffers/streams and must match declared length and SHA256. Avoid trusting codec-advertised decompressed lengths for allocation.

## 3. Footer: final 128 bytes at EOF

| Offset | Size | Type | Meaning |
|---|---:|---|---|
| 0 | 8 | bytes | ASCII `OHAEND1` then `00` |
| 8 | 8 | u64 | total archive bytes, including footer |
| 16 | 8 | u64 | MNFT frame absolute offset |
| 24 | 8 | u64 | MNFT frame total bytes (header + payload) |
| 32 | 8 | u64 | INDX frame absolute offset |
| 40 | 8 | u64 | INDX frame total bytes |
| 48 | 8 | u64 | generation = 1 in M1 |
| 56 | 32 | bytes | SHA-256 of MNFT **payload** (not authenticated) |
| 88 | 32 | bytes | SHA-256 of INDX **payload** (not authenticated) |
| 120 | 4 | u32 | CRC32C over bytes 0..119 |
| 124 | 4 | u32 | reserved zero |

Range checks precede all reads. MNFT must end at or before INDX, INDX ends exactly at footer, and both contain complete 80-byte frame headers. Footer SHA must be validated against full referenced metadata bytes, and frame SHA must agree. Reading the footer itself never grants trust in archive paths, sizes, frame contents or authenticity.

## 4. Unresolved items before format approval

- **Canonical manifest and index byte serialization**: path encoding/normalization, file mapping, exact offset tables, file hash semantics, file metadata and ordering. Candidate: length-prefixed UTF-8 NFC relative paths with `/`; strict Windows device/ADS/casefold compatibility checks at extraction. POSIX undecodable filenames require explicit refusal/export policy, not lossy conversion.
- Quotas and resource budgets: proposed defaults `DATA` decoded frame <= 16 MiB, max path <= 4096 UTF-8 bytes, <= 1,000,000 entries, maximum decoded total configurable, and maximum archive metadata processing budget. Exact accepted limits and low-memory streaming behavior need implementation profiling.
- SHA-256 vs BLAKE3 for content hashes and eventual M3; avoid rolling own cryptography.
- Optional feature rule, unknown frame skipping, ZSTD dictionary policy and codec registry stability.
- Explicit supported timestamp granularity, ACL/xattr handling and platform error reporting.
- Windows/macOS/Linux golden cross-decoder vectors and fuzzed invalid corpus.
- Future append/snapshot commit chain and AEAD envelope are **not** defined by this proposal.

## 5. Research verification

`tools/wire_header_probe.py` checks only header/footer structure and CRC32C without writing archives. `tests/test_wire_header_probe.py` includes the independently specified CRC32C standard vector and negative bounds, endian, version and corruption cases. The fixed research examples in `research/wire-v1-framing-vectors.json` are only framing examples, **not valid full archives or independent end-to-end vectors**. **A passing test is not archive-conformance or security certification.**

## M0 80-byte frame header research checks

The **unapproved** `DATA`, `MNFT`, and `INDX` frame proposal now has a read-only `validate_frame_header()` negative-test suite in `tools/wire_header_probe.py` and `tests/test_wire_header_probe.py`. It rejects unknown frame kinds, versions, flags, codecs, invalid block IDs, CRC32C corruption, declared size inconsistencies and over-budget frame lengths. The bounded default research limits are 16 MiB decoded and 18 MiB encoded bytes, each caller-overridable by a stricter budget; they are **not accepted public wire limits**. Hash verification, manifest/index serialization, compressed body validation, archive consistency and safe extraction remain unimplemented. No `.oha` writer or decoding claim follows from these tests.

## Physical envelope integrity research (M0, pending wire approval)

`tools/wire_header_probe.py::validate_candidate_envelope()` checks only a **bounded, in-memory candidate byte envelope**. It requires contiguous DATA records before exactly one MNFT and one INDX frame followed by the final footer; rejects duplicate block IDs, range/gap violations and frame CRC failures. It independently checks SHA-256 of all STORE DATA and both metadata payloads against record fields, and metadata digest against the footer. It tracks but **does not decode or authenticate ZSTD DATA**, reporting the count explicitly as `zstd_payloads_NOT_verified`. It does not interpret manifest/index payload bytes, validate filenames or paths, extract files, produce archives or prove any compressed stream is valid. Candidate default budgets: 64 MiB envelope, 4 MiB per metadata payload, 4096 DATA frames. These are research limits, not an accepted wire contract. Tests construct transient candidate buffers only and reject deliberate mutations. Owner approval and actual independent implementation are still required by #5.

## Candidate portable path semantics (research-only)

`tools/candidate_paths.py` and `tests/test_candidate_paths.py` implement a **conservative, non-extracting** manifest path eligibility and collision probe. The candidate requires relative `/`-separated NFC UTF-8, rejects parent traversal, symlinks/special entry types, Windows ADS/drive/reserved device names (), trailing dots/spaces, backslashes, controls, overlong components, duplicate/casefold and file/dir ancestor conflicts. Suggested research caps: 4096 UTF-8 bytes per path, 255 per component, 64 levels and 1 million entries. Exact target filesystem equivalence (especially NTFS/APFS Unicode/case folding and 8.3 aliasing) is **not** modelled; rejecting non-NFC source paths rather than silently rewriting them may make some legitimate POSIX filenames unsupported in M1. These trade-offs still require approval. No filesystem writes or safe extraction claim. See [Microsoft path naming](https://learn.microsoft.com/windows/desktop/FileIO/naming-a-file) and [Unicode normalization FAQ](https://www.unicode.org/faq/normalization.html).

### Extended Win32 console-name negatives (M0)

Windows `CreateFile` treats exact filenames `CONIN$` and `CONOUT$` as console handles, even though they are not in the classic DOS reserved-name table. The research path check rejects these full components case-insensitively; unlike `CON.txt`, `CONIN$.txt` is not treated as an exact console device name. The `CLOCK$` stem (with or without extension) is additionally excluded conservatively due to Windows shell API treatment. See [Microsoft CreateFile console documentation](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilea#consoles) and [Chromium Windows reserved-name checks](https://chromium.googlesource.com/chromium/src/base/+/refs/heads/main/files/file_util.cc). This adds only research filtering; actual extraction must still use handle-relative safe path operations and target-volume collision checks.
