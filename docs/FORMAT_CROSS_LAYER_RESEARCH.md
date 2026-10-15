# M0: research-only cross-layer candidate consistency

**UNAPPROVED, NOT AN ARCHIVE DECODER OR WRITER.** No filesystem writes, compressed-byte decoding or safe extraction.

The read-only candidate check combines three independent M0 proposals on a bounded in-memory candidate byte string: physical header/frame/footer verification, deterministic CBOR MNFT/INDX metadata, and conservative relative portable paths.

Additional cross-layer invariants:

- Manifest and index must agree on block references, each DATA block is referenced once (no M1 dedup).
- INDX physical frame offset, total frame length, declared decoded length and codec ID must match every DATA header exactly.
- Every physical DATA frame must be present in INDX; no orphan blocks or duplicate IDs.
- Proposed manifest names must pass path safety and collision checks. Manifest entry count and sum of decoded bytes are separately bounded.
- Both MNFT and INDX must be contiguous. A gap after MNFT is not allowed even if footer offsets/CRC were adjusted.
- STORE DATA and metadata hashes verified by physical probe. ZSTD block bodies remain **unverified** even when CBOR/index/frame headers agree. SHA-256 is not a cryptographic authenticity mechanism.

Research limits are 64 MiB candidate physical envelope, 4 MiB each metadata payload, 100k entries and 128 MiB sum of declared decoded DATA lengths. These are not accepted production compatibility or extraction limits.

Implementation: `tools/candidate_envelope_semantics.py` with negative fixtures in `tests/test_integrated_candidate.py`. The tests reuse the project's own experimental frame and CBOR test fixture encoders; independent decoder/interoperability vectors are still missing.

Unresolved metadata decision: the proposed manifest currently preserves bytes and directory structure, but **not** modification timestamps or portable read-only/permission attributes. Future writer must not silently promise or discard such metadata; decide an explicit portable representation (including pre-epoch timestamps) before format approval.\n\nRemaining issue #5 gate: owner approval of CBOR vs TLV, precise path rules, metadata preservation, quotas and codec parameters; safe descriptor-relative extraction, actual ZSTD verification and a complete archive implementation belong to M1.
