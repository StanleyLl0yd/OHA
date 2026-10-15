# SPDX-License-Identifier: MPL-2.0
"""Test-only CBOR fixture encoder; no .oha writer or decoder is implemented."""
import importlib.util
from pathlib import Path
import unittest

source = Path(__file__).resolve().parents[1] / "tools" / "candidate_metadata.py"
spec = importlib.util.spec_from_file_location("candidate_metadata", source)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def head(kind, n):
    if n < 24:
        return bytes([kind << 5 | n])
    if n < 256:
        return bytes([kind << 5 | 24, n])
    if n < 65536:
        return bytes([kind << 5 | 25]) + n.to_bytes(2, "big")
    if n < (1 << 32):
        return bytes([kind << 5 | 26]) + n.to_bytes(4, "big")
    return bytes([kind << 5 | 27]) + n.to_bytes(8, "big")

def fixture(value):
    if type(value) is int:
        return head(0, value)
    if type(value) is str:
        raw = value.encode("utf-8")
        return head(3, len(raw)) + raw
    if type(value) is bytes:
        return head(2, len(value)) + value
    if type(value) is list:
        return head(4, len(value)) + b"".join(fixture(x) for x in value)
    raise TypeError("test fixture only")

def mnft(rows=None):
    if rows is None:
        rows = [["a.txt", 0, 5, [[1, 0, 5]]], ["folder", 1, 0, []]]
    return fixture([1, rows])

def indx(rows=None):
    return fixture([1, [[1, 64, 85, 5, 0]] if rows is None else rows])

class MetadataTests(unittest.TestCase):
    def test_valid_manifest_index(self):
        rows = mod.manifest(mnft())
        self.assertEqual(mod.check_references(rows, mod.index(indx())), 1)
        self.assertEqual(len(rows), 2)

    def test_minimal_cbor_integer_encoding(self):
        self.assertEqual(mod.parse(b"\x18\x18"), 24)
        self.assertEqual(mod.parse(b"\x19\x01\x00"), 256)
        for data in (b"\x18\x17", b"\x19\x00\xff", b"\x1a\x00\x00\xff\xff",
                     b"\x1b\x00\x00\x00\x00\xff\xff\xff\xff"):
            with self.subTest(raw=data), self.assertRaisesRegex(mod.ProposalError, "non-minimal"):
                mod.parse(data)

    def test_unknown_and_indefinite_types(self):
        for raw in (b"\x9f\xff", b"\xbf\xff", b"\xa0", b"\x20", b"\xf6",
                    b"\xc0\x00", b"\xf9\x3c\x00", b"\x40\xff"):
            with self.subTest(raw=raw), self.assertRaises(mod.ProposalError):
                mod.parse(raw)

    def test_invalid_utf8_nfc(self):
        with self.assertRaisesRegex(mod.ProposalError, "UTF-8"):
            mod.parse(b"\x63\xff\xff\xff")
        with self.assertRaisesRegex(mod.ProposalError, "NFC"):
            mod.parse(fixture("cafe\u0301"))

    def test_truncated_trailing_and_budget(self):
        for data in (b"", mnft()[:-1], mnft() + b"\x00"):
            with self.assertRaises(mod.ProposalError):
                mod.manifest(data)
        with self.assertRaisesRegex(mod.ProposalError, "budget"):
            mod.parse(mnft(), max_bytes=10)
        with self.assertRaisesRegex(mod.ProposalError, "budget"):
            mod.parse(fixture([1, 2, 3]), max_items=2)

    def test_nesting_limit(self):
        with self.assertRaisesRegex(mod.ProposalError, "nesting"):
            mod.parse(fixture([[[[[[[[1]]]]]]]]))

    def test_manifest_sort_and_duplicate(self):
        for rows in ([["b", 0, 0, []], ["a", 0, 0, []]],
                     [["a", 0, 0, []], ["a", 1, 0, []]]):
            with self.assertRaisesRegex(mod.ProposalError, "duplicate or unsorted"):
                mod.manifest(mnft(rows))

    def test_manifest_segment_shape_and_coverage(self):
        for row in (["a", 0, 7, [[1, 0, 5]]],
                    ["a", 0, 7, [[1, 1, 7]]],
                    ["a", 0, 7, [[1, 0, 0]]],
                    ["a", 0, 7, [[0, 0, 7]]],
                    ["a", 1, 1, []], ["a", 1, 0, [[1, 0, 1]]]):
            with self.subTest(row=row), self.assertRaises(mod.ProposalError):
                mod.manifest(mnft([row]))

    def test_index_order_range_and_codec(self):
        for rows in ([[[1, 64, 85, 5, 0], [1, 149, 85, 5, 0]]],
                     [[1, 63, 85, 5, 0]], [[1, 64, 81, 5, 0]],
                     [[0, 64, 85, 5, 0]], [[1, 64, 85, 5, 5]]):
            with self.subTest(rows=rows), self.assertRaises(mod.ProposalError):
                mod.index(indx(rows))

    def test_inconsistent_references(self):
        idx = mod.index(indx())
        with self.assertRaisesRegex(mod.ProposalError, "missing"):
            mod.check_references([("a", 0, 5, [[2, 0, 5]])], idx)
        with self.assertRaisesRegex(mod.ProposalError, "repeated"):
            mod.check_references([("a", 0, 5, [[1, 0, 5]]),
                                  ("b", 0, 5, [[1, 0, 5]])], idx)
        with self.assertRaisesRegex(mod.ProposalError, "orphan"):
            mod.check_references([], idx)
        with self.assertRaisesRegex(mod.ProposalError, "mismatch"):
            mod.check_references([("a", 0, 4, [[1, 0, 4]])], idx)

    def test_incompatible_schema_version(self):
        with self.assertRaisesRegex(mod.ProposalError, "schema"):
            mod.manifest(fixture([2, []]))
        with self.assertRaisesRegex(mod.ProposalError, "schema"):
            mod.index(fixture([1, [], []]))

if __name__ == "__main__":
    unittest.main()
