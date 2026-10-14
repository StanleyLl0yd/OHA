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
