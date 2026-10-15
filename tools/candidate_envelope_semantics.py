# SPDX-License-Identifier: MPL-2.0
"""Read-only cross-layer consistency of an UNAPPROVED OHA M0 format proposal.

No actual archive writer, compressed decoder, filesystem access or safe extraction.
"""
from __future__ import annotations

import candidate_metadata as metadata
import candidate_paths as paths
import wire_header_probe as wire

MAX_TOTAL_DECODED = 128 * 1024 * 1024
MAX_ENTRIES = 100_000


class CandidateConsistencyError(ValueError):
    pass


def validate_candidate_consistency(
    raw: bytes, *, max_total_decoded: int = MAX_TOTAL_DECODED,
    max_entries: int = MAX_ENTRIES
) -> dict:
    """Check framing, proposed CBOR, paths and index. ZSTD remains unverified."""
    if max_total_decoded < 0 or not 0 <= max_entries <= MAX_ENTRIES:
        raise ValueError("invalid research consistency budget")
    physical = wire.validate_candidate_envelope(raw)
    footer = wire.validate_footer(raw[-wire.FOOTER_BYTES:], len(raw))
    manifest_at = footer["manifest_at"]
    index_at = footer["index_at"]
    mbytes = raw[manifest_at + wire.FRAME_HEADER_BYTES:
                 manifest_at + footer["manifest_bytes"]]
    ibytes = raw[index_at + wire.FRAME_HEADER_BYTES:
                 index_at + footer["index_bytes"]]
    mrows = metadata.manifest(mbytes)
    irows = metadata.index(ibytes)
    if len(mrows) > max_entries:
        raise CandidateConsistencyError("manifest entry-count budget")
    try:
        paths.validate_candidate_tree(
            [(name, "dir" if kind == 1 else "file") for name, kind, _, _ in mrows],
            max_entries=max_entries
        )
    except paths.CandidatePathError as exc:
        raise CandidateConsistencyError("unsafe or colliding manifest path") from exc
    metadata.check_references(mrows, irows)

    physical_index = {}
    position, decoded_total = wire.HEADER_BYTES, 0
    while position < manifest_at:
        record = wire.validate_frame_header(
            raw[position:position + wire.FRAME_HEADER_BYTES]
        )
        decoded = record["decoded_bytes"]
        if decoded > max_total_decoded - decoded_total:
            raise CandidateConsistencyError("aggregate decoded output budget")
        decoded_total += decoded
        bid = record["block_id"]
        if bid in physical_index:
            raise CandidateConsistencyError("duplicate physical DATA id")
        physical_index[bid] = {
            "offset": position,
            "frame_bytes": wire.FRAME_HEADER_BYTES + record["payload_bytes"],
            "decoded_bytes": decoded,
            "codec": record["codec"],
        }
        position += wire.FRAME_HEADER_BYTES + record["payload_bytes"]
    if physical_index != irows:
        raise CandidateConsistencyError("index does not match physical DATA frames")
    return {
        **physical,
        "manifest_entries": len(mrows),
        "referenced_blocks": len(irows),
        "declared_decoded_bytes_NOT_ALL_VERIFIED": decoded_total,
        "metadata_schema": "proposed CBOR arrays v1; NOT APPROVED",
        "zstd_data_authenticated": False,
    }
