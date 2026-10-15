# M0 research: deterministic CBOR manifest and index

**UNAPPROVED PROPOSAL, NOT AN .oha READER OR WRITER.** Do not use for extraction or treat the schema as stable.

## Motivation and alternatives

RFC 8949 section 4.2 (https://www.rfc-editor.org/rfc/rfc8949.html#section-4.2) defines deterministic CBOR with shortest integer and length forms. OHA can use the CBOR definite-array subset and avoid a bespoke metadata encoding. This is a candidate, not the owner's decision. The alternative is a small custom LE length-prefixed TLV, which avoids relying on a CBOR parser but creates its own permanent wire dialect.

All physical header/frame/footer fields in the existing draft are LE. **CBOR integer arguments use RFC 8949 big-endian representation**, an explicit exception requiring owner approval. In this proposal only CBOR unsigned integers, byte strings, NFC UTF-8 text and definite arrays are accepted. Reject maps (including duplicate-key ambiguity), negative integers, floats, tags, indefinites, overlong encodings and trailing bytes. This is narrower than general CBOR.

## Proposed MNFT payload

Root shape: [1, entries], where 1 is schema version and entries are sorted strictly by UTF-8-encoded path bytes.

Each entry: [path, kind, size, segments]. kind=0 regular file, kind=1 directory (size=0, no segments). Each file segment: [block_id, file_offset, decoded_length]. The segments must exactly and consecutively cover [0,size) and reference a complete DATA block, with no deduplication in initial M1. Empty files have no segments. Symlinks, xattrs, ACLs and timestamps are not represented; an eventual writer must explicitly report unsupported metadata or agree on preservation policy before creating an archive.

All paths must separately satisfy an approved portable-path policy (PR #22 is an experimental candidate). NFC alone does not solve target-platform collisions or descriptor-relative extraction races.

## Proposed INDX payload

Root shape: [1, rows]; each row [block_id, frame_offset, frame_total_bytes, decoded_bytes, codec_id]. Rows sorted by strictly increasing positive block ID. frame_offset >=64 and frame_total_bytes >80. Codec IDs 0=STORE and 1=ZSTD. STORE requires frame_total_bytes-80 == decoded_bytes. The index must eventually match physical frame offsets and lengths exactly. The current CBOR schema probe does not perform that cross-check.

Reference consistency: each DATA block must be used by exactly one file segment (no M1 dedup), segment decoded length must equal index decoded length, and orphan indexed blocks are rejected.

## Limits and verification boundary

Research limits: <=4 MiB per CBOR payload; <=100,000 CBOR values; nesting depth <=7; decoded DATA block <=16 MiB. These are **not** accepted format compatibility limits. File size proposal <=2^63-1. Independent decoder needs streaming and explicit total output / time / RAM caps, and all metadata values must be checked against physical framing.

Dependency-free Python test probe: tools/candidate_metadata.py and tests/test_candidate_metadata.py. Fixture encoder is test-only. It validates shape, minimal CBOR integers/lengths, text, limits, sorting, segment coverage and cross-document references, but **no actual archive or compressed bytes are decoded**, no files are extracted and no authenticity is established.

## Owner decisions blocking format approval

1. Deterministic CBOR definite-array subset vs bespoke LE TLV.
2. Exact manifest/index schemas, metadata compatibility/versioning and supported timestamps/attributes.
3. Portable NFC refusal policy vs reversible mapping for nonrepresentable POSIX filenames.
4. Hard format maxima versus configurable decoder safety budgets; acceptance for huge archive trees.
5. ZSTD self-contained window/dictionary policy, codec registry and cross-platform conformance goldens.

Until approved in issue #5, this proposal remains research-only. Actual serializer/parser, streaming writer/reader, extraction and compatibility testing belong to M1.
