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


def fixture(folder: Path, platform: str) -> Path:
    """Return checksum file; macOS checksum manifest is outside the app bundle."""
    prefix = folder / "Contents" / "Resources" if platform == "macos" else folder
    prefix.mkdir(parents=True, exist_ok=True)
    (prefix / "LICENSE").write_text("Mozilla Public License Version 2.0\n", encoding="utf-8")
    (prefix / "THIRD_PARTY_NOTICES.md").write_text("unreviewed runtime terms", encoding="utf-8")
    (prefix / "SOURCE-CODE.txt").write_text(inv.GITHUB_SOURCE + COMMIT, encoding="utf-8")
    for name in inv.OWN_BINARIES[platform]:
        p = folder / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"binary")
    checksum = (folder.parent / "SHA256SUMS.txt" if platform == "macos"
                else folder / "SHA256SUMS.txt")
    paths = sorted(p for p in folder.rglob("*") if p.is_file())
    checksum.write_text("".join(
        f"{inv.digest(p)} *{p.relative_to(folder).as_posix()}\n" for p in paths
    ), encoding="utf-8")
    return checksum


class NativePreviewInventoryTests(unittest.TestCase):
    def test_windows_inventory_and_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, "windows")
            result = inv.inventory(root, "windows", COMMIT)
            self.assertEqual(result["checksums_verified"], result["file_count"] - 1)
            self.assertEqual(result["third_party_binary_candidates_unreviewed"], [])

    def test_mac_complete_external_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "OHA.app"
            checksums = fixture(root, "macos")
            result = inv.inventory(root, "macos", COMMIT, checksum_manifest=checksums)
            self.assertEqual(result["checksums_verified"], result["file_count"])
            self.assertIn("Contents/Resources/LICENSE", result["files"])

    def test_mac_manifest_required_outside_signed_bundle(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "OHA.app"
            checksums = fixture(root, "macos")
            with self.assertRaisesRegex(ValueError, "requires external"):
                inv.inventory(root, "macos", COMMIT)
            with self.assertRaisesRegex(ValueError, "outside signed"):
                inv.inventory(root, "macos", COMMIT,
                              checksum_manifest=root / "Contents/Resources/LICENSE")
            self.assertTrue(checksums.is_file())

    def test_mac_post_signing_added_file_is_not_unverified(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "OHA.app"
            checksums = fixture(root, "macos")
            (root / "Contents" / "Resources" / "new-resource.txt").write_text("extra")
            with self.assertRaisesRegex(ValueError, "incomplete"):
                inv.inventory(root, "macos", COMMIT, checksum_manifest=checksums)

    def test_mac_checksum_cannot_be_inside_bundle(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "OHA.app"
            checksums = fixture(root, "macos")
            (root / "Contents" / "SHA256SUMS.txt").write_text("bad")
            with self.assertRaisesRegex(ValueError, "signed macOS bundle"):
                inv.inventory(root, "macos", COMMIT, checksum_manifest=checksums)

    def test_mac_tampered_resource_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "OHA.app"
            checksums = fixture(root, "macos")
            (root / "Contents" / "Resources" / "LICENSE").write_text(
                "Mozilla Public License Version 2.0\nmodified", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mismatch"):
                inv.inventory(root, "macos", COMMIT, checksum_manifest=checksums)

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
            root = Path(d) / "OHA.app"
            checksums = fixture(root, "macos")
            (root / "Contents" / "Resources" / "LICENSE").write_text("bad", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "MPL"):
                inv.inventory(root, "macos", COMMIT, checksum_manifest=checksums)

    def test_empty_or_malformed_commit_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, "windows")
            with self.assertRaisesRegex(ValueError, "commit"):
                inv.inventory(root, "windows", "x")

    def test_third_party_binary_candidate_not_cleared(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "OHA.app"
            item = root / "Contents" / "Frameworks" / "ThirdParty.dylib"
            fixture(root, "macos")
            item.write_bytes(b"foreign")
            checksums = root.parent / "SHA256SUMS.txt"
            with self.assertRaisesRegex(ValueError, "incomplete"):
                inv.inventory(root, "macos", COMMIT, checksum_manifest=checksums)
            # A complete manifest makes the file visible, not legally cleared.
            checksums.write_text(checksums.read_text(encoding="utf-8") +
                                 f"{inv.digest(item)} *Contents/Frameworks/ThirdParty.dylib\n")
            result = inv.inventory(root, "macos", COMMIT, checksum_manifest=checksums)
            self.assertIn("Contents/Frameworks/ThirdParty.dylib",
                          result["third_party_binary_candidates_unreviewed"])


if __name__ == "__main__":
    unittest.main()
