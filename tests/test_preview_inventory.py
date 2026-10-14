# SPDX-License-Identifier: MPL-2.0
"""Offline tests for native binary inventory policy with synthetic files."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

module = Path(__file__).resolve().parents[1] / "tools" / "preview_inventory.py"
spec = importlib.util.spec_from_file_location("preview_inventory", module)
inv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inv)

COMMIT = "a" * 40


def fixture(folder: Path, platform: str):
    prefix = folder / "Contents" / "Resources" if platform == "macos" else folder
    prefix.mkdir(parents=True, exist_ok=True)
    (prefix / "LICENSE").write_text("Mozilla Public License Version 2.0\n", encoding="utf-8")
    (prefix / "THIRD_PARTY_NOTICES.md").write_text("unreviewed runtime terms", encoding="utf-8")
    (prefix / "SOURCE-CODE.txt").write_text(inv.GITHUB_SOURCE + COMMIT, encoding="utf-8")
    bins = inv.OWN_BINARIES[platform]
    for name in bins:
        p = folder / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"binary")
    checksum = folder / ("Contents/SHA256SUMS.txt" if platform == "macos" else "SHA256SUMS.txt")
    base = folder / "Contents" if platform == "macos" else folder
    names = sorted(bins) if platform == "macos" else [
        p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()
    ]
    checksum.parent.mkdir(parents=True, exist_ok=True)
    checksum.write_text("".join(
        f"{inv.digest(folder / p)} *{(folder / p).relative_to(base).as_posix()}\n"
        for p in names
    ), encoding="utf-8")


class NativePreviewInventoryTests(unittest.TestCase):
    def test_windows_inventory_and_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, "windows")
            result = inv.inventory(root, "windows", COMMIT)
            self.assertEqual(result["checksums_verified"], result["file_count"] - 1)
            self.assertEqual(result["third_party_binary_candidates_unreviewed"], [])

    def test_mac_inventory_and_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, "macos")
            result = inv.inventory(root, "macos", COMMIT)
            self.assertEqual(result["checksums_verified"], 2)

    def test_mismatched_commit_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, "windows")
            with self.assertRaisesRegex(ValueError, "source notice"):
                inv.inventory(root, "windows", "b" * 40)

    def test_corrupted_checksum_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, "windows")
            (root / "oha_ffi.dll").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "mismatch"):
                inv.inventory(root, "windows", COMMIT)

    def test_missing_runtime_notice_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, "windows")
            (root / "THIRD_PARTY_NOTICES.md").unlink()
            with self.assertRaisesRegex(ValueError, "required"):
                inv.inventory(root, "windows", COMMIT)

    def test_wrong_licensing_header_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, "macos")
            (root / "Contents" / "Resources" / "LICENSE").write_text("bad", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "MPL"):
                inv.inventory(root, "macos", COMMIT)

    def test_empty_or_malformed_commit_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, "windows")
            with self.assertRaisesRegex(ValueError, "commit"):
                inv.inventory(root, "windows", "x")

    def test_third_party_binary_candidate_not_cleared(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, "macos")
            item = root / "Contents" / "Frameworks" / "ThirdParty.dylib"
            item.write_bytes(b"foreign")
            result = inv.inventory(root, "macos", COMMIT)
            self.assertIn("Contents/Frameworks/ThirdParty.dylib",
                          result["third_party_binary_candidates_unreviewed"])


if __name__ == "__main__":
    unittest.main()
