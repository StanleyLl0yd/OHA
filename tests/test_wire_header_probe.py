"""Validation tests for an UNAPPROVED on-disk layout proposal."""

import importlib.util
import json
import random
import struct
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "oha_wire_probe", Path(__file__).resolve().parents[1] / "tools" / "wire_header_probe.py"
)
wire = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wire)


def valid_header():
    header = bytearray(64)
    header[:8] = wire.HEADER_MAGIC
    struct.pack_into("<HHI", header, 8, 1, 0, 64)
    struct.pack_into("<I", header, 56, wire.crc32c(header[:56]))
    return bytes(header)


def valid_footer():
    footer = bytearray(128)
    footer[:8] = wire.FOOTER_MAGIC
    struct.pack_into("<QQQQQQ", footer, 8, 64 + 160 + 128, 64, 80, 144, 80, 1)
    struct.pack_into("<I", footer, 120, wire.crc32c(footer[:120]))
    return bytes(footer)


class WireCandidateTests(unittest.TestCase):
    def test_framing_vectors_are_fixed(self):
        vectors = json.loads((Path(__file__).resolve().parents[1] /
                              "docs/research/wire-v1-framing-vectors.json").read_text())
        self.assertEqual(valid_header().hex(), vectors["header_v1_hex"])
        self.assertEqual(valid_footer().hex(), vectors["footer_v1_hex"])

    def test_random_invalid_framing_never_crashes(self):
        rng = random.Random(20261014)
        for _ in range(512):
            random_header = rng.randbytes(64)
            random_footer = rng.randbytes(128)
            with self.assertRaises(wire.ProposalFormatError):
                wire.validate_header(random_header)
            with self.assertRaises(wire.ProposalFormatError):
                wire.validate_footer(random_footer, 352)

    def test_crc32c_standard_vector(self):
        self.assertEqual(wire.crc32c(b"123456789"), 0xE3069283)
        self.assertEqual(wire.crc32c(b""), 0)

    def test_header_valid(self):
        self.assertEqual(wire.validate_header(valid_header())["major"], 1)

    def test_header_corrupted_crc_rejected(self):
        raw = bytearray(valid_header())
        raw[56] ^= 1
        with self.assertRaisesRegex(wire.ProposalFormatError, "CRC"):
            wire.validate_header(raw)

    def test_header_unsupported_feature_rejected(self):
        raw = bytearray(valid_header())
        struct.pack_into("<I", raw, 16, 1)
        struct.pack_into("<I", raw, 56, wire.crc32c(raw[:56]))
        with self.assertRaisesRegex(wire.ProposalFormatError, "feature"):
            wire.validate_header(raw)

    def test_header_wrong_endianness_or_major_rejected(self):
        raw = bytearray(valid_header())
        raw[8:10] = b"\x00\x01"
        struct.pack_into("<I", raw, 56, wire.crc32c(raw[:56]))
        with self.assertRaisesRegex(wire.ProposalFormatError, "version"):
            wire.validate_header(raw)

    def test_footer_valid(self):
        self.assertEqual(wire.validate_footer(valid_footer(), 352)["generation"], 1)

    def test_footer_overlapping_ranges_rejected(self):
        raw = bytearray(valid_footer())
        struct.pack_into("<Q", raw, 32, 143)
        struct.pack_into("<I", raw, 120, wire.crc32c(raw[:120]))
        with self.assertRaisesRegex(wire.ProposalFormatError, "index range"):
            wire.validate_footer(raw, 352)

    def test_footer_size_mismatch_rejected(self):
        with self.assertRaisesRegex(wire.ProposalFormatError, "archive size"):
            wire.validate_footer(valid_footer(), 353)

    def test_footer_checksum_corruption_rejected(self):
        raw = bytearray(valid_footer())
        raw[88] ^= 1
        with self.assertRaisesRegex(wire.ProposalFormatError, "CRC"):
            wire.validate_footer(raw, 352)

    def test_footer_reservations_rejected(self):
        raw = bytearray(valid_footer())
        raw[125] = 1
        with self.assertRaisesRegex(wire.ProposalFormatError, "reserved"):
            wire.validate_footer(raw, 352)

    def test_truncation_rejected(self):
        for raw in [b"", valid_header()[:-1]]:
            with self.assertRaises(wire.ProposalFormatError):
                wire.validate_header(raw)
        with self.assertRaises(wire.ProposalFormatError):
            wire.validate_footer(valid_footer()[:-1], 352)


if __name__ == "__main__":
    unittest.main()
