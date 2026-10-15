# SPDX-License-Identifier: MPL-2.0
"""Research-only envelope-integrity negatives for an unapproved OHA proposal."""

import hashlib
import importlib.util
from pathlib import Path
import random
import struct
import unittest

src = Path(__file__).resolve().parents[1] / "tools" / "wire_header_probe.py"
spec = importlib.util.spec_from_file_location("candidate_wire", src)
wire = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wire)


def frame(kind, payload: bytes, *, block_id=0, codec=0, decoded=None):
    raw = bytearray(80)
    raw[:4] = kind
    if decoded is None:
        decoded = len(payload)
    struct.pack_into("<HHIQQQHH", raw, 4, 80, 1, 0, len(payload), decoded, block_id, codec, 0)
    raw[40:72] = hashlib.sha256(payload).digest()
    struct.pack_into("<I", raw, 72, wire.crc32c(raw[:72]))
    return bytes(raw) + payload


def envelope(data_frames=None, *, manifest=b"unapproved manifest", index=b"unapproved index"):
    if data_frames is None:
        data_frames = [frame(b"DATA", b"hello", block_id=1)]
    stream = b"".join(data_frames)
    m = frame(b"MNFT", manifest)
    i = frame(b"INDX", index)
    header = bytearray(64)
    header[:8] = wire.HEADER_MAGIC
    struct.pack_into("<HHI", header, 8, 1, 0, 64)
    struct.pack_into("<I", header, 56, wire.crc32c(header[:56]))
    manifest_at = len(header) + len(stream)
    index_at = manifest_at + len(m)
    footer = bytearray(128)
    footer[:8] = wire.FOOTER_MAGIC
    total = index_at + len(i) + len(footer)
    struct.pack_into("<QQQQQQ", footer, 8, total, manifest_at, len(m), index_at, len(i), 1)
    footer[56:88] = hashlib.sha256(manifest).digest()
    footer[88:120] = hashlib.sha256(index).digest()
    struct.pack_into("<I", footer, 120, wire.crc32c(footer[:120]))
    return bytes(header) + stream + m + i + bytes(footer)


class EnvelopeResearchTests(unittest.TestCase):
    def test_store_and_metadata_hashes(self):
        result = wire.validate_candidate_envelope(envelope())
        self.assertEqual(result["data_frames"], 1)
        self.assertEqual(result["store_payloads_sha256_verified"], 1)
        self.assertEqual(result["metadata_payloads_sha256_verified"], 2)
        self.assertEqual(result["zstd_payloads_NOT_verified"], 0)

    def test_zero_data_frames_structurally_accepted_not_semantic_archive(self):
        result = wire.validate_candidate_envelope(envelope([]))
        self.assertEqual(result["data_frames"], 0)

    def test_multiple_unique_data_frames(self):
        seq = [frame(b"DATA", b"a", block_id=1), frame(b"DATA", b"b", block_id=2)]
        self.assertEqual(wire.validate_candidate_envelope(envelope(seq))["data_frames"], 2)

    def test_duplicate_data_id_rejected(self):
        seq = [frame(b"DATA", b"a", block_id=1), frame(b"DATA", b"b", block_id=1)]
        with self.assertRaisesRegex(wire.ProposalFormatError, "duplicate"):
            wire.validate_candidate_envelope(envelope(seq))

    def test_store_payload_tampering_rejected(self):
        value = bytearray(envelope())
        value[64 + 80] ^= 1
        with self.assertRaisesRegex(wire.ProposalFormatError, "DATA SHA"):
            wire.validate_candidate_envelope(bytes(value))

    def test_metadata_payload_tampering_rejected(self):
        value = bytearray(envelope())
        # First manifest payload begins immediately after STORE frame.
        manifest_payload_start = 64 + 80 + 5 + 80
        value[manifest_payload_start] ^= 1
        with self.assertRaisesRegex(wire.ProposalFormatError, "metadata SHA"):
            wire.validate_candidate_envelope(bytes(value))

    def test_footer_metadata_digest_tampering_rejected_even_with_crc_fixed(self):
        value = bytearray(envelope())
        value[-128 + 56] ^= 1
        struct.pack_into("<I", value, len(value) - 8, wire.crc32c(value[-128:-8]))
        with self.assertRaisesRegex(wire.ProposalFormatError, "metadata SHA"):
            wire.validate_candidate_envelope(bytes(value))

    def test_unexpected_record_in_data_sequence_rejected(self):
        with self.assertRaisesRegex(wire.ProposalFormatError, "non-DATA"):
            wire.validate_candidate_envelope(envelope([frame(b"MNFT", b"bad")]))

    def test_gap_before_manifest_rejected(self):
        with self.assertRaisesRegex(wire.ProposalFormatError, "incomplete"):
            wire.validate_candidate_envelope(envelope([b"X"]))

    def test_data_frame_count_budget_rejected(self):
        seq = [frame(b"DATA", b"a", block_id=1), frame(b"DATA", b"b", block_id=2)]
        with self.assertRaisesRegex(wire.ProposalFormatError, "count"):
            wire.validate_candidate_envelope(envelope(seq), max_data_frames=1)

    def test_metadata_byte_budget_rejected(self):
        with self.assertRaisesRegex(wire.ProposalFormatError, "metadata resource"):
            wire.validate_candidate_envelope(envelope(), max_metadata_bytes=2)

    def test_total_archive_byte_budget_rejected(self):
        with self.assertRaisesRegex(wire.ProposalFormatError, "archive resource"):
            wire.validate_candidate_envelope(envelope(), max_archive_bytes=192)

    def test_invalid_budget_rejected(self):
        for kw in ({"max_archive_bytes": -1}, {"max_metadata_bytes": -1}, {"max_data_frames": -1}):
            with self.subTest(kw=kw):
                with self.assertRaises(ValueError):
                    wire.validate_candidate_envelope(envelope(), **kw)

    def test_zstd_payload_explicitly_unverified(self):
        # Fake compressed payload is intentionally NOT decoded or accepted as content.
        zstd = frame(b"DATA", b"fake zstd", block_id=7, codec=1, decoded=400)
        result = wire.validate_candidate_envelope(envelope([zstd]))
        self.assertEqual(result["zstd_payloads_NOT_verified"], 1)
        self.assertEqual(result["store_payloads_sha256_verified"], 0)

    def test_random_bytes_never_claim_valid_envelope(self):
        rng = random.Random(1447)
        for _ in range(128):
            with self.assertRaises(wire.ProposalFormatError):
                wire.validate_candidate_envelope(rng.randbytes(rng.randrange(1, 300)))


if __name__ == "__main__":
    unittest.main()
