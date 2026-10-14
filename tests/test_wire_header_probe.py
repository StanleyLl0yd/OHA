# SPDX-License-Identifier: MPL-2.0
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



def candidate_frame(
    *,
    kind=b"DATA",
    payload=64,
    decoded=64,
    block_id=1,
    codec=0,
    version=1,
    length=80,
    flags=0,
    params=0,
):
    frame = bytearray(80)
    frame[:4] = kind
    struct.pack_into(
        "<HHIQQQHH", frame, 4,
        length, version, flags, payload, decoded, block_id, codec, params,
    )
    # Header SHA-256 is a stored field, not verified without decoded body bytes.
    frame[40:72] = bytes(range(32))
    struct.pack_into("<I", frame, 72, wire.crc32c(frame[:72]))
    return bytes(frame)


class FrameHeaderProposalTests(unittest.TestCase):
    def test_regular_data_store(self):
        self.assertEqual(wire.validate_frame_header(candidate_frame())["kind"], "DATA")

    def test_zstd_length_may_differ(self):
        result = wire.validate_frame_header(candidate_frame(payload=42, decoded=4096, codec=1))
        self.assertEqual(result["decoded_bytes"], 4096)

    def test_metadata_is_store_and_id_zero(self):
        for kind in (b"MNFT", b"INDX"):
            with self.subTest(kind=kind):
                self.assertEqual(
                    wire.validate_frame_header(
                        candidate_frame(kind=kind, block_id=0)
                    )["kind"],
                    kind.decode(),
                )

    def test_truncated_or_extended_frame_rejected(self):
        raw = candidate_frame()
        for altered in (b"", raw[:-1], raw + b"\x00"):
            with self.subTest(size=len(altered)):
                with self.assertRaisesRegex(wire.ProposalFormatError, "size"):
                    wire.validate_frame_header(altered)

    def test_unknown_kind_rejected(self):
        with self.assertRaisesRegex(wire.ProposalFormatError, "kind"):
            wire.validate_frame_header(candidate_frame(kind=b"EVIL"))

    def test_frame_version_and_header_length_rejected(self):
        for data in (candidate_frame(version=2), candidate_frame(length=79)):
            with self.assertRaisesRegex(wire.ProposalFormatError, "version"):
                wire.validate_frame_header(data)

    def test_flags_parameters_and_reserved_rejected(self):
        for data in (candidate_frame(flags=1), candidate_frame(params=2)):
            with self.assertRaisesRegex(wire.ProposalFormatError, "flags"):
                wire.validate_frame_header(data)
        data = bytearray(candidate_frame())
        data[76] = 1
        with self.assertRaisesRegex(wire.ProposalFormatError, "reserved"):
            wire.validate_frame_header(bytes(data))

    def test_corrupt_crc_rejected(self):
        data = bytearray(candidate_frame())
        data[72] ^= 1
        with self.assertRaisesRegex(wire.ProposalFormatError, "CRC32C"):
            wire.validate_frame_header(bytes(data))

    def test_over_budget_rejected(self):
        for data in (
            candidate_frame(payload=wire.RESEARCH_MAX_FRAME_PAYLOAD + 1,
                            decoded=wire.RESEARCH_MAX_FRAME_PAYLOAD + 1),
            candidate_frame(payload=20, decoded=wire.RESEARCH_MAX_FRAME_DECODED + 1,
                            codec=1),
        ):
            with self.assertRaisesRegex(wire.ProposalFormatError, "resource"):
                wire.validate_frame_header(data)

    def test_caller_budget_is_enforced(self):
        with self.assertRaisesRegex(wire.ProposalFormatError, "resource"):
            wire.validate_frame_header(candidate_frame(), max_decoded_bytes=63)
        with self.assertRaises(ValueError):
            wire.validate_frame_header(candidate_frame(), max_payload_bytes=-1)

    def test_data_block_and_codec_rejected(self):
        for data in (candidate_frame(block_id=0), candidate_frame(codec=65535)):
            with self.assertRaisesRegex(wire.ProposalFormatError, "DATA"):
                wire.validate_frame_header(data)

    def test_store_requires_equal_lengths(self):
        with self.assertRaisesRegex(wire.ProposalFormatError, "STORE"):
            wire.validate_frame_header(candidate_frame(payload=2, decoded=3))

    def test_zstd_nonempty_payload(self):
        with self.assertRaisesRegex(wire.ProposalFormatError, "ZSTD"):
            wire.validate_frame_header(candidate_frame(payload=0, decoded=8, codec=1))

    def test_metadata_invariants_rejected(self):
        for kwargs in (
            {"block_id": 1},
            {"codec": 1},
            {"payload": 20, "decoded": 21},
        ):
            with self.subTest(**kwargs):
                with self.assertRaisesRegex(wire.ProposalFormatError, "metadata"):
                    wire.validate_frame_header(candidate_frame(kind=b"MNFT", **kwargs))

    def test_fuzz_invalid_headers_never_crash(self):
        rng = random.Random(20261014)
        for _ in range(512):
            random_header = rng.randbytes(80)
            with self.assertRaises(wire.ProposalFormatError):
                wire.validate_frame_header(random_header)

if __name__ == "__main__":
    unittest.main()
