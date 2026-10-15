# SPDX-License-Identifier: MPL-2.0
"""Read-only M0 header/footer validation for an UNAPPROVED .oha wire proposal.

This is not an archive reader or encoder. A successful probe result does not
establish authenticity, manifest correctness or safe extraction.
"""

from __future__ import annotations

import struct

HEADER_MAGIC = b"OHA\x1a\r\n\x00\x01"
FOOTER_MAGIC = b"OHAEND1\x00"
HEADER_BYTES = 64
FOOTER_BYTES = 128
FRAME_HEADER_BYTES = 80


class ProposalFormatError(ValueError):
    pass


def crc32c(data: bytes) -> int:
    """Reflected Castagnoli polynomial, for research, not cryptography."""
    value = 0xFFFFFFFF
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0x82F63B78 if value & 1 else 0)
    return value ^ 0xFFFFFFFF


def validate_header(header: bytes) -> dict[str, int]:
    if len(header) != HEADER_BYTES:
        raise ProposalFormatError("header size")
    if header[:8] != HEADER_MAGIC:
        raise ProposalFormatError("magic")
    major, minor, header_length, required, optional = struct.unpack_from("<HHIII", header, 8)
    if (major, minor, header_length) != (1, 0, HEADER_BYTES):
        raise ProposalFormatError("unsupported version or header size")
    if required != 0 or optional != 0:
        raise ProposalFormatError("unknown feature bits in research v1")
    if any(header[24:56]) or any(header[60:64]):
        raise ProposalFormatError("nonzero reserved header field")
    expected_crc = struct.unpack_from("<I", header, 56)[0]
    if crc32c(header[:56]) != expected_crc:
        raise ProposalFormatError("header CRC32C mismatch")
    return {"major": major, "minor": minor, "required_features": required}


def validate_footer(footer: bytes, archive_bytes: int) -> dict[str, int]:
    if len(footer) != FOOTER_BYTES or archive_bytes < HEADER_BYTES + FOOTER_BYTES:
        raise ProposalFormatError("footer/archive length")
    if footer[:8] != FOOTER_MAGIC:
        raise ProposalFormatError("footer magic")
    recorded_bytes, manifest_at, manifest_bytes, index_at, index_bytes, generation = (
        struct.unpack_from("<QQQQQQ", footer, 8)
    )
    if recorded_bytes != archive_bytes or generation != 1:
        raise ProposalFormatError("archive size or generation")
    footer_at = archive_bytes - FOOTER_BYTES
    # Checks are subtractive so untrusted offsets cannot overflow fixed-width arithmetic.
    if (manifest_at < HEADER_BYTES or manifest_bytes < FRAME_HEADER_BYTES or
            manifest_at > footer_at or manifest_bytes > footer_at - manifest_at):
        raise ProposalFormatError("manifest range")
    if (index_at < manifest_at + manifest_bytes or
            index_at > footer_at or index_bytes < FRAME_HEADER_BYTES or
            index_bytes > footer_at - index_at or
            index_at + index_bytes != footer_at):
        raise ProposalFormatError("index range")
    if any(footer[124:128]):
        raise ProposalFormatError("nonzero reserved footer field")
    if crc32c(footer[:120]) != struct.unpack_from("<I", footer, 120)[0]:
        raise ProposalFormatError("footer CRC32C mismatch")
    return {"archive_bytes": archive_bytes, "manifest_at": manifest_at,
            "manifest_bytes": manifest_bytes, "index_at": index_at,
            "index_bytes": index_bytes, "generation": generation}

# Research-only frame header limits. A final specification may set different limits.
RESEARCH_MAX_FRAME_PAYLOAD = 18 * 1024 * 1024
RESEARCH_MAX_FRAME_DECODED = 16 * 1024 * 1024
FRAME_KINDS = (b"DATA", b"MNFT", b"INDX")


def validate_frame_header(
    raw: bytes,
    *,
    max_payload_bytes: int = RESEARCH_MAX_FRAME_PAYLOAD,
    max_decoded_bytes: int = RESEARCH_MAX_FRAME_DECODED,
) -> dict[str, int | str]:
    """Validate only a proposed 80-byte frame header, not its body or archive.

    Caller-provided resource ceilings are mandatory for any production decoder.
    This is a structural research probe; no SHA-256 or decompression is performed.
    """
    if len(raw) != FRAME_HEADER_BYTES:
        raise ProposalFormatError("frame header size")
    if max_payload_bytes < 0 or max_decoded_bytes < 0:
        raise ValueError("negative frame budget")
    kind = raw[:4]
    if kind not in FRAME_KINDS:
        raise ProposalFormatError("unknown frame kind")
    header_len, version, flags, payload, decoded, block_id, codec, params = (
        struct.unpack_from("<HHIQQQHH", raw, 4)
    )
    if header_len != FRAME_HEADER_BYTES or version != 1:
        raise ProposalFormatError("frame header size/version")
    if flags != 0 or params != 0 or any(raw[76:80]):
        raise ProposalFormatError("unknown frame flags, parameters or reserved fields")
    if payload > max_payload_bytes or decoded > max_decoded_bytes:
        raise ProposalFormatError("frame resource limit")
    if crc32c(raw[:72]) != struct.unpack_from("<I", raw, 72)[0]:
        raise ProposalFormatError("frame CRC32C mismatch")
    if kind == b"DATA":
        if block_id == 0 or codec not in (0, 1):
            raise ProposalFormatError("invalid DATA block id or codec")
        if codec == 0 and payload != decoded:
            raise ProposalFormatError("STORE DATA length mismatch")
        if codec == 1 and payload == 0:
            raise ProposalFormatError("empty ZSTD payload")
    elif block_id != 0 or codec != 0 or payload != decoded:
        raise ProposalFormatError("invalid metadata block id, codec or lengths")
    return {
        "kind": kind.decode("ascii"),
        "payload_bytes": payload,
        "decoded_bytes": decoded,
        "block_id": block_id,
        "codec": codec,
    }


