# SPDX-License-Identifier: MPL-2.0
"""Cross-layer candidate OHA research. Test fixtures are not real archives."""
import struct
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import candidate_envelope_semantics as integrated
import wire_header_probe as wire
from test_wire_candidate_envelope import frame, envelope
from test_candidate_metadata import fixture


def candidate(rows=None, index_rows=None, frames=None):
    if rows is None:
        rows = [["a.txt", 0, 5, [[1, 0, 5]]], ["folder", 1, 0, []]]
    if index_rows is None:
        index_rows = [[1, 64, 85, 5, 0]]
    if frames is None:
        frames = [frame(b"DATA", b"hello", block_id=1)]
    return envelope(frames, manifest=fixture([1, rows]),
                    index=fixture([1, index_rows]))


class IntegratedProposalTests(unittest.TestCase):
    def test_valid_structural_candidate(self):
        r = integrated.validate_candidate_consistency(candidate())
        self.assertEqual(r["manifest_entries"], 2)
        self.assertEqual(r["referenced_blocks"], 1)
        self.assertEqual(r["store_payloads_sha256_verified"], 1)
        self.assertFalse(r["zstd_data_authenticated"])

    def test_empty_manifest(self):
        r = integrated.validate_candidate_consistency(
            candidate(rows=[], index_rows=[], frames=[]))
        self.assertEqual(r["referenced_blocks"], 0)

    def test_index_physical_offset_disagreement(self):
        with self.assertRaisesRegex(integrated.CandidateConsistencyError, "physical"):
            integrated.validate_candidate_consistency(
                candidate(index_rows=[[1, 65, 85, 5, 0]]))

    def test_index_frame_length_disagreement(self):
        with self.assertRaisesRegex(integrated.CandidateConsistencyError, "physical"):
            integrated.validate_candidate_consistency(
                candidate(rows=[["a", 0, 6, [[1, 0, 6]]]],
                          index_rows=[[1, 64, 86, 6, 0]]))

    def test_orphan_physical_block(self):
        with self.assertRaisesRegex(integrated.CandidateConsistencyError, "physical"):
            integrated.validate_candidate_consistency(
                candidate(frames=[frame(b"DATA", b"hello", block_id=1),
                                  frame(b"DATA", b"world", block_id=2)]))

    def test_invalid_manifest_block_reference(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            integrated.validate_candidate_consistency(
                candidate(rows=[["a", 0, 5, [[2, 0, 5]]]]))

    def test_reserved_windows_name(self):
        with self.assertRaisesRegex(integrated.CandidateConsistencyError, "path"):
            integrated.validate_candidate_consistency(
                candidate(rows=[["CON.txt", 0, 5, [[1, 0, 5]]]]))

    def test_unicode_casefold_collision(self):
        with self.assertRaisesRegex(integrated.CandidateConsistencyError, "path"):
            integrated.validate_candidate_consistency(
                candidate(rows=[["A", 0, 5, [[1, 0, 5]]], ["a", 1, 0, []]]))

    def test_wrong_cbor_with_matching_frame_hashes(self):
        with self.assertRaises(ValueError):
            integrated.validate_candidate_consistency(
                envelope(manifest=b"nonsense", index=b"not CBOR"))

    def test_declared_decoded_output_budget(self):
        with self.assertRaisesRegex(integrated.CandidateConsistencyError, "decoded"):
            integrated.validate_candidate_consistency(
                candidate(), max_total_decoded=4)

    def test_file_entry_count_limit(self):
        with self.assertRaisesRegex(integrated.CandidateConsistencyError, "entry-count"):
            integrated.validate_candidate_consistency(candidate(), max_entries=1)

    def test_invalid_budget(self):
        for kw in ({"max_entries": -1}, {"max_total_decoded": -1}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                integrated.validate_candidate_consistency(candidate(), **kw)

    def test_fake_zstd_not_decoded_or_authenticated(self):
        payload = b"invalid compressed bytes!"
        result = integrated.validate_candidate_consistency(
            candidate(rows=[["a", 0, 5, [[1, 0, 5]]]],
                      index_rows=[[1, 64, 80 + len(payload), 5, 1]],
                      frames=[frame(b"DATA", payload, block_id=1, codec=1, decoded=5)]))
        self.assertEqual(result["zstd_payloads_NOT_verified"], 1)
        self.assertFalse(result["zstd_data_authenticated"])

    def test_gap_between_metadata_frames(self):
        data = bytearray(candidate())
        start = len(data) - 128
        index_at = struct.unpack_from("<Q", data, start + 32)[0]
        data[index_at:index_at] = b"X"
        start += 1
        struct.pack_into("<Q", data, start + 8, len(data))
        struct.pack_into("<Q", data, start + 32, index_at + 1)
        struct.pack_into("<I", data, start + 120,
                         wire.crc32c(data[start:start + 120]))
        with self.assertRaisesRegex(wire.ProposalFormatError, "gap"):
            integrated.validate_candidate_consistency(bytes(data))


if __name__ == "__main__":
    unittest.main()
