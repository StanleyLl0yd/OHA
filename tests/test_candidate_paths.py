# SPDX-License-Identifier: MPL-2.0
"""Negative/positive path-eligibility tests for an unapproved archive proposal."""

import importlib.util
from pathlib import Path
import unittest

src = Path(__file__).resolve().parents[1] / "tools" / "candidate_paths.py"
spec = importlib.util.spec_from_file_location("oha_candidate_paths", src)
paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paths)


class CandidatePathTests(unittest.TestCase):
    def test_normal_portable_names(self):
        for value in ("a", ".gitignore", "folder/file.txt", "тест/слово.txt",
                      "emoji/🙂.md", "backup/2026-10-14/report"):
            with self.subTest(value=value):
                self.assertEqual(paths.validate_candidate_path(value), value)

    def test_empty_dot_and_traversal(self):
        for value in ("", "../secrets", "a/../b", "a/./b", "./x", "a//b", "a/"):
            with self.subTest(value=value):
                with self.assertRaises(paths.CandidatePathError):
                    paths.validate_candidate_path(value)

    def test_absolute_unc_and_drive_path(self):
        for value in ("/etc/passwd", "C:/test", "C:relative", "\\\\host\\share", "a\\b"):
            with self.subTest(value=value):
                with self.assertRaises(paths.CandidatePathError):
                    paths.validate_candidate_path(value)

    def test_windows_reserved_names_with_extensions(self):
        for name in ("CON", "con.txt", "AUX.bin", "NUL.tar.gz", "COM1", "lPt9",
                     "COM¹.txt", "LPT²", "COM³/normal", "dir/PRN.ext"):
            with self.subTest(name=name):
                with self.assertRaisesRegex(paths.CandidatePathError, "device"):
                    paths.validate_candidate_path(name)

    def test_windows_console_device_names(self):
        # Console handles can be opened by CreateFile with these exact names.
        for name in ("CONIN$", "conout$", "CoNiN$", "a/CONOUT$",
                     "CLOCK$", "clock$.txt", "directory/CLOCK$.data"):
            with self.subTest(name=name):
                with self.assertRaisesRegex(paths.CandidatePathError, "device"):
                    paths.validate_candidate_path(name)

    def test_console_name_with_extension_is_not_special(self):
        # Unlike CON.txt, CONIN$.txt is not a Windows console handle.
        self.assertEqual(paths.validate_candidate_path("CONIN$.txt"), "CONIN$.txt")

    def test_forbidden_windows_characters_and_ads(self):
        for name in ('file:stream', 'a<b', 'a>b', 'foo|bar', 'test?.md', 'x*y', 'a"b',
                     "a\x00b", "a\x1fb", "a\x7fb"):
            with self.subTest(name=name):
                with self.assertRaises(paths.CandidatePathError):
                    paths.validate_candidate_path(name)

    def test_trailing_space_and_dot(self):
        for value in ("name.", "name ", "folder./file", "name..."):
            with self.assertRaisesRegex(paths.CandidatePathError, "trailing"):
                paths.validate_candidate_path(value)

    def test_non_nfc_name_is_rejected_without_rewriting(self):
        with self.assertRaisesRegex(paths.CandidatePathError, "NFC"):
            paths.validate_candidate_path("cafe\u0301.txt")
        self.assertEqual(paths.validate_candidate_path("café.txt"), "café.txt")

    def test_unpaired_surrogate_rejected(self):
        with self.assertRaisesRegex(paths.CandidatePathError, "surrogate"):
            paths.validate_candidate_path("bad\ud800")

    def test_bounded_path_and_component_sizes(self):
        with self.assertRaisesRegex(paths.CandidatePathError, "byte budget"):
            paths.validate_candidate_path("abc", max_bytes=2)
        with self.assertRaisesRegex(paths.CandidatePathError, "component byte budget"):
            paths.validate_candidate_path("a" * 256)
        with self.assertRaisesRegex(paths.CandidatePathError, "depth budget"):
            paths.validate_candidate_path("a/b/c", max_depth=2)
        with self.assertRaises(ValueError):
            paths.validate_candidate_path("a", max_depth=0)

    def test_valid_tree(self):
        result = paths.validate_candidate_tree([("d", "dir"), ("d/a", "file"), ("d/b", "file")])
        self.assertEqual(result, {"entries": 3, "file_entries": 2, "directory_entries": 1})

    def test_tree_duplicate_and_case_collision(self):
        for manifest in (
            [("a", "file"), ("a", "dir")],
            [("a", "file"), ("A", "file")],
            [("folder/A", "file"), ("folder/a", "file")],
            [("A/file", "file"), ("a/other", "file")],
        ):
            with self.subTest(manifest=manifest):
                with self.assertRaisesRegex(paths.CandidatePathError, "collid"):
                    paths.validate_candidate_tree(manifest)

    def test_file_parent_conflict(self):
        for manifest in ([("a", "file"), ("a/b", "file")],
                         [("a/b", "file"), ("a", "file")]):
            with self.assertRaisesRegex(paths.CandidatePathError, "ancestor"):
                paths.validate_candidate_tree(manifest)

    def test_unsupported_entry_kind_and_budget(self):
        for manifest in ([("link", "symlink")], [("dir", "special")]):
            with self.assertRaisesRegex(paths.CandidatePathError, "unsupported"):
                paths.validate_candidate_tree(manifest)
        with self.assertRaisesRegex(paths.CandidatePathError, "count"):
            paths.validate_candidate_tree([("a", "file")], max_entries=0)
        with self.assertRaises(ValueError):
            paths.validate_candidate_tree([], max_entries=-1)

    def test_no_target_filesystem_assumptions(self):
        # These are conservative candidates, not actual filesystem resolution.
        self.assertEqual(paths.validate_candidate_tree([("foo", "file")])["entries"], 1)


if __name__ == "__main__":
    unittest.main()