# Full-byte-envelope research probe. It does not decode a manifest or compressed data.
import hashlib

RESEARCH_MAX_ENVELOPE_BYTES = 64 * 1024 * 1024
RESEARCH_MAX_METADATA_BYTES = 4 * 1024 * 1024
RESEARCH_MAX_DATA_FRAMES = 4096


def validate_candidate_envelope(
    data: bytes,
    *,
    max_archive_bytes: int = RESEARCH_MAX_ENVELOPE_BYTES,
    max_metadata_bytes: int = RESEARCH_MAX_METADATA_BYTES,
    max_data_frames: int = RESEARCH_MAX_DATA_FRAMES,
) -> dict[str, int]:
    """Validate physical framing, checksums and STORE blocks of an unapproved proposal.

    Compressed DATA contents, manifest/index schemas, filesystem paths and archive
    semantics are intentionally NOT validated. Never use this for extraction.
    """
    if max_archive_bytes < HEADER_BYTES + FOOTER_BYTES or max_metadata_bytes < 0 or max_data_frames < 0:
        raise ValueError("invalid research resource ceilings")
    if len(data) > max_archive_bytes:
        raise ProposalFormatError("archive resource budget exceeded")
    if len(data) < HEADER_BYTES + FOOTER_BYTES:
        raise ProposalFormatError("candidate envelope truncated")
    validate_header(data[:HEADER_BYTES])
    footer_at = len(data) - FOOTER_BYTES
    footer_raw = data[footer_at:]
    footer = validate_footer(footer_raw, len(data))
    manifest_at = footer["manifest_at"]
    index_at = footer["index_at"]
    metadata = (("MNFT", manifest_at, footer["manifest_bytes"], footer_raw[56:88]),
                ("INDX", index_at, footer["index_bytes"], footer_raw[88:120]))

    def record(at: int, boundary: int, budget: int) -> tuple[dict[str, int | str], int, bytes]:
        if boundary - at < FRAME_HEADER_BYTES:
            raise ProposalFormatError("incomplete candidate frame header or gap")
        raw = data[at:at + FRAME_HEADER_BYTES]
        header = validate_frame_header(raw, max_payload_bytes=budget)
        length = header["payload_bytes"]
        assert isinstance(length, int)
        if length > boundary - at - FRAME_HEADER_BYTES:
            raise ProposalFormatError("candidate frame crosses boundary")
        end = at + FRAME_HEADER_BYTES + length
        payload = data[at + FRAME_HEADER_BYTES:end]
        return header, end, payload

    seen: set[int] = set()
    data_count = 0
    verified_store = 0
    unverified_compressed = 0
    position = HEADER_BYTES
    while position < manifest_at:
        if data_count >= max_data_frames:
            raise ProposalFormatError("DATA frame count resource limit")
        header, position_end, payload = record(position, manifest_at, RESEARCH_MAX_FRAME_PAYLOAD)
        if header["kind"] != "DATA":
            raise ProposalFormatError("unexpected non-DATA frame before manifest")
        block_id = header["block_id"]
        assert isinstance(block_id, int)
        if block_id in seen:
            raise ProposalFormatError("duplicate DATA block ID")
        seen.add(block_id)
        if header["codec"] == 0:
            if hashlib.sha256(payload).digest() != data[position + 40:position + 72]:
                raise ProposalFormatError("STORE DATA SHA-256 mismatch")
            verified_store += 1
        else:
            # No ZSTD decoding here, even if the compressed frame header is structurally valid.
            unverified_compressed += 1
        data_count += 1
        position = position_end
    if position != manifest_at:
        raise ProposalFormatError("DATA sequence not contiguous")

    for expected_kind, at, length, footer_hash in metadata:
        if length > max_metadata_bytes + FRAME_HEADER_BYTES:
            raise ProposalFormatError("metadata resource budget exceeded")
        boundary = at + length
        header, end, payload = record(at, boundary, max_metadata_bytes)
        if header["kind"] != expected_kind or end != boundary:
            raise ProposalFormatError("metadata kind or physical frame length mismatch")
        actual = hashlib.sha256(payload).digest()
        if actual != data[at + 40:at + 72] or actual != footer_hash:
            raise ProposalFormatError("metadata SHA-256 mismatch")

    return {
        "archive_bytes": len(data),
        "data_frames": data_count,
        "store_payloads_sha256_verified": verified_store,
        "zstd_payloads_NOT_verified": unverified_compressed,
        "metadata_payloads_sha256_verified": 2,
    }
